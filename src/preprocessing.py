# =============================================================================
# FILE PURPOSE & OVERVIEW
# =============================================================================
# This file (`src/preprocessing.py`) handles all data loading, validation, and cleaning.
# It ensures that the raw CSV data is properly formatted before it gets sent to the AI.
#
# FUNCTION EXPLANATIONS:
# -----------------------------------------------------------------------------
# - load_data():
#   Reads the raw CSV file into a pandas DataFrame and checks if the file exists and is not empty.
#
# - validate_data():
#   Checks if all required columns (like FeedbackID, Text, Rating, etc.) are present in the data.
#
# - get_data_quality_summary():
#   Calculates statistics about the data quality (e.g., counting how many rows have missing text
#   or invalid ratings) to show what needs cleaning.
#
# - clean_data():
#   The main cleaning function. It removes duplicates, drops empty rows, fixes date formats,
#   and ensures ratings and customer types are valid.
#
# - print_data_quality_report():
#   Takes the statistics from get_data_quality_summary() and prints them nicely to the console.
# =============================================================================

"""Data loading, validation, cleaning, and preprocessing module for Customer Feedback Intelligence."""

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pandas as pd

# Expected columns in the feedback dataset
REQUIRED_COLUMNS: List[str] = ["FeedbackID", "Text", "Rating", "Date", "CustomerType"]

# Valid customer tiers
VALID_CUSTOMER_TYPES: List[str] = ["Standard", "Premium", "Enterprise"]


