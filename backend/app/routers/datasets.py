import os
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import crud, schemas
from app.config import MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS, USE_CLOUD_STORAGE
from app.services.cleaning_service import CleaningService
from app.services.eda_service import EDAService
from app.services.storage_service import StorageService
from app.dependencies.auth import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("/upload", response_model=schemas.DatasetVersionSchema)
def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Uploads a CSV file, persists it (locally or to Supabase Storage),
    computes quality metrics, and creates Version 1 in the database.
    """
    # 1. Validate file extension
    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only .csv files are supported."
        )

    # 2. Create Dataset DB record first (generates the ID we use for filename)
    dataset = crud.create_dataset(db, name=file.filename, user_id=user_id)
    filename = f"dataset_{dataset.id}_v1.csv"

    # 3. Stream file into memory buffer, enforcing size limit
    total_bytes = 0
    chunks = []
    try:
        while chunk := file.file.read(1024 * 1024):  # 1 MB chunks
            total_bytes += len(chunk)
            if total_bytes > MAX_CONTENT_LENGTH:
                crud.delete_dataset(db, dataset.id)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File size exceeds the 100 MB limit."
                )
            chunks.append(chunk)
    except HTTPException:
        raise
    except Exception as e:
        crud.delete_dataset(db, dataset.id)
        raise HTTPException(status_code=500, detail=f"File read error: {e}")

    raw_bytes = b"".join(chunks)

    # 4. Parse CSV to validate it and compute quality metrics
    try:
        df = StorageService.read_csv_robustly(raw_bytes)
        row_count, col_count = df.shape
        if row_count == 0:
            crud.delete_dataset(db, dataset.id)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Uploaded CSV file is empty. Please upload a file with data."
            )
        quality_score = EDAService.get_quality_score(df)
    except HTTPException:
        raise
    except Exception as e:
        crud.delete_dataset(db, dataset.id)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to parse CSV: {e}"
        )

    # 5. Persist file (Supabase or local)
    try:
        filepath, _ = StorageService.save_dataframe(df, filename)
    except Exception as e:
        crud.delete_dataset(db, dataset.id)
        raise HTTPException(status_code=500, detail=f"Storage error: {e}")

    # 6. Save DatasetVersion 1 in database
    version = crud.create_dataset_version(
        db=db,
        dataset_id=dataset.id,
        filepath=filepath,
        row_count=row_count,
        col_count=col_count,
        file_size=total_bytes,
        quality_score=quality_score,
        change_summary="Initial Upload",
        version_number=1
    )

    crud.log_cleaning_action(
        db=db,
        version_id=version.id,
        action_type="Upload",
        column_name=None,
        details=f"Uploaded '{file.filename}' — {row_count} rows × {col_count} columns."
    )

    logger.info(f"[Upload] Dataset {dataset.id} v1 saved. Storage: {'cloud' if USE_CLOUD_STORAGE else 'local'}")
    return version


@router.get("", response_model=List[schemas.DatasetSchema])
def list_datasets(
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Lists all datasets with their versions."""
    return crud.list_datasets(db, user_id=user_id)


@router.get("/{dataset_id}", response_model=schemas.DatasetSchema)
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Retrieves metadata for a specific dataset."""
    dataset = crud.get_dataset(db, dataset_id, user_id=user_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Removes a dataset and all associated files (disk or cloud)."""
    dataset = crud.get_dataset(db, dataset_id, user_id=user_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    for version in dataset.versions:
        StorageService.delete_file(version.filepath)

    crud.delete_dataset(db, dataset_id, user_id=user_id)
    return {"message": f"Dataset '{dataset.name}' deleted successfully."}


@router.get("/{dataset_id}/preview", response_model=schemas.DatasetPreview)
def get_dataset_preview(
    dataset_id: int,
    version_num: Optional[int] = Query(None, alias="version"),
    limit: int = 50,
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """Generates preview columns, types, null counts, and a sample data block."""
    dataset = crud.get_dataset(db, dataset_id, user_id=user_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")

    version = (
        crud.get_version_by_number(db, dataset_id, version_num)
        if version_num
        else crud.get_latest_version(db, dataset_id)
    )
    if not version:
        raise HTTPException(status_code=404, detail="Specified dataset version not found.")

    try:
        df = StorageService.load_dataframe(version.filepath)
        headers = list(df.columns)
        types = {col: str(dtype) for col, dtype in df.dtypes.items()}
        null_counts = df.isnull().sum().to_dict()
        raw_data = df.head(limit).to_dict(orient="records")
        data = EDAService.clean_dict(raw_data)

        return schemas.DatasetPreview(
            headers=headers,
            types=types,
            null_counts=null_counts,
            row_count=version.row_count,
            col_count=version.col_count,
            file_size=version.file_size,
            quality_score=version.quality_score,
            data=data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {e}")
