import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple

class EDAService:
    @staticmethod
    def clean_json_val(val: Any) -> Any:
        """Helper to convert NaN, Inf, and NaT to None so they serialize cleanly to JSON."""
        if pd.isna(val):
            return None
        if isinstance(val, (float, np.float64, np.float32)):
            if np.isinf(val) or np.isnan(val):
                return None
            return float(val)
        if isinstance(val, (int, np.int64, np.int32)):
            return int(val)
        if isinstance(val, np.ndarray):
            return [EDAService.clean_json_val(x) for x in val]
        return val

    @classmethod
    def clean_dict(cls, d: Any) -> Any:
        """Recursively cleans dictionary or list values for JSON compliance."""
        if isinstance(d, dict):
            return {k: cls.clean_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [cls.clean_dict(x) for x in d]
        else:
            return cls.clean_json_val(d)

    @classmethod
    def get_quality_score(cls, df: pd.DataFrame) -> float:
        """Calculates a quality score out of 100 based on missing, duplicate, and outlier ratios."""
        if len(df) == 0:
            return 0.0

        total_cells = df.size
        missing_cells = int(df.isnull().sum().sum())
        missing_ratio = missing_cells / total_cells if total_cells > 0 else 0.0

        # Duplicate ratio
        dup_rows = int(df.duplicated().sum())
        dup_ratio = dup_rows / len(df)

        # Outlier ratio (only on numerical columns)
        num_cols = df.select_dtypes(include=[np.number]).columns
        outlier_cells = 0
        total_num_cells = 0
        for col in num_cols:
            series = df[col].dropna()
            if len(series) > 5:  # Check outliers only if we have sufficient samples
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = ((series < lower) | (series > upper)).sum()
                outlier_cells += outliers
            total_num_cells += len(series)

        outlier_ratio = outlier_cells / total_num_cells if total_num_cells > 0 else 0.0

        # Weights
        # 40% missing values, 30% duplicates, 30% outliers
        deduction = (missing_ratio * 40.0) + (dup_ratio * 30.0) + (outlier_ratio * 30.0)
        
        # Max score is 100, min is 0
        score = max(0.0, min(100.0, 100.0 - deduction))
        return round(score, 2)

    @classmethod
    def analyze_dataset(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """Runs the entire EDA analysis and returns stats formatted for frontend widgets and charts."""
        # Row & Col Info
        rows, cols = df.shape
        
        # Memory usage
        memory_bytes = df.memory_usage(deep=True).sum()
        if memory_bytes < 1024:
            memory_str = f"{memory_bytes} B"
        elif memory_bytes < 1024 * 1024:
            memory_str = f"{memory_bytes / 1024:.2f} KB"
        else:
            memory_str = f"{memory_bytes / (1024 * 1024):.2f} MB"

        # Column Datatypes (convert to readable string descriptions)
        dtypes = {}
        for col, dtype in df.dtypes.items():
            if pd.api.types.is_datetime64_any_dtype(dtype):
                dtypes[col] = "datetime"
            elif pd.api.types.is_numeric_dtype(dtype):
                dtypes[col] = "numeric"
            elif pd.api.types.is_categorical_dtype(dtype) or isinstance(dtype, pd.CategoricalDtype):
                dtypes[col] = "categorical"
            elif dtype == object:
                # Inspect values to see if it resembles datetime
                sample = df[col].dropna().head(50).astype(str)
                is_dt = False
                if len(sample) > 0:
                    try:
                        # Test parser
                        pd.to_datetime(sample, errors="raise")
                        is_dt = True
                    except Exception:
                        pass
                dtypes[col] = "datetime" if is_dt else "text"
            else:
                dtypes[col] = str(dtype)

        # Missing cells summary
        null_counts = df.isnull().sum().to_dict()

        # Descriptive Statistics
        descriptive_stats = {}
        # Numerical stats
        num_cols = df.select_dtypes(include=[np.number]).columns
        for col in num_cols:
            series = df[col].dropna()
            if len(series) > 0:
                modes = series.mode()
                mode_val = modes[0] if not modes.empty else None
                descriptive_stats[col] = {
                    "type": "numeric",
                    "count": int(df[col].count()),
                    "missing_pct": float(df[col].isnull().mean() * 100),
                    "mean": float(series.mean()),
                    "median": float(series.median()),
                    "mode": mode_val,
                    "min": float(series.min()),
                    "max": float(series.max()),
                    "std": float(series.std()) if len(series) > 1 else 0.0,
                    "var": float(series.var()) if len(series) > 1 else 0.0,
                    "q25": float(series.quantile(0.25)),
                    "q50": float(series.quantile(0.50)),
                    "q75": float(series.quantile(0.75)),
                }
            else:
                descriptive_stats[col] = {"type": "numeric", "count": 0, "missing_pct": 100.0}

        # Categorical/Text Stats
        cat_cols = [c for c in df.columns if c not in num_cols]
        categorical_summary = {}
        for col in cat_cols:
            series = df[col].dropna().astype(str)
            if len(series) > 0:
                counts = series.value_counts()
                top_counts = counts.head(10).to_dict()
                unique_count = int(series.nunique())
                categorical_summary[col] = {
                    "unique_count": unique_count,
                    "top_categories": top_counts,
                }
                # Also place basic stats in descriptive_stats
                descriptive_stats[col] = {
                    "type": "categorical",
                    "count": int(df[col].count()),
                    "missing_pct": float(df[col].isnull().mean() * 100),
                    "unique_count": unique_count,
                    "most_frequent": series.mode()[0] if not series.mode().empty else None,
                    "most_frequent_count": int(counts.iloc[0]) if len(counts) > 0 else 0
                }
            else:
                descriptive_stats[col] = {"type": "categorical", "count": 0, "missing_pct": 100.0}
                categorical_summary[col] = {"unique_count": 0, "top_categories": {}}

        # Correlation Matrix (Pearson)
        corr_matrix_dict = {}
        strong_relationships = []
        if len(num_cols) > 1:
            corr_df = df[num_cols].corr(method="pearson")
            corr_matrix_dict = corr_df.to_dict()
            
            # Find strong correlations (|r| >= 0.7) and ignore identity matrix duplicates
            cols_list = list(num_cols)
            for i in range(len(cols_list)):
                for j in range(i + 1, len(cols_list)):
                    col_a = cols_list[i]
                    col_b = cols_list[j]
                    val = corr_df.loc[col_a, col_b]
                    if not pd.isna(val) and abs(val) >= 0.7:
                        strong_relationships.append({
                            "column1": col_a,
                            "column2": col_b,
                            "coefficient": float(val),
                            "direction": "positive" if val > 0 else "negative"
                        })
            # Sort by absolute strength
            strong_relationships.sort(key=lambda x: abs(x["coefficient"]), reverse=True)

        correlation_result = {
            "matrix": corr_matrix_dict,
            "strong_relationships": strong_relationships
        }

        # Time Series Auto-Detection and trend generation
        time_series_detected = [col for col, dtype in dtypes.items() if dtype == "datetime"]
        time_series_data = None

        if time_series_detected and len(num_cols) > 0:
            # Let's pick the first datetime column and analyze trend
            ts_col = time_series_detected[0]
            # Convert values to datetime temporarily
            temp_dt = pd.to_datetime(df[ts_col], errors="coerce")
            
            # Drop null timestamps
            ts_df = df.copy()
            ts_df["__parsed_date__"] = temp_dt
            ts_df = ts_df.dropna(subset=["__parsed_date__"])
            
            if len(ts_df) > 0:
                # Sort by date
                ts_df = ts_df.sort_values(by="__parsed_date__")
                
                # Check frequency, group accordingly
                # If date range is large (> 2 years), group by Month or Year. Else group by Date.
                min_date = ts_df["__parsed_date__"].min()
                max_date = ts_df["__parsed_date__"].max()
                delta_days = (max_date - min_date).days
                
                if delta_days > 730:
                    group_freq = "YE"  # Year End
                    date_format_str = "%Y"
                elif delta_days > 60:
                    group_freq = "ME"  # Month End
                    date_format_str = "%Y-%m"
                else:
                    group_freq = "D"   # Day
                    date_format_str = "%Y-%m-%d"

                try:
                    grouped = ts_df.groupby(pd.Grouper(key="__parsed_date__", freq=group_freq))
                    
                    # Take up to top 3 numerical columns to aggregate
                    num_cols_to_plot = list(num_cols)[:3]
                    
                    trend_records = []
                    for name, group in grouped:
                        if len(group) > 0:
                            record = {
                                "date": name.strftime(date_format_str),
                                "count": len(group)
                            }
                            for col in num_cols_to_plot:
                                record[col] = float(group[col].mean()) if not pd.isna(group[col].mean()) else 0.0
                            trend_records.append(record)
                    
                    # Limit trend data count to 100 points max to avoid overloading frontend
                    if len(trend_records) > 100:
                        step = len(trend_records) // 100
                        trend_records = trend_records[::step]

                    time_series_data = {
                        "date_column": ts_col,
                        "aggregated_columns": num_cols_to_plot,
                        "data": trend_records
                    }
                except Exception:
                    pass  # If grouping fails (e.g. incorrect timezone or format mismatch), skip it

        summary = {
            "shape": [rows, cols],
            "memory_usage": memory_str,
            "null_summary": null_counts,
            "dtypes": dtypes,
            "descriptive_stats": descriptive_stats,
            "categorical_summary": categorical_summary,
            "correlation": correlation_result,
            "time_series_detected": time_series_detected,
            "time_series_data": time_series_data
        }

        return cls.clean_dict(summary)
