import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.database import get_db
from app import crud
from app.services.cleaning_service import CleaningService
from app.services.eda_service import EDAService
from app.services.insight_service import InsightService
from app.dependencies.auth import get_current_user_id

router = APIRouter(prefix="/api/datasets/{dataset_id}/insights", tags=["insights"])

@router.get("", response_model=List[Dict[str, Any]])
def get_insights(
    dataset_id: int,
    version_num: Optional[int] = Query(None, alias="version"),
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Generates business insights using rules-based logic or optional LLM calls."""
    dataset = crud.get_dataset(db, dataset_id, user_id=user_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    if version_num:
        version = crud.get_version_by_number(db, dataset_id, version_num)
    else:
        version = crud.get_latest_version(db, dataset_id)

    if not version:
        raise HTTPException(status_code=404, detail="No active version found.")

    if not os.path.exists(version.filepath):
        raise HTTPException(status_code=404, detail="Dataset source file is missing from storage.")

    try:
        # Load data
        df = CleaningService.load_df(version.filepath)
        df_summary = EDAService.analyze_dataset(df)
        
        # Generate insights
        insights = InsightService.generate_insights(df_summary, version.quality_score)
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate dataset insights: {str(e)}"
        )
