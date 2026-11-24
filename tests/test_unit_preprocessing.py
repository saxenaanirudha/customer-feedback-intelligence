"""Unit tests for src/preprocessing.py module."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.preprocessing import (
    REQUIRED_COLUMNS,
    VALID_CUSTOMER_TYPES,
    clean_data,
    get_data_quality_summary,
    load_data,
    print_data_quality_report,
    validate_data,
)


class TestLoadData:
    """Tests for load_data function."""

    def test_load_valid_csv(self, temp_dir: Path, sample_raw_data: pd.DataFrame):
        csv_path = temp_dir / "valid_feedback.csv"
        sample_raw_data.to_csv(csv_path, index=False)

        df = load_data(csv_path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5
        assert list(df.columns) == REQUIRED_COLUMNS

    def test_load_nonexistent_file_raises_error(self, temp_dir: Path):
        with pytest.raises(FileNotFoundError, match="Feedback data file not found"):
            load_data(temp_dir / "missing.csv")

    def test_load_zero_byte_file_raises_error(self, temp_dir: Path):
        empty_file = temp_dir / "empty.csv"
        empty_file.touch()

        with pytest.raises(ValueError, match="is empty"):
            load_data(empty_file)

    def test_load_csv_with_only_headers_raises_error(self, temp_dir: Path):
        header_only = temp_dir / "header_only.csv"
        header_only.write_text("FeedbackID,Text,Rating,Date,CustomerType\n", encoding="utf-8")

        with pytest.raises(ValueError, match="contains no data rows"):
            load_data(header_only)

    def test_load_malformed_csv_raises_error(self, temp_dir: Path):
        malformed = temp_dir / "malformed.csv"
        malformed.write_bytes(b"\x00\x01\x02\xff\xfe")

        with pytest.raises(ValueError, match="Failed to read CSV file"):
            load_data(malformed)


class TestValidateData:
    """Tests for validate_data function."""

    def test_validate_valid_dataframe(self, sample_raw_data: pd.DataFrame):
        assert validate_data(sample_raw_data) is True

    def test_validate_missing_columns_raises_error(self):
        df_missing = pd.DataFrame({"FeedbackID": ["F1"], "Text": ["Test"]})
        with pytest.raises(ValueError, match="Missing required columns in dataset"):
            validate_data(df_missing)

    def test_validate_none_input_raises_error(self):
        with pytest.raises(ValueError, match="Input data must be a valid pandas DataFrame"):
            validate_data(None)

    def test_validate_non_dataframe_input_raises_error(self):
        with pytest.raises(ValueError, match="Input data must be a valid pandas DataFrame"):
            validate_data([1, 2, 3])  # type: ignore


class TestGetDataQualitySummary:
    """Tests for get_data_quality_summary function."""

    def test_quality_summary_counts_anomalies_accurately(self, sample_raw_data_with_anomalies: pd.DataFrame):
        summary = get_data_quality_summary(sample_raw_data_with_anomalies)

        assert summary["total_raw_records"] == 10
        assert summary["duplicate_id_count"] == 1  # F001 duplicated
        assert summary["missing_text_count"] == 2  # whitespace string + None
        assert summary["invalid_rating_count"] == 3  # 7, -1, 'abc'
        assert summary["invalid_date_count"] == 1  # 'invalid-date'
        assert summary["invalid_customer_type_count"] == 1  # 'UnknownTier'
        assert summary["total_cleaned_records"] is None

    def test_quality_summary_with_cleaned_records(
        self, sample_raw_data: pd.DataFrame, sample_cleaned_data: pd.DataFrame
    ):
        summary = get_data_quality_summary(sample_raw_data, sample_cleaned_data)
        assert summary["total_raw_records"] == 5
        assert summary["total_cleaned_records"] == 3

    def test_print_data_quality_report_executes_without_error(
        self, sample_raw_data: pd.DataFrame, sample_cleaned_data: pd.DataFrame, capsys
    ):
        summary = get_data_quality_summary(sample_raw_data, sample_cleaned_data)
        print_data_quality_report(summary)
        captured = capsys.readouterr()
        assert "DATA QUALITY & CLEANING SUMMARY" in captured.out
        assert "Total Raw Records:" in captured.out
        assert "Total Cleaned Records:" in captured.out


class TestCleanData:
    """Tests for clean_data function."""

    def test_clean_data_removes_duplicates_and_anomalies(self, sample_raw_data_with_anomalies: pd.DataFrame):
        cleaned = clean_data(sample_raw_data_with_anomalies)

        # Expected valid rows: F001 (first), F009
        assert len(cleaned) == 2
        assert set(cleaned["FeedbackID"]) == {"F001", "F009"}
        assert cleaned["Rating"].dtype == np.int64 or cleaned["Rating"].dtype == int
        assert all(cleaned["CustomerType"].isin(VALID_CUSTOMER_TYPES))
        assert all(cleaned["Rating"].between(1, 5))

    def test_clean_data_strips_text_whitespace(self):
        df = pd.DataFrame([{
            "FeedbackID": "F001",
            "Text": "   Padded feedback text   ",
            "Rating": 4,
            "Date": "2026-01-01",
            "CustomerType": "Standard",
        }])
        cleaned = clean_data(df)
        assert cleaned.iloc[0]["Text"] == "Padded feedback text"

    def test_clean_data_normalizes_customer_type_whitespace(self):
        df = pd.DataFrame([{
            "FeedbackID": "F001",
            "Text": "Good feature set",
            "Rating": 4,
            "Date": "2026-01-01",
            "CustomerType": "  Enterprise  ",
        }])
        cleaned = clean_data(df)
        assert len(cleaned) == 1
        assert cleaned.iloc[0]["CustomerType"] == "Enterprise"

    def test_clean_data_drops_all_missing_text_variants(self):
        df = pd.DataFrame([
            {"FeedbackID": "F1", "Text": "", "Rating": 3, "Date": "2026-01-01", "CustomerType": "Standard"},
            {"FeedbackID": "F2", "Text": "    \t \n", "Rating": 3, "Date": "2026-01-01", "CustomerType": "Standard"},
            {"FeedbackID": "F3", "Text": None, "Rating": 3, "Date": "2026-01-01", "CustomerType": "Standard"},
            {"FeedbackID": "F4", "Text": np.nan, "Rating": 3, "Date": "2026-01-01", "CustomerType": "Standard"},
        ])
        cleaned = clean_data(df)
        assert len(cleaned) == 0

    def test_clean_data_drops_out_of_bound_ratings(self):
        df = pd.DataFrame([
            {"FeedbackID": "F1", "Text": "Review 1", "Rating": 0, "Date": "2026-01-01", "CustomerType": "Standard"},
            {"FeedbackID": "F2", "Text": "Review 2", "Rating": 6, "Date": "2026-01-01", "CustomerType": "Standard"},
            {"FeedbackID": "F3", "Text": "Review 3", "Rating": 1, "Date": "2026-01-01", "CustomerType": "Standard"},
            {"FeedbackID": "F4", "Text": "Review 4", "Rating": 5, "Date": "2026-01-01", "CustomerType": "Standard"},
        ])
        cleaned = clean_data(df)
        assert len(cleaned) == 2
        assert set(cleaned["FeedbackID"]) == {"F3", "F4"}

    def test_clean_data_preserves_input_dataframe_immutability(self, sample_raw_data: pd.DataFrame):
        original_copy = sample_raw_data.copy(deep=True)
        _ = clean_data(sample_raw_data)
        pd.testing.assert_frame_equal(sample_raw_data, original_copy)
