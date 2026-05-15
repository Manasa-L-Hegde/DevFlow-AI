"""
Data Loading Module
Loads train.xlsx into SQLite database for DevFlow AI
Run this ONCE before starting the app
"""

import pandas as pd
from db import create_engine_connection, table_exists
import os
import re


def normalize_column_name(column_name: str) -> str:
    """
    Convert a raw spreadsheet header into a SQLite-friendly column name.

    Examples:
        Product Name -> Product_Name
        Ship-Mode -> Ship_Mode
        Order/Date -> Order_Date
    """
    cleaned = column_name.strip()
    cleaned = cleaned.replace(" ", "_")
    cleaned = cleaned.replace("-", "_")
    cleaned = cleaned.replace("/", "_")
    cleaned = re.sub(r"[^0-9A-Za-z_]", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_")


def load_excel_to_sqlite(excel_file: str, table_name: str = "train"):
    """
    Load Excel file into SQLite database.
    
    Args:
        excel_file (str): Path to Excel file (e.g., "train.xlsx")
        table_name (str): Name of the table to create in database
        
    Returns:
        bool: True if successful
    """
    try:
        # Check if file exists
        if not os.path.exists(excel_file):
            print(f"[ERROR] {excel_file} not found!")
            return False
        
        # Read Excel file
        print(f"[INFO] Loading {excel_file}...")
        df = pd.read_excel(excel_file)

        # Normalize column names so SQL generation stays reliable.
        original_columns = list(df.columns)
        df.columns = [normalize_column_name(column) for column in df.columns]
        
        print(f"[OK] File loaded: {len(df)} rows, {len(df.columns)} columns")
        print("Original -> Normalized columns:")
        for original, normalized in zip(original_columns, df.columns):
            print(f"  {original} -> {normalized}")
        
        # Create database connection
        engine = create_engine_connection()
        
        # Replace table if it exists
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"[OK] Data loaded into table '{table_name}'")
        
        # Display preview
        print(f"\n[INFO] Preview of {table_name} table:")
        print(df.head())
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error loading data: {str(e)}")
        return False


if __name__ == "__main__":
    # Run this script to load data
    # Usage: python load_data.py
    
    print("=" * 50)
    print("DevFlow AI Data Loader")
    print("=" * 50)
    
    success = load_excel_to_sqlite("train.xlsx", "train")
    
    if success:
        print("\n[OK] Data loading complete!")
        print("You can now run: streamlit run app.py")
    else:
        print("\n[FAILED] Data loading failed. Check the error above.")
