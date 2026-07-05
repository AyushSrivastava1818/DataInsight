import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import crud, schemas, models
from app.services.cleaning_service import CleaningService
from app.services.eda_service import EDAService
from app.services.storage_service import StorageService
from app.dependencies.auth import get_current_user_id

router = APIRouter(prefix="/api/datasets/{dataset_id}/clean", tags=["cleaning"])

def get_latest_version_and_df(dataset_id: int, db: Session, user_id: Optional[str] = None) -> tuple:
    """Helper: fetch latest version from DB and load its dataframe via StorageService."""
    dataset = crud.get_dataset(db, dataset_id, user_id=user_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    version = crud.get_latest_version(db, dataset_id)
    if not version:
        raise HTTPException(status_code=404, detail="No active dataset version found.")

    try:
        df = StorageService.load_dataframe(version.filepath)
        return version, df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read dataset: {e}")

def save_new_version(
    db: Session,
    dataset_id: int,
    df,
    prev_version,
    change_summary: str,
    action_type: str,
    column_name: str,
    action_details: str
):
    """Persist the cleaned DataFrame via StorageService and record the new version in DB."""
    new_version_num = prev_version.version_number + 1
    new_filename = f"dataset_{dataset_id}_v{new_version_num}.csv"

    try:
        filepath, file_size = StorageService.save_dataframe(df, new_filename)
        row_count, col_count = df.shape
        quality_score = EDAService.get_quality_score(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save cleaned dataset: {e}")

    new_version = crud.create_dataset_version(
        db=db,
        dataset_id=dataset_id,
        filepath=filepath,
        row_count=row_count,
        col_count=col_count,
        file_size=file_size,
        quality_score=quality_score,
        change_summary=change_summary,
        version_number=new_version_num
    )

    crud.log_cleaning_action(
        db=db,
        version_id=new_version.id,
        action_type=action_type,
        column_name=column_name,
        details=action_details
    )

    return new_version


@router.post("/missing-values", response_model=schemas.DatasetVersionSchema)
def impute_missing_values(
    dataset_id: int,
    payload: schemas.MissingValuesImputation,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Applies imputation strategy to handle missing entries in a column."""
    version, df = get_latest_version_and_df(dataset_id, db, user_id=user_id)
    
    try:
        df_cleaned, details = CleaningService.impute_missing(df, payload.column, payload.strategy)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    summary = f"Imputed '{payload.column}' using '{payload.strategy}'"
    return save_new_version(
        db=db,
        dataset_id=dataset_id,
        df=df_cleaned,
        prev_version=version,
        change_summary=summary,
        action_type="Imputation",
        column_name=payload.column,
        action_details=details
    )


@router.post("/duplicates", response_model=schemas.DatasetVersionSchema)
def remove_duplicates(
    dataset_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Removes duplicate rows from the dataset."""
    version, df = get_latest_version_and_df(dataset_id, db, user_id=user_id)
    
    df_cleaned, details = CleaningService.remove_duplicates(df)
    summary = "Removed duplicates"
    
    return save_new_version(
        db=db,
        dataset_id=dataset_id,
        df=df_cleaned,
        prev_version=version,
        change_summary=summary,
        action_type="Remove Duplicates",
        column_name=None,
        action_details=details
    )


@router.post("/type-correction", response_model=schemas.DatasetVersionSchema)
def convert_data_type(
    dataset_id: int,
    payload: schemas.DataTypeCorrection,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Converts a column data type (numeric, datetime, categorical, text)."""
    version, df = get_latest_version_and_df(dataset_id, db, user_id=user_id)
    
    try:
        df_cleaned, details = CleaningService.correct_data_type(
            df=df,
            column=payload.column,
            target_type=payload.target_type,
            date_format=payload.date_format
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    summary = f"Cast '{payload.column}' to '{payload.target_type}'"
    return save_new_version(
        db=db,
        dataset_id=dataset_id,
        df=df_cleaned,
        prev_version=version,
        change_summary=summary,
        action_type="Type Cast",
        column_name=payload.column,
        action_details=details
    )


@router.post("/outliers", response_model=schemas.DatasetVersionSchema)
def handle_outliers(
    dataset_id: int,
    payload: schemas.OutlierHandling,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Detects outliers using IQR or Z-score and removes or caps them."""
    version, df = get_latest_version_and_df(dataset_id, db, user_id=user_id)
    
    try:
        df_cleaned, details = CleaningService.handle_outliers(
            df=df,
            column=payload.column,
            method=payload.method,
            strategy=payload.strategy,
            threshold=payload.threshold
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    summary = f"Handled outliers in '{payload.column}' ({payload.method}/{payload.strategy})"
    return save_new_version(
        db=db,
        dataset_id=dataset_id,
        df=df_cleaned,
        prev_version=version,
        change_summary=summary,
        action_type="Outliers",
        column_name=payload.column,
        action_details=details
    )


@router.post("/text", response_model=schemas.DatasetVersionSchema)
def clean_text_column(
    dataset_id: int,
    payload: schemas.TextCleaning,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Trims, cases, or removes special characters in text columns."""
    version, df = get_latest_version_and_df(dataset_id, db, user_id=user_id)
    
    try:
        df_cleaned, details = CleaningService.clean_text(
            df=df,
            column=payload.column,
            remove_extra_spaces=payload.remove_extra_spaces,
            casing=payload.casing,
            remove_special_chars=payload.remove_special_chars
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    summary = f"Cleaned text in '{payload.column}'"
    return save_new_version(
        db=db,
        dataset_id=dataset_id,
        df=df_cleaned,
        prev_version=version,
        change_summary=summary,
        action_type="Text Cleaning",
        column_name=payload.column,
        action_details=details
    )


@router.post("/column-op", response_model=schemas.DatasetVersionSchema)
def execute_column_operation(
    dataset_id: int,
    payload: schemas.ColumnOperations,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Performs Column Rename, Deletion, or Math formula creation."""
    version, df = get_latest_version_and_df(dataset_id, db, user_id=user_id)
    
    try:
        df_cleaned, details = CleaningService.execute_column_op(
            df=df,
            action=payload.action,
            column=payload.column,
            new_name=payload.new_name,
            expression=payload.expression
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    summary = f"ColOp: {payload.action.upper()} on '{payload.column}'"
    return save_new_version(
        db=db,
        dataset_id=dataset_id,
        df=df_cleaned,
        prev_version=version,
        change_summary=summary,
        action_type="Column Operation",
        column_name=payload.column,
        action_details=details
    )
