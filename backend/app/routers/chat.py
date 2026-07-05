import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import crud, schemas, models
from app.services.cleaning_service import CleaningService
from app.services.eda_service import EDAService
from app.services.chat_service import ChatService
from app.dependencies.auth import get_current_user_id

router = APIRouter(prefix="/api/datasets/{dataset_id}/chat", tags=["chat"])

@router.post("", response_model=schemas.ChatResponse)
def chat_with_dataset(
    dataset_id: int,
    payload: schemas.ChatRequest,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Submits a chat message, retrieves analytical answers, and logs conversation history."""
    dataset = crud.get_dataset(db, dataset_id, user_id=user_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    version = crud.get_latest_version(db, dataset_id)
    if not version:
        raise HTTPException(status_code=404, detail="No active version found.")

    if not os.path.exists(version.filepath):
        raise HTTPException(status_code=404, detail="Dataset source file is missing from storage.")

    # 1. Log User Message
    crud.create_chat_message(db, dataset_id, sender="user", message=payload.message)

    try:
        # Load dataset statistics
        df = CleaningService.load_df(version.filepath)
        df_summary = EDAService.analyze_dataset(df)
        
        # Get Chat History
        chat_history = crud.get_chat_history(db, dataset_id)
        
        # Generate Answer
        answer_text = ChatService.answer_query(
            query=payload.message,
            df_summary=df_summary,
            quality_score=version.quality_score,
            chat_history=chat_history[:-1]  # Exclude current message from history to prevent duplication
        )
    except Exception as e:
        # Fallback error response
        answer_text = f"Sorry, I encountered an error processing your dataset: {str(e)}"

    # 2. Log Assistant Message
    db_msg = crud.create_chat_message(db, dataset_id, sender="assistant", message=answer_text)

    return schemas.ChatResponse(
        sender=db_msg.sender,
        message=db_msg.message,
        timestamp=db_msg.timestamp
    )


@router.get("", response_model=List[schemas.ChatMessageSchema])
def get_chat_history(
    dataset_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Retrieves all chat messages for a dataset session."""
    dataset = crud.get_dataset(db, dataset_id, user_id=user_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return crud.get_chat_history(db, dataset_id)


@router.delete("")
def clear_chat_history(
    dataset_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Wipes the active chat history log."""
    dataset = crud.get_dataset(db, dataset_id, user_id=user_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    crud.clear_chat_history(db, dataset_id)
    return {"message": "Chat history cleared successfully."}
