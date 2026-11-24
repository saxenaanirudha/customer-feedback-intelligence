"""Failing regression test suite for confirmed defects (Barn Door Protocol: RED Phase).

These tests assert the REQUIRED, CORRECT behavior for each confirmed defect.
On the unpatched production codebase, these tests are EXPECTED TO FAIL (RED),
providing execution evidence of the defects before fixes are implemented.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from dashboard.app import load_pipeline_data
from main import run_pipeline
from src import classifier, insights, priority


class TestRedPhaseConfirmedDefects:
    """RED-phase tests that fail on unpatched code and turn GREEN upon applying approved fixes."""

    def test_red_defect_1_add_priority_columns_none_error_log_path_must_not_crash(self):
        """DEFECT 1 (HIGH): add_priority_columns crashes when error_log_path is None and errors exist.

        Expected Correct Behavior: Function must not crash with AttributeError,
        and must return the enriched DataFrame with priority columns.
        """
        df_invalid = pd.DataFrame([{
            "FeedbackID": "BAD_1",
            "CustomerType": "InvalidTier",
            "Urgency": "UltraHigh",
            "Sentiment": "Angry",
            "Rating": 10,
        }])

        # Should execute cleanly without AttributeError
        enriched = priority.add_priority_columns(df_invalid, error_log_path=None)
        assert isinstance(enriched, pd.DataFrame)
        assert "PriorityScore" in enriched.columns
        assert "PriorityLevel" in enriched.columns

    def test_red_defect_2_calculate_priority_score_float_rating_must_match_int_rating(self):
        """DEFECT 2 (MEDIUM): calculate_priority_score miscalculates float ratings.

        Expected Correct Behavior: rating=2.0 (float) must produce the exact same score (70)
        as rating=2 (int), instead of falling back to rating 3 (4 points -> 67).
        """
        score_int = priority.calculate_priority_score("High", "Standard", "Negative", 2)
        score_float = priority.calculate_priority_score("High", "Standard", "Negative", 2.0)

        assert score_int == 70
        assert score_float == 70, f"Expected 70 for float rating 2.0, but got {score_float}"

    def test_red_defect_3_insights_must_support_both_priority_label_formats(
        self, sample_prioritized_data: pd.DataFrame
    ):
        """DEFECT 3 (CRITICAL): insights.py fails to count high/critical issues when ' Priority' is stripped by dashboard.

        Expected Correct Behavior: get_overall_kpis and get_feedback_trends must recognize
        both 'Critical Priority'/'High Priority' AND 'Critical'/'High', ensuring dashboard
        analytics never collapse to 0.
        """
        df_dashboard_format = sample_prioritized_data.copy()
        df_dashboard_format["PriorityLevel"] = (
            df_dashboard_format["PriorityLevel"].str.replace(" Priority", "").str.strip()
        )

        kpis = insights.get_overall_kpis(df_dashboard_format)
        assert kpis["high_critical_count"] == 3, (
            f"Expected 3 high/critical issues with dashboard-format labels, but got {kpis['high_critical_count']}"
        )
        assert kpis["critical_count"] == 1, (
            f"Expected 1 critical issue with dashboard-format labels, but got {kpis['critical_count']}"
        )

    def test_red_defect_4_main_must_handle_empty_dataset_without_valueerror(
        self, monkeypatch, temp_dir: Path, capsys
    ):
        """DEFECT 4 (MEDIUM): main.py must handle empty dataset without ValueError or crash."""
        monkeypatch.setattr("main.BASE_DIR", temp_dir)
        data_dir = temp_dir / "data"
        output_dir = temp_dir / "output"
        data_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Raw data where all rows are dropped by clean_data
        df_all_anomalies = pd.DataFrame([
            {"FeedbackID": "BAD1", "Text": "   ", "Rating": 9, "Date": "bad-date", "CustomerType": "BadTier"},
        ])
        df_all_anomalies.to_csv(data_dir / "feedback.csv", index=False)
        monkeypatch.setenv("OPENAI_API_KEY", "")

        # In patched code, run_pipeline executes cleanly without crashing
        run_pipeline(force_reclassify=True)
        captured = capsys.readouterr()
        assert "Total Records Processed:   0" in captured.out
        assert "No feedback records available" in captured.out

    def test_red_defect_5_heuristic_topic_classification_must_not_collide_on_reports(self):
        """DEFECT 5 (LOW/ANOMALY): 'rep' in customer support keywords collides with 'reports'.

        Expected Correct Behavior: 'We need sprint reports' must be classified as 'Product Features',
        not hijacked into 'Customer Support' by the substring 'rep'.
        """
        cls = classifier.FeedbackClassifier(api_key=None)
        res = cls.classify_single_heuristic("We need sprint reports and backlog filters", rating=3)
        assert res["Topic"] == "Product Features", (
            f"Expected 'Product Features', but got '{res['Topic']}' due to 'rep' substring match"
        )

    def test_red_security_csv_export_must_escape_formula_prefixes(self):
        """SECURITY DEFECT 1 (HIGH): CSV export must sanitize formula characters (=, +, -, @).

        Expected Correct Behavior: Any text starting with dangerous formula characters
        must be prepended with a single quote or sanitized so spreadsheet software treats it as text.
        """
        from dashboard.app import to_safe_csv_bytes

        malicious_text = "=cmd|' /C calc'!A0"
        df = pd.DataFrame([{"FeedbackID": "F001", "Text": malicious_text}])

        safe_csv_bytes = to_safe_csv_bytes(df)
        safe_csv_str = safe_csv_bytes.decode("utf-8")

        # The dangerous formula trigger '=' must be escaped with "'"
        assert "'=cmd" in safe_csv_str
        assert not any(line.startswith("=cmd") or ",=cmd" in line for line in safe_csv_str.splitlines())
