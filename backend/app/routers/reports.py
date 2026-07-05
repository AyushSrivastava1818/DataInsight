import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app import crud, models
from app.config import USE_CLOUD_STORAGE
from app.services.storage_service import StorageService
from app.services.eda_service import EDAService
from app.services.insight_service import InsightService
from app.services.pdf_service import PDFService
from app.dependencies.auth import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/datasets/{dataset_id}/reports", tags=["reports"])


def _get_version(db: Session, dataset_id: int, version_num: Optional[int], user_id: Optional[str] = None):
    """Fetch a specific or latest dataset version. Raises 404 if missing."""
    dataset = crud.get_dataset(db, dataset_id, user_id=user_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    version = (
        crud.get_version_by_number(db, dataset_id, version_num)
        if version_num
        else crud.get_latest_version(db, dataset_id)
    )
    if not version:
        raise HTTPException(status_code=404, detail="Requested dataset version not found.")
    return dataset, version


@router.get("/csv")
def download_cleaned_csv(
    dataset_id: int,
    version_num: Optional[int] = Query(None, alias="version"),
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Downloads the CSV for the specified (or latest) dataset version.
    - Cloud mode: redirects to a 1-hour Supabase signed URL.
    - Local mode: serves file directly via FileResponse.
    """
    dataset, version = _get_version(db, dataset_id, version_num, user_id=user_id)
    base_name, _ = os.path.splitext(dataset.name)
    download_name = f"{base_name}_cleaned_v{version.version_number}.csv"

    if USE_CLOUD_STORAGE and version.filepath.startswith("csv/"):
        url = StorageService.get_download_url(version.filepath)
        if url:
            return RedirectResponse(url=url)
        # If url generation failed but it is a cloud path, fall back to checking if we have a local copy
        filename = os.path.basename(version.filepath)
        from app.config import STORAGE_DIR
        local_path = os.path.join(STORAGE_DIR, filename)
        if os.path.exists(local_path):
            return FileResponse(path=local_path, media_type="text/csv", filename=download_name)
        raise HTTPException(status_code=500, detail="Could not generate download URL and no local copy exists.")

    # Local mode (or local fallback path) — serve file from disk
    filepath = version.filepath
    if filepath.startswith("csv/"):
        filename = os.path.basename(filepath)
        from app.config import STORAGE_DIR
        filepath = os.path.join(STORAGE_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="CSV file is missing from local storage.")
    return FileResponse(path=filepath, media_type="text/csv", filename=download_name)


@router.get("/pdf")
def download_pdf_report(
    dataset_id: int,
    version_num: Optional[int] = Query(None, alias="version"),
    db: Session = Depends(get_db),
    user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Compiles a full PDF analytics report with EDA tables, cleaning audit trails,
    matplotlib charts, and AI narrative insights.
    """
    dataset, version = _get_version(db, dataset_id, version_num, user_id=user_id)

    try:
        # 1. Load dataframe from storage (works for both local and cloud)
        df = StorageService.load_dataframe(version.filepath)
        df_summary = EDAService.analyze_dataset(df)

        # 2. Collect complete cleaning audit trail for this dataset
        all_versions = (
            db.query(models.DatasetVersion)
            .filter(
                models.DatasetVersion.dataset_id == dataset_id,
                models.DatasetVersion.version_number <= version.version_number
            )
            .order_by(models.DatasetVersion.version_number)
            .all()
        )
        all_logs = []
        for v in all_versions:
            all_logs.extend(v.cleaning_logs)

        # 3. Generate AI insights
        insights = InsightService.generate_insights(df_summary, version.quality_score)

        # 4. Compile PDF
        pdf_bytes = PDFService.build_report(
            df=df,
            df_summary=df_summary,
            cleaning_logs=all_logs,
            insights=insights,
            dataset_name=dataset.name,
            version_number=version.version_number,
            quality_score=version.quality_score
        )

        base_name, _ = os.path.splitext(dataset.name)
        download_name = f"{base_name}_analytics_report_v{version.version_number}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={download_name}",
                "Cache-Control": "no-cache"
            }
        )
    except Exception as e:
        logger.error(f"[PDF] Report compilation failed for dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compile PDF Report: {e}")
