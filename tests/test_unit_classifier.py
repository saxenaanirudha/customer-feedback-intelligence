"""Unit tests for src/classifier.py module."""

import json
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.classifier import (
    VALID_SENTIMENTS,
    VALID_TOPICS,
    VALID_URGENCIES,
    FeedbackClassifier,
    validate_classified_data,
)


class TestFeedbackClassifierHeuristic:
    """Tests for the rule-based / heuristic fallback classification engine."""

    @pytest.fixture
    def classifier(self) -> FeedbackClassifier:
        # Initialized without API key to ensure offline heuristic engine is used
        return FeedbackClassifier(api_key=None)

    def test_classifier_identifies_offline_status(self, classifier: FeedbackClassifier):
        assert classifier.is_llm_available() is False

    @pytest.mark.parametrize(
        "text,expected_topic",
        [
            ("We were charged twice on our credit card invoice.", "Billing"),
            ("The annual subscription price is too expensive for startups.", "Pricing"),
            ("The application crashes and memory leak hangs the system.", "Performance"),
            ("Customer support rep took 4 days to answer my ticket.", "Customer Support"),
            ("The dark mode interface and navigation layout is sleek.", "UI/UX"),
            ("We really need native GitHub integration and automation.", "Product Features"),
            ("Random unrelated comment with no keywords.", "Other"),
        ],
    )
    def test_heuristic_topic_classification(self, classifier: FeedbackClassifier, text: str, expected_topic: str):
        res = classifier.classify_single_heuristic(text, rating=3)
        assert res["Topic"] == expected_topic

    def test_heuristic_topic_classification_reports_no_longer_collides_with_rep(self, classifier: FeedbackClassifier):
        """VERIFIED FIX: 'rep' keyword uses word boundaries, so 'sprint reports' is correctly classified as Product Features."""
        res = classifier.classify_single_heuristic("We need sprint reports", rating=3)
        assert res["Topic"] == "Product Features"

    @pytest.mark.parametrize(
        "text,rating,expected_sentiment",
        [
            ("Absolutely fantastic tool, love the smooth experience!", 5, "Positive"),
            ("Terrible, broken, slow and painful experience.", 1, "Negative"),
            ("The tool works as expected for basic task tracking.", 3, "Neutral"),
            ("Superb features but occasionally expensive.", 4, "Neutral"),  # Rating 4 with mixed negative word evaluates to Neutral by design
            ("Superb features but occasionally expensive.", 5, "Positive"),  # Rating 5 with mixed negative word evaluates to Positive
        ],
    )
    def test_heuristic_sentiment_classification(
        self, classifier: FeedbackClassifier, text: str, rating: int, expected_sentiment: str
    ):
        res = classifier.classify_single_heuristic(text, rating)
        assert res["Sentiment"] == expected_sentiment

    @pytest.mark.parametrize(
        "text,rating,expected_urgency",
        [
            ("System crashed and we experienced data loss!", 1, "Critical"),
            ("Charged twice on our Stripe subscription account.", 1, "Critical"),
            ("Buggy interface and ticket unresolved for 6 days.", 2, "High"),
            ("Could be better, contrast is a bit confusing.", 3, "Medium"),
            ("Great application, nothing urgent.", 5, "Low"),
        ],
    )
    def test_heuristic_urgency_classification(
        self, classifier: FeedbackClassifier, text: str, rating: int, expected_urgency: str
    ):
        res = classifier.classify_single_heuristic(text, rating)
        assert res["Urgency"] == expected_urgency

    def test_classify_feedback_dataframe(self, classifier: FeedbackClassifier, sample_cleaned_data: pd.DataFrame):
        df_classified = classifier.classify_feedback(sample_cleaned_data, show_progress=False)

        assert len(df_classified) == len(sample_cleaned_data)
        assert "Sentiment" in df_classified.columns
        assert "Topic" in df_classified.columns
        assert "Urgency" in df_classified.columns

        # Verify classifications conform to allowed enums
        assert validate_classified_data(df_classified) is True


