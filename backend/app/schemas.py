from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

# Base Schemas
class CleaningLogSchema(BaseModel):
    id: int
    version_id: int
    action_type: str
    column_name: Optional[str] = None
    details: str
    timestamp: datetime

    class Config:
        from_attributes = True


class DatasetVersionSchema(BaseModel):
    id: int
    dataset_id: int
    version_number: int
    row_count: int
    col_count: int
    file_size: int
    quality_score: float
    change_summary: str
    created_at: datetime
    cleaning_logs: List[CleaningLogSchema] = []

    class Config:
        from_attributes = True


class DatasetSchema(BaseModel):
    id: int
    name: str
    created_at: datetime
    versions: List[DatasetVersionSchema] = []

    class Config:
        from_attributes = True


class ChatMessageSchema(BaseModel):
    id: int
    dataset_id: int
    sender: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


# Request Schemas for Cleaning Operations
class MissingValuesImputation(BaseModel):
    column: str
    strategy: str  # "mean", "median", "mode", "ffill", "bfill", "drop_rows", "drop_col"

class DropDuplicates(BaseModel):
    pass

class DataTypeCorrection(BaseModel):
    column: str
    target_type: str  # "numeric", "datetime", "categorical", "text"
    date_format: Optional[str] = None

class OutlierHandling(BaseModel):
    column: str
    method: str  # "iqr", "zscore"
    strategy: str  # "remove", "cap", "keep"
    threshold: Optional[float] = 3.0  # Used for Z-Score threshold (default 3) or IQR scaling (default 1.5)

class TextCleaning(BaseModel):
    column: str
    remove_extra_spaces: bool = True
    casing: Optional[str] = None  # "lower", "upper", "title"
    remove_special_chars: bool = False

class ColumnOperations(BaseModel):
    action: str  # "rename", "delete", "create"
    column: str
    new_name: Optional[str] = None
    expression: Optional[str] = None  # for creating columns, e.g. "col1 * col2" or similar basic ops

# API Response Schemas
class DatasetPreview(BaseModel):
    headers: List[str]
    types: Dict[str, str]
    null_counts: Dict[str, int]
    row_count: int
    col_count: int
    file_size: int
    quality_score: float
    data: List[Dict[str, Any]]

class CorrelationResult(BaseModel):
    matrix: Dict[str, Dict[str, Optional[float]]]
    strong_relationships: List[Dict[str, Any]]

class CategoricalColumnSummary(BaseModel):
    unique_count: int
    top_categories: Dict[str, int]

class EDASummary(BaseModel):
    shape: List[int]  # [rows, cols]
    memory_usage: str
    null_summary: Dict[str, int]
    dtypes: Dict[str, str]
    descriptive_stats: Dict[str, Dict[str, Any]]
    categorical_summary: Dict[str, CategoricalColumnSummary]
    correlation: CorrelationResult
    time_series_detected: List[str]
    time_series_data: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    sender: str
    message: str
    timestamp: datetime
