from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

# ── Engine configuration ──────────────────────────────────────────────────────
# SQLite needs check_same_thread=False (single-file, thread-bound by default).
# PostgreSQL uses connection pooling; no special connect_args needed.
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
else:
    # PostgreSQL production configuration:
    # - pool_size: keep 5 connections warm in the pool
    # - max_overflow: allow up to 10 extra temporary connections under high load
    # - pool_pre_ping: test each connection before checkout to prevent stale conn errors
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency: yields a scoped DB session, always closes on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