def load_data(file_path: str | Path) -> pd.DataFrame:
    """Load customer feedback dataset from a CSV file.

    Args:
        file_path (str | Path): Relative or absolute path to the CSV file.

    Returns:
        pd.DataFrame: Loaded raw DataFrame.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the CSV file is empty.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Feedback data file not found at: {file_path}")

    if os.path.getsize(path) == 0:
        raise ValueError(f"The CSV file at {file_path} is empty.")

    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {e}")

    if df.empty:
        raise ValueError(f"The CSV file at {file_path} contains no data rows.")

    return df


def validate_data(df: pd.DataFrame) -> bool:
    """Validate that the DataFrame conforms to the required schema and columns.

    Args:
        df (pd.DataFrame): DataFrame to validate.

    Returns:
        bool: True if schema is valid.

    Raises:
        ValueError: If any required column is missing.
    """
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("Input data must be a valid pandas DataFrame.")

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")

    return True


def get_data_quality_summary(df_raw: pd.DataFrame, df_cleaned: pd.DataFrame | None = None) -> Dict[str, Any]:
    """Compute data quality statistics and count anomalies before and after cleaning.

    Args:
        df_raw (pd.DataFrame): The raw uncleaned DataFrame.
        df_cleaned (pd.DataFrame, optional): The cleaned DataFrame.

    Returns:
        Dict[str, Any]: Quality metrics summary.
    """
    total_raw = len(df_raw)

    # 1. Missing or whitespace-only text
    missing_text = int(df_raw["Text"].isna().sum() + (df_raw["Text"].astype(str).str.strip() == "").sum())

    # 2. Duplicate FeedbackID
    duplicate_ids = int(df_raw["FeedbackID"].duplicated().sum())

    # 3. Invalid rating (non-numeric or not in range 1-5)
    numeric_ratings = pd.to_numeric(df_raw["Rating"], errors="coerce")
    invalid_ratings = int(numeric_ratings.isna().sum() + ((numeric_ratings < 1) | (numeric_ratings > 5)).sum())

    # 4. Invalid dates
    parsed_dates = pd.to_datetime(df_raw["Date"], errors="coerce")
    invalid_dates = int(parsed_dates.isna().sum())

    # 5. Invalid CustomerType
    invalid_customer_types = int((~df_raw["CustomerType"].astype(str).isin(VALID_CUSTOMER_TYPES)).sum())

    summary = {
        "total_raw_records": total_raw,
        "missing_text_count": missing_text,
        "duplicate_id_count": duplicate_ids,
        "invalid_rating_count": invalid_ratings,
        "invalid_date_count": invalid_dates,
        "invalid_customer_type_count": invalid_customer_types,
        "total_cleaned_records": len(df_cleaned) if df_cleaned is not None else None,
    }

    return summary


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize customer feedback records.

    Cleaning steps:
    1. Validate required columns exist.
    2. Make a copy to avoid mutating raw inputs.
    3. Remove duplicate FeedbackID records (keeping the first occurrence).
    4. Strip whitespace from text and drop empty/missing text rows.
    5. Convert Rating to numeric, keep only integer values 1 to 5.
    6. Convert Date to datetime format and drop unparseable dates.
    7. Validate and filter CustomerType to allowed tiers (Standard, Premium, Enterprise).
    8. Reset DataFrame index.

    Args:
        df (pd.DataFrame): Raw feedback DataFrame.

    Returns:
        pd.DataFrame: Cleaned and validated DataFrame.
    """
    validate_data(df)

    # Work on a copy
    cleaned = df.copy()

    # Step 1: Remove duplicate FeedbackID
    cleaned = cleaned.drop_duplicates(subset=["FeedbackID"], keep="first")

    # Step 2: Clean Text - drop NaN and empty/whitespace strings
    cleaned = cleaned.dropna(subset=["Text"])
    cleaned["Text"] = cleaned["Text"].astype(str).str.strip()
    cleaned = cleaned[cleaned["Text"] != ""]

    # Step 3: Clean Rating - convert to numeric, filter between 1 and 5, cast to int
    cleaned["Rating"] = pd.to_numeric(cleaned["Rating"], errors="coerce")
    cleaned = cleaned.dropna(subset=["Rating"])
    cleaned = cleaned[(cleaned["Rating"] >= 1) & (cleaned["Rating"] <= 5)]
    cleaned["Rating"] = cleaned["Rating"].astype(int)

    # Step 4: Clean Date - parse to datetime, drop invalid dates, format as YYYY-MM-DD
    cleaned["Date"] = pd.to_datetime(cleaned["Date"], errors="coerce")
    cleaned = cleaned.dropna(subset=["Date"])

    # Step 5: Clean CustomerType - filter strictly to valid categories
    cleaned["CustomerType"] = cleaned["CustomerType"].astype(str).str.strip()
    cleaned = cleaned[cleaned["CustomerType"].isin(VALID_CUSTOMER_TYPES)]

    # Step 6: Reset index
    cleaned = cleaned.reset_index(drop=True)

    return cleaned


def print_data_quality_report(summary: Dict[str, Any]) -> None:
    """Print a nicely formatted data quality summary table to the console.

    Args:
        summary (Dict[str, Any]): Data quality metrics dictionary.
    """
    print("\n" + "=" * 55)
    print("           DATA QUALITY & CLEANING SUMMARY          ")
    print("=" * 55)
    print(f"  • Total Raw Records:           {summary['total_raw_records']:>6}")
    print(f"  • Duplicate Feedback IDs:      {summary['duplicate_id_count']:>6}")
    print(f"  • Missing / Empty Text Rows:   {summary['missing_text_count']:>6}")
    print(f"  • Invalid Rating Values:       {summary['invalid_rating_count']:>6}")
    print(f"  • Invalid Date Formats:        {summary['invalid_date_count']:>6}")
    print(f"  • Invalid Customer Types:      {summary['invalid_customer_type_count']:>6}")
    print("-" * 55)
    if summary["total_cleaned_records"] is not None:
        removed = summary["total_raw_records"] - summary["total_cleaned_records"]
        print(f"  • Total Cleaned Records:       {summary['total_cleaned_records']:>6}")
        print(f"  • Total Anomalies Filtered:    {removed:>6}")
    print("=" * 55 + "\n")
