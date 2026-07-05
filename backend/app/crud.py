from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from app import models, schemas

# Dataset operations
def create_dataset(db: Session, name: str, user_id: Optional[str] = None):
    db_dataset = models.Dataset(name=name, user_id=user_id)
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset

def get_dataset(db: Session, dataset_id: int, user_id: Optional[str] = None):
    query = db.query(models.Dataset).filter(models.Dataset.id == dataset_id)
    if user_id is not None:
        query = query.filter(models.Dataset.user_id == user_id)
    return query.first()

def list_datasets(db: Session, user_id: Optional[str] = None):
    query = db.query(models.Dataset)
    if user_id is not None:
        query = query.filter(models.Dataset.user_id == user_id)
    return query.order_by(desc(models.Dataset.created_at)).all()

def delete_dataset(db: Session, dataset_id: int, user_id: Optional[str] = None):
    db_dataset = get_dataset(db, dataset_id, user_id=user_id)
    if db_dataset:
        db.delete(db_dataset)
        db.commit()
        return True
    return False

# DatasetVersion operations
def create_dataset_version(
    db: Session,
    dataset_id: int,
    filepath: str,
    row_count: int,
    col_count: int,
    file_size: int,
    quality_score: float,
    change_summary: str,
    version_number: int
):
    db_version = models.DatasetVersion(
        dataset_id=dataset_id,
        version_number=version_number,
        filepath=filepath,
        row_count=row_count,
        col_count=col_count,
        file_size=file_size,
        quality_score=quality_score,
        change_summary=change_summary
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version

def get_latest_version(db: Session, dataset_id: int):
    return (
        db.query(models.DatasetVersion)
        .filter(models.DatasetVersion.dataset_id == dataset_id)
        .order_by(desc(models.DatasetVersion.version_number))
        .first()
    )

def get_version(db: Session, version_id: int):
    return db.query(models.DatasetVersion).filter(models.DatasetVersion.id == version_id).first()

def get_version_by_number(db: Session, dataset_id: int, version_number: int):
    return (
        db.query(models.DatasetVersion)
        .filter(
            models.DatasetVersion.dataset_id == dataset_id,
            models.DatasetVersion.version_number == version_number
        )
        .first()
    )

# CleaningLog operations
def log_cleaning_action(
    db: Session,
    version_id: int,
    action_type: str,
    column_name: str,
    details: str
):
    db_log = models.CleaningLog(
        version_id=version_id,
        action_type=action_type,
        column_name=column_name,
        details=details
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

# ChatMessage operations
def create_chat_message(db: Session, dataset_id: int, sender: str, message: str):
    db_message = models.ChatMessage(
        dataset_id=dataset_id,
        sender=sender,
        message=message
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_chat_history(db: Session, dataset_id: int):
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.dataset_id == dataset_id)
        .order_by(models.ChatMessage.timestamp)
        .all()
    )

def clear_chat_history(db: Session, dataset_id: int):
    db.query(models.ChatMessage).filter(models.ChatMessage.dataset_id == dataset_id).delete()
    db.commit()
