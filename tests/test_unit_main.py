"""Unit tests for main.py pipeline runner."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from main import run_pipeline


class TestMainPipeline:
    """Tests for main.py execution flow and options."""

    def test_run_pipeline_priority_only_with_missing_classified_file(self, monkeypatch, temp_dir: Path):
        """Test priority-only mode when output/classified_feedback.csv does not exist."""
        monkeypatch.setattr("main.BASE_DIR", temp_dir)
        (temp_dir / "output").mkdir(parents=True, exist_ok=True)

        with pytest.raises(SystemExit) as exc_info:
            run_pipeline(priority_only=True)
        assert exc_info.value.code == 1

    def test_run_pipeline_missing_raw_feedback_file(self, monkeypatch, temp_dir: Path):
        """Test full pipeline when data/feedback.csv does not exist."""
        monkeypatch.setattr("main.BASE_DIR", temp_dir)
        (temp_dir / "data").mkdir(parents=True, exist_ok=True)
        (temp_dir / "output").mkdir(parents=True, exist_ok=True)

        with pytest.raises(SystemExit) as exc_info:
            run_pipeline(force_reclassify=True)
        assert exc_info.value.code == 1

    def test_run_pipeline_end_to_end_in_temp_dir(
        self, monkeypatch, temp_dir: Path, sample_raw_data: pd.DataFrame, capsys
    ):
        """Test end-to-end pipeline run from raw data to prioritized output."""
        monkeypatch.setattr("main.BASE_DIR", temp_dir)
        data_dir = temp_dir / "data"
        output_dir = temp_dir / "output"
        data_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write raw CSV
        sample_raw_data.to_csv(data_dir / "feedback.csv", index=False)

        # Ensure no live OpenAI API key
        monkeypatch.setenv("OPENAI_API_KEY", "")

        # Run pipeline
        run_pipeline(force_reclassify=True)

        captured = capsys.readouterr()
        assert "CUSTOMER FEEDBACK INTELLIGENCE SYSTEM" in captured.out
        assert "PRIORITY SCORING SUMMARY" in captured.out
        assert "TOP 10 HIGHEST-PRIORITY ACTIONABLE ISSUES" in captured.out

        # Verify output files exist
        assert (output_dir / "cleaned_feedback.csv").exists()
        assert (output_dir / "classified_feedback.csv").exists()
        assert (output_dir / "prioritized_feedback.csv").exists()

        df_res = pd.read_csv(output_dir / "prioritized_feedback.csv")
        assert len(df_res) == 5
        assert "PriorityScore" in df_res.columns
        assert "PriorityLevel" in df_res.columns

    def test_run_pipeline_handles_empty_cleaned_dataset_gracefully(
        self, monkeypatch, temp_dir: Path, capsys
    ):
        """Verify run_pipeline handles empty or all-filtered raw data gracefully without crashing."""
        monkeypatch.setattr("main.BASE_DIR", temp_dir)
        data_dir = temp_dir / "data"
        output_dir = temp_dir / "output"
        data_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create raw CSV with only empty/invalid rows that get stripped by clean_data
        df_all_anomalies = pd.DataFrame([
            {"FeedbackID": "BAD1", "Text": "   ", "Rating": 9, "Date": "bad-date", "CustomerType": "BadTier"},
        ])
        df_all_anomalies.to_csv(data_dir / "feedback.csv", index=False)
        monkeypatch.setenv("OPENAI_API_KEY", "")

        # Must execute cleanly without ValueError or ZeroDivisionError
        run_pipeline(force_reclassify=True)
        captured = capsys.readouterr()
        assert "Total Records Processed:   0" in captured.out
        assert "No feedback records available" in captured.out
