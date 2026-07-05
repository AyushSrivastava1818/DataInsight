from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    # user_id stores the Supabase Auth UUID of the dataset owner.
    # Nullable=True for backwards compat with existing local-dev records.
    # On production PostgreSQL every new upload will set this from the JWT.
    user_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan")
    chat_history = relationship("ChatMessage", back_populates="dataset", cascade="all, delete-orphan")


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    # filepath stores either a local OS path (SQLite mode) or a Supabase Storage path/URL
    filepath = Column(String, nullable=False)
    row_count = Column(Integer, default=0)
    col_count = Column(Integer, default=0)
    file_size = Column(Integer, default=0)  # bytes
    quality_score = Column(Float, default=0.0)
    change_summary = Column(String, default="Initial Upload")
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="versions")
    cleaning_logs = relationship("CleaningLog", back_populates="version", cascade="all, delete-orphan")

    # Composite index so queries like "latest version for dataset X" are O(log n)
    __table_args__ = (
        Index("ix_dataset_versions_dataset_version", "dataset_id", "version_number"),
    )


class CleaningLog(Base):
    __tablename__ = "cleaning_logs"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(Integer, ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(String, nullable=False)
    column_name = Column(String, nullable=True)
    details = Column(Text, nullable=True)   # Changed to nullable — some ops have no detail text
    timestamp = Column(DateTime, default=datetime.utcnow)

    version = relationship("DatasetVersion", back_populates="cleaning_logs")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String, nullable=False)  # "user" or "assistant"
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="chat_history")
