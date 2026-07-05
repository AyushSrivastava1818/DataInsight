import uvicorn
import logging
import os
import shutil
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.database import engine, Base, SessionLocal
from app.config import STORAGE_DIR, ALLOWED_ORIGINS, USE_CLOUD_STORAGE
from app import crud
from app.services.cleaning_service import CleaningService
from app.services.eda_service import EDAService
from app.routers import datasets, cleaning, eda, insights, chat, reports

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("datainsight")

# ── Rate Limiter ──────────────────────────────────────────────────────────────
# Uses client IP as key. Default: 60 requests / minute per IP.
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


# ── EDA Cache ─────────────────────────────────────────────────────────────────
# Simple in-process dict cache keyed by (dataset_id, version_number).
# Cleared automatically when a new cleaning version is saved.
# For production scale, replace with Redis via cachetools or fastapi-cache2.
eda_cache: dict = {}


def seed_demo_dataset():
    """Seeds the database with a demo CSV if no datasets exist yet."""
    if USE_CLOUD_STORAGE:
        logger.info("[Seed] Cloud storage mode — skipping local demo seeding.")
        return

    db = SessionLocal()
    try:
        existing = crud.list_datasets(db)
        if existing:
            return

        demo_src = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "sample_data", "company_sales_demo.csv")
        )
        if not os.path.exists(demo_src):
            logger.warning(f"[Seed] Demo CSV not found at: {demo_src}")
            return

        dataset = crud.create_dataset(db, name="company_sales_demo.csv")
        filename = f"dataset_{dataset.id}_v1.csv"
        dest_path = os.path.join(STORAGE_DIR, filename)
        shutil.copy2(demo_src, dest_path)

        df = CleaningService.load_df(dest_path)
        row_count, col_count = df.shape
        quality_score = EDAService.get_quality_score(df)

        version = crud.create_dataset_version(
            db=db, dataset_id=dataset.id, filepath=dest_path,
            row_count=row_count, col_count=col_count,
            file_size=os.path.getsize(dest_path), quality_score=quality_score,
            change_summary="Initial Upload (Demo)", version_number=1
        )
        crud.log_cleaning_action(
            db=db, version_id=version.id, action_type="Upload", column_name=None,
            details=f"Preloaded demo dataset: {row_count} rows × {col_count} columns."
        )
        logger.info("[Seed] Seeded database with company_sales_demo.csv")
    except Exception as e:
        logger.error(f"[Seed] Failed: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks before serving, then cleanup on shutdown."""
    logger.info("[Startup] Creating database tables…")
    Base.metadata.create_all(bind=engine)
    seed_demo_dataset()
    logger.info("[Startup] DataInsight AI backend ready.")
    yield
    logger.info("[Shutdown] DataInsight AI backend stopping.")


# ── App Factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="DataInsight AI API",
    description="Production backend for CSV cleaning, profiling, AI insights, and report generation.",
    version="2.0.0",
    lifespan=lifespan,
)

# Attach rate limiter state and middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ──────────────────────────────────────────────────────────────────────
# In dev mode (ALLOWED_ORIGINS="*") all origins are allowed.
# In production set ALLOWED_ORIGINS to the deployed frontend domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again."}
    )

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(datasets.router)
app.include_router(cleaning.router)
app.include_router(eda.router)
app.include_router(insights.router)
app.include_router(chat.router)
app.include_router(reports.router)


@app.get("/")
def get_root():
    return {
        "status": "online",
        "app": "DataInsight AI API",
        "version": "2.0.0",
        "storage": "supabase" if USE_CLOUD_STORAGE else "local",
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
