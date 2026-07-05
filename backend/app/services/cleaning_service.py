import pandas as pd
import numpy as np
import re
from typing import Tuple, Dict, Any, List

class CleaningService:
    @staticmethod
    def load_df(filepath: str) -> pd.DataFrame:
        """Loads a dataframe from a CSV path, attempting to handle common encodings."""
        from app.services.storage_service import StorageService
        return StorageService.read_csv_robustly(filepath)

    @staticmethod
    def save_df(df: pd.DataFrame, filepath: str) -> None:
        """Saves the dataframe as a CSV."""
        df.to_csv(filepath, index=False)

    @staticmethod
    def impute_missing(df: pd.DataFrame, column: str, strategy: str) -> Tuple[pd.DataFrame, str]:
        """Imputes missing values using various strategies."""
        df = df.copy()
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found.")

        initial_nulls = int(df[column].isnull().sum())
        if initial_nulls == 0:
            return df, f"Column '{column}' had no missing values. No action taken."

        detail = ""
        if strategy == "mean":
            if not pd.api.types.is_numeric_dtype(df[column]):
                raise ValueError(f"Mean imputation requires a numerical column. '{column}' is not numerical.")
            mean_val = df[column].mean()
            df[column] = df[column].fillna(mean_val)
            detail = f"Imputed {initial_nulls} missing values in '{column}' using mean ({mean_val:.4f})."

        elif strategy == "median":
            if not pd.api.types.is_numeric_dtype(df[column]):
                raise ValueError(f"Median imputation requires a numerical column. '{column}' is not numerical.")
            median_val = df[column].median()
            df[column] = df[column].fillna(median_val)
            detail = f"Imputed {initial_nulls} missing values in '{column}' using median ({median_val:.4f})."

        elif strategy == "mode":
            mode_series = df[column].mode()
            if mode_series.empty:
                raise ValueError(f"No mode found in column '{column}' to impute.")
            mode_val = mode_series[0]
            df[column] = df[column].fillna(mode_val)
            detail = f"Imputed {initial_nulls} missing values in '{column}' using mode ('{mode_val}')."

        elif strategy == "ffill":
            df[column] = df[column].ffill()
            new_nulls = int(df[column].isnull().sum())
            filled = initial_nulls - new_nulls
            detail = f"Applied Forward Fill on '{column}', filling {filled} missing values."

        elif strategy == "bfill":
            df[column] = df[column].bfill()
            new_nulls = int(df[column].isnull().sum())
            filled = initial_nulls - new_nulls
            detail = f"Applied Backward Fill on '{column}', filling {filled} missing values."

        elif strategy == "drop_rows":
            df = df.dropna(subset=[column])
            detail = f"Dropped {initial_nulls} rows where '{column}' had missing values."

        elif strategy == "drop_col":
            df = df.drop(columns=[column])
            detail = f"Dropped column '{column}' which had {initial_nulls} missing values."

        else:
            raise ValueError(f"Invalid imputation strategy: {strategy}")

        return df, detail

    @staticmethod
    def remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
        """Detects and removes duplicate rows."""
        initial_rows = len(df)
        df_cleaned = df.drop_duplicates()
        duplicates_removed = initial_rows - len(df_cleaned)
        
        if duplicates_removed > 0:
            detail = f"Detected and removed {duplicates_removed} duplicate rows."
        else:
            detail = "No duplicate rows detected. No action taken."
        return df_cleaned, detail

    @staticmethod
    def correct_data_type(df: pd.DataFrame, column: str, target_type: str, date_format: str = None) -> Tuple[pd.DataFrame, str]:
        """Converts columns to numerical, datetime, categorical, or text formats."""
        df = df.copy()
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found.")

        detail = ""
        if target_type == "numeric":
            # Coerce errors to NaN, then fill or alert
            original_nans = df[column].isna().sum()
            df[column] = pd.to_numeric(df[column], errors="coerce")
            new_nans = df[column].isna().sum()
            coerced = new_nans - original_nans
            detail = f"Converted '{column}' to numeric type. {coerced} invalid strings were set to NaN."

        elif target_type == "datetime":
            original_nans = df[column].isna().sum()
            df[column] = pd.to_datetime(df[column], format=date_format, errors="coerce")
            new_nans = df[column].isna().sum()
            coerced = new_nans - original_nans
            detail = f"Converted '{column}' to datetime. {coerced} values set to NaN due to formatting issues."

        elif target_type == "categorical":
            df[column] = df[column].astype("category")
            detail = f"Converted '{column}' to categorical type with {df[column].nunique()} distinct categories."

        elif target_type == "text":
            df[column] = df[column].astype(str)
            # Re-convert 'nan' strings back to actual NaN
            df[column] = df[column].replace("nan", np.nan).replace("None", np.nan)
            detail = f"Converted '{column}' to text (string) type."
        else:
            raise ValueError(f"Unsupported target type: {target_type}")

        return df, detail

    @staticmethod
    def handle_outliers(df: pd.DataFrame, column: str, method: str, strategy: str, threshold: float = 3.0) -> Tuple[pd.DataFrame, str]:
        """Detects outliers using IQR or Z-score, and removes or caps them."""
        df = df.copy()
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found.")

        if not pd.api.types.is_numeric_dtype(df[column]):
            raise ValueError(f"Outlier detection requires a numerical column. '{column}' is not numerical.")

        # Exclude null values for analysis
        series = df[column].dropna()
        if len(series) == 0:
            return df, f"Column '{column}' is empty. No outlier action taken."

        # Detect Outliers
        lower_bound = 0.0
        upper_bound = 0.0
        if method == "iqr":
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            multiplier = threshold if threshold is not None else 1.5
            lower_bound = q1 - multiplier * iqr
            upper_bound = q3 + multiplier * iqr
        elif method == "zscore":
            mean = series.mean()
            std = series.std()
            if std == 0:
                return df, f"Standard deviation of '{column}' is zero. Outliers cannot be calculated."
            z_thresh = threshold if threshold is not None else 3.0
            lower_bound = mean - z_thresh * std
            upper_bound = mean + z_thresh * std
        else:
            raise ValueError(f"Invalid outlier detection method: {method}")

        # Outlier counts
        outlier_mask = (df[column] < lower_bound) | (df[column] > upper_bound)
        outlier_count = int(outlier_mask.sum())

        if outlier_count == 0:
            return df, f"No outliers detected in '{column}' using {method.upper()} with threshold {threshold}."

        detail = ""
        if strategy == "remove":
            df = df[~outlier_mask]
            detail = f"Removed {outlier_count} outlier rows from '{column}' (bounds: [{lower_bound:.2f}, {upper_bound:.2f}])."
        elif strategy == "cap":
            # Cap values
            df[column] = np.clip(df[column], lower_bound, upper_bound)
            detail = f"Capped {outlier_count} outliers in '{column}' at limits [{lower_bound:.2f}, {upper_bound:.2f}]."
        elif strategy == "keep":
            detail = f"Identified {outlier_count} outliers in '{column}' (bounds: [{lower_bound:.2f}, {upper_bound:.2f}]), but kept them as per preference."
        else:
            raise ValueError(f"Invalid outlier handling strategy: {strategy}")

        return df, detail

    @staticmethod
    def clean_text(df: pd.DataFrame, column: str, remove_extra_spaces: bool, casing: str = None, remove_special_chars: bool = False) -> Tuple[pd.DataFrame, str]:
        """Cleans a text column by trimming, casing, and removing special characters."""
        df = df.copy()
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found.")

        # Cast to string first
        df[column] = df[column].astype(str).replace("nan", np.nan).replace("None", np.nan)
        
        detail_steps = []
        
        def process_text(val):
            if pd.isna(val):
                return val
            text = str(val)
            if remove_extra_spaces:
                text = " ".join(text.split())
            if remove_special_chars:
                text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
            if casing == "lower":
                text = text.lower()
            elif casing == "upper":
                text = text.upper()
            elif casing == "title":
                text = text.title()
            return text

        df[column] = df[column].apply(process_text)

        if remove_extra_spaces:
            detail_steps.append("trimmed extra whitespace")
        if remove_special_chars:
            detail_steps.append("removed special characters")
        if casing:
            detail_steps.append(f"applied '{casing}' casing")

        detail = f"Cleaned text in '{column}': " + ", ".join(detail_steps) + "."
        return df, detail

    @staticmethod
    def execute_column_op(df: pd.DataFrame, action: str, column: str, new_name: str = None, expression: str = None) -> Tuple[pd.DataFrame, str]:
        """Performs column rename, deletion, or new formula-based column creation."""
        df = df.copy()
        detail = ""

        if action == "rename":
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found.")
            if not new_name:
                raise ValueError("New column name is required for renaming.")
            if new_name in df.columns:
                raise ValueError(f"A column named '{new_name}' already exists.")
            df = df.rename(columns={column: new_name})
            detail = f"Renamed column '{column}' to '{new_name}'."

        elif action == "delete":
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found.")
            df = df.drop(columns=[column])
            detail = f"Deleted column '{column}'."

        elif action == "create":
            if not column:
                raise ValueError("New column name is required.")
            if column in df.columns:
                raise ValueError(f"Column '{column}' already exists.")
            if not expression:
                raise ValueError("Expression/Formula is required to create a new column.")

            # Support formulas: 'col1 + col2', 'col1 * 2.5', 'col1 - col2', 'col1 / col2'
            # Safe Parsing: Regex split on standard operators
            pattern = r"^([a-zA-Z0-9_ ]+)\s*([\+\-\*\/])\s*([a-zA-Z0-9_\. ]+)$"
            match = re.match(pattern, expression.strip())
            if not match:
                raise ValueError(
                    "Expression format invalid. Please use a simple binary formula like 'ColumnA * ColumnB' or 'ColumnA + 10'."
                )

            operand1_str = match.group(1).strip()
            operator = match.group(2)
            operand2_str = match.group(3).strip()

            # Resolve Operand 1
            if operand1_str in df.columns:
                if not pd.api.types.is_numeric_dtype(df[operand1_str]):
                    raise ValueError(f"Operand '{operand1_str}' must be a numerical column.")
                val1 = df[operand1_str]
            else:
                try:
                    val1 = float(operand1_str)
                except ValueError:
                    raise ValueError(f"Operand '{operand1_str}' is neither a column nor a valid number.")

            # Resolve Operand 2
            if operand2_str in df.columns:
                if not pd.api.types.is_numeric_dtype(df[operand2_str]):
                    raise ValueError(f"Operand '{operand2_str}' must be a numerical column.")
                val2 = df[operand2_str]
            else:
                try:
                    val2 = float(operand2_str)
                except ValueError:
                    raise ValueError(f"Operand '{operand2_str}' is neither a column nor a valid number.")

            # Compute
            if operator == "+":
                df[column] = val1 + val2
            elif operator == "-":
                df[column] = val1 - val2
            elif operator == "*":
                df[column] = val1 * val2
            elif operator == "/":
                # Guard against divide by zero
                if isinstance(val2, (int, float)):
                    if val2 == 0:
                        raise ValueError("Division by constant zero is not allowed.")
                    df[column] = val1 / val2
                else:
                    df[column] = val1 / val2.replace(0, np.nan)
            
            detail = f"Created calculated column '{column}' from formula: '{expression}'."

        else:
            raise ValueError(f"Invalid column operation: {action}")

        return df, detail
