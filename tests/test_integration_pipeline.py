"""Integration tests testing multi-module pipeline transitions."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src import classifier, executive_insights, insights, preprocessing, priority


class TestPipelineIntegration:
    """Integration test suite covering contract handoffs between modules."""

    @pytest.fixture
    def mock_classifier_llm(self, mock_openai_response: MagicMock):
        with patch("src.classifier.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai_cls.return_value = mock_client
            yield mock_client

    def test_stage_1_csv_to_preprocessing(self, temp_dir: Path, sample_raw_data_with_anomalies: pd.DataFrame):
        """Scenario 1: CSV file -> load_data -> validate_data -> clean_data."""
        csv_path = temp_dir / "raw_feedback.csv"
        sample_raw_data_with_anomalies.to_csv(csv_path, index=False)

        # 1. Load
        df_raw = preprocessing.load_data(csv_path)
        assert len(df_raw) == 10

        # 2. Validate
        assert preprocessing.validate_data(df_raw) is True

        # 3. Clean
        df_cleaned = preprocessing.clean_data(df_raw)
        assert len(df_cleaned) == 2  # Anomalies filtered out
        assert list(df_cleaned.columns) == preprocessing.REQUIRED_COLUMNS

    def test_stage_2_preprocessing_to_classification(self, sample_cleaned_data: pd.DataFrame):
        """Scenario 2: Cleaned Data -> FeedbackClassifier -> validate_classified_data."""
        cls = classifier.FeedbackClassifier(api_key=None)  # Use deterministic heuristic
        df_classified = cls.classify_feedback(sample_cleaned_data, show_progress=False)

        assert len(df_classified) == len(sample_cleaned_data)
        assert classifier.validate_classified_data(df_classified) is True
        for col in ["Sentiment", "Topic", "Urgency"]:
            assert col in df_classified.columns
            assert not df_classified[col].isna().any()

    def test_stage_3_classification_to_priority_scoring(
        self, temp_dir: Path, sample_classified_data: pd.DataFrame
    ):
        """Scenario 3: Classified Data -> Priority Engine -> Prioritized Data."""
        err_log = temp_dir / "priority_errors.log"
        errors = priority.validate_priority_inputs(sample_classified_data, error_log_path=err_log)
        assert len(errors) == 0

        df_prioritized = priority.add_priority_columns(sample_classified_data, error_log_path=err_log)
        assert len(df_prioritized) == len(sample_classified_data)
        for col in ["PriorityScore", "PriorityLevel", "PriorityReason"]:
            assert col in df_prioritized.columns
            assert not df_prioritized[col].isna().any()

        # Check score range
        assert df_prioritized["PriorityScore"].between(0, 100).all()

    def test_stage_4_priority_scoring_to_analytics(self, sample_prioritized_data: pd.DataFrame):
        """Scenario 4: Prioritized Data -> Business Analytics (KPIs, Trends, Segments)."""
        kpis = insights.get_overall_kpis(sample_prioritized_data)
        assert kpis["total_feedback"] == len(sample_prioritized_data)
        assert kpis["positive_pct"] + kpis["neutral_pct"] + kpis["negative_pct"] == pytest.approx(100.0, 0.1)

        trends = insights.get_feedback_trends(sample_prioritized_data)
        assert not trends.empty
        assert "TotalVolume" in trends.columns

        segments = insights.get_customer_segment_analysis(sample_prioritized_data)
        assert not segments.empty

    def test_stage_5_prioritized_data_to_executive_insights(self, sample_prioritized_data: pd.DataFrame):
        """Scenario 5: Prioritized Data -> Executive Context -> Executive Report."""
        context = executive_insights.build_executive_context(sample_prioritized_data)
        assert "overall_kpis" in context
        assert "representative_feedback" in context

        resp, is_cached, err = executive_insights.generate_executive_insights(
            sample_prioritized_data, force_refresh=True
        )
        assert resp is not None
        assert isinstance(resp, executive_insights.ExecutiveInsightsResponse)
        assert resp.overall_customer_health in ["Healthy", "At Risk", "Critical"]

    def test_stage_6_complete_end_to_end_pipeline(
        self, temp_dir: Path, sample_raw_data: pd.DataFrame
    ):
        """Scenario 6: Complete End-to-End Pipeline Verification in isolated temp directory."""
        raw_csv = temp_dir / "feedback.csv"
        cleaned_csv = temp_dir / "cleaned_feedback.csv"
        classified_csv = temp_dir / "classified_feedback.csv"
        prioritized_csv = temp_dir / "prioritized_feedback.csv"
        error_log = temp_dir / "priority_errors.log"

        sample_raw_data.to_csv(raw_csv, index=False)

        # 1. Preprocess
        df_raw = preprocessing.load_data(raw_csv)
        preprocessing.validate_data(df_raw)
        df_cleaned = preprocessing.clean_data(df_raw)
        df_cleaned.to_csv(cleaned_csv, index=False)
        assert cleaned_csv.exists()

        # 2. Classify
        cls = classifier.FeedbackClassifier(api_key=None)
        df_classified = cls.classify_feedback(df_cleaned, show_progress=False)
        classifier.validate_classified_data(df_classified)
        df_classified.to_csv(classified_csv, index=False)
        assert classified_csv.exists()

        # 3. Priority Score
        df_prioritized = priority.add_priority_columns(df_classified, error_log_path=error_log)
        df_prioritized.to_csv(prioritized_csv, index=False)
        assert prioritized_csv.exists()

        # 4. Analytics & Executive Insights
        kpis = insights.get_overall_kpis(df_prioritized)
        assert kpis["total_feedback"] == len(sample_raw_data)

        report, _, err = executive_insights.generate_executive_insights(df_prioritized)
        assert report is not None
        assert err is None