class TestFeedbackClassifierLLM:
    """Tests for LLM-based classification with mocked OpenAI API."""

    def test_classify_single_llm_success(self, mock_openai_response: MagicMock):
        with patch("openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_openai_response
            mock_openai_cls.return_value = mock_client

            classifier = FeedbackClassifier(api_key="sk-test-valid-key-12345")
            assert classifier.is_llm_available() is True

            res = classifier.classify_single_llm("Server crashed during sprint planning", rating=1)
            assert res["Sentiment"] == "Negative"
            assert res["Topic"] == "Performance"
            assert res["Urgency"] == "Critical"

    def test_classify_single_llm_fallback_on_json_parse_error(self):
        with patch("openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_resp = MagicMock()
            mock_resp.choices = [MagicMock(message=MagicMock(content="Invalid Non-JSON String"))]
            mock_client.chat.completions.create.return_value = mock_resp
            mock_openai_cls.return_value = mock_client

            classifier = FeedbackClassifier(api_key="sk-test-valid-key-12345")
            res = classifier.classify_single_llm("Server crashed and slow performance", rating=1)

            # Should fall back cleanly to heuristic
            assert res["Sentiment"] in VALID_SENTIMENTS
            assert res["Topic"] in VALID_TOPICS
            assert res["Urgency"] in VALID_URGENCIES

    def test_classify_single_llm_fallback_on_api_exception(self):
        with patch("openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = TimeoutError("OpenAI API timed out")
            mock_openai_cls.return_value = mock_client

            classifier = FeedbackClassifier(api_key="sk-test-valid-key-12345")
            res = classifier.classify_single_llm("Customer support ticket unanswered", rating=2)

            assert res["Sentiment"] == "Negative"
            assert res["Topic"] == "Customer Support"

    def test_validate_and_normalize_handles_invalid_enums(self):
        classifier = FeedbackClassifier(api_key=None)
        malformed_output = {
            "Sentiment": "VeryUnhappy",  # invalid
            "Topic": "Speed",            # variant mapping to Performance
            "Urgency": "UltraCritical",  # invalid
        }
        normalized = classifier._validate_and_normalize(malformed_output, text="Too slow", rating=1)
        assert normalized["Sentiment"] == "Negative"  # mapped from rating <= 2
        assert normalized["Topic"] == "Performance"   # mapped from variant
        assert normalized["Urgency"] == "High"        # mapped from rating <= 2


class TestValidateClassifiedData:
    """Tests for validate_classified_data function."""

    def test_validate_valid_classified_df(self, sample_classified_data: pd.DataFrame):
        assert validate_classified_data(sample_classified_data) is True

    def test_validate_missing_classification_columns_raises_error(self):
        df_incomplete = pd.DataFrame({"Sentiment": ["Positive"], "Topic": ["Pricing"]})
        with pytest.raises(ValueError, match="Missing required classification column: 'Urgency'"):
            validate_classified_data(df_incomplete)

    def test_validate_invalid_sentiment_raises_error(self, sample_classified_data: pd.DataFrame):
        df_bad = sample_classified_data.copy()
        df_bad.loc[0, "Sentiment"] = "Ecstatic"
        with pytest.raises(ValueError, match="Invalid Sentiment values detected"):
            validate_classified_data(df_bad)

    def test_validate_invalid_topic_raises_error(self, sample_classified_data: pd.DataFrame):
        df_bad = sample_classified_data.copy()
        df_bad.loc[0, "Topic"] = "Hardware"
        with pytest.raises(ValueError, match="Invalid Topic values detected"):
            validate_classified_data(df_bad)

    def test_validate_invalid_urgency_raises_error(self, sample_classified_data: pd.DataFrame):
        df_bad = sample_classified_data.copy()
        df_bad.loc[0, "Urgency"] = "Immediate"
        with pytest.raises(ValueError, match="Invalid Urgency values detected"):
            validate_classified_data(df_bad)
