import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import crud, schemas
from app.services.cleaning_service import CleaningService
from app.services.eda_service import EDAService
from app.dependencies.auth import get_current_user_id

router = APIRouter(prefix="/api/datasets/{dataset_id}/eda", tags=["eda"])

@router.get("", response_model=schemas.EDASummary)
def get_eda_summary(
    dataset_id: int,
    version_num: Optional[int] = Query(None, alias="version"),
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Calculates dataset descriptive statistics, correlation maps, and trend matrices."""
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
        df = CleaningService.load_df(version.filepath)
        eda_summary = EDAService.analyze_dataset(df)
        return eda_summary
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate statistical EDA profile: {str(e)}"
        )
