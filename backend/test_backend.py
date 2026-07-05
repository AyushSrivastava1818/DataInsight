import sys
import os
import pandas as pd
import numpy as np

# Adjust path to import backend modules
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.cleaning_service import CleaningService
from app.services.eda_service import EDAService

DEMO_CSV = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sample_data", "company_sales_demo.csv")

def run_tests():
    print("--------------------------------------------------")
    print("Running Automated Tests on Cleaning and EDA Services")
    print("--------------------------------------------------")
    
    # 1. Load DataFrame
    assert os.path.exists(DEMO_CSV), f"Missing demo CSV: {DEMO_CSV}"
    df = CleaningService.load_df(DEMO_CSV)
    print(f"[SUCCESS] Loaded dataset. Shape: {df.shape}")
    
    # 2. Impute missing values
    # Column 'Units_Sold' has missing values
    col = "Units_Sold"
    initial_nulls = df[col].isnull().sum()
    print(f"Column '{col}' initial nulls: {initial_nulls}")
    assert initial_nulls > 0, "Units_Sold should contain null values in demo CSV."
    
    df_imputed, detail = CleaningService.impute_missing(df, col, "median")
    print(f"[SUCCESS] Median Imputation detail: {detail}")
    assert df_imputed[col].isnull().sum() == 0, "Imputed column should contain 0 nulls."
    
    # 3. Duplicate checks
    initial_rows = len(df)
    df_no_dups, detail = CleaningService.remove_duplicates(df)
    print(f"[SUCCESS] Duplicate removal detail: {detail}")
    assert len(df_no_dups) < initial_rows, "Duplicates should be removed."
    
    # 4. Outliers detection and capping
    # 'Customer_Rating' has outlier of 99.0
    col_out = "Customer_Rating"
    df_no_null_rating, _ = CleaningService.impute_missing(df, col_out, "median")
    
    df_capped, detail = CleaningService.handle_outliers(df_no_null_rating, col_out, "zscore", "cap", threshold=3.0)
    print(f"[SUCCESS] Outlier capping detail: {detail}")
    assert df_capped[col_out].max() < 99.0, "Outlier value (99.0) should have been capped."
    
    # 5. Text Cleaning
    col_text = "Customer_Name"
    df_text_cleaned, detail = CleaningService.clean_text(df, col_text, remove_extra_spaces=True, casing="upper")
    print(f"[SUCCESS] Text cleaning detail: {detail}")
    assert df_text_cleaned[col_text].iloc[0] == "ALICE SMITH", "Name spaces and casing incorrect."
    
    # 6. Column arithmetic
    df_col, detail = CleaningService.execute_column_op(
        df_imputed, 
        action="create", 
        column="Total_Price_Check", 
        expression="Units_Sold * Unit_Price"
    )
    print(f"[SUCCESS] Calculated Column detail: {detail}")
    assert "Total_Price_Check" in df_col.columns, "New column failed to create."
    
    # 7. Quality Score calculation
    score = EDAService.get_quality_score(df)
    print(f"[SUCCESS] Computed raw Data Quality Score: {score}/100")
    assert 0 <= score <= 100, "Quality Score out of bounds."
    
    print("\n--------------------------------------------------")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("--------------------------------------------------")

if __name__ == "__main__":
    run_tests()
