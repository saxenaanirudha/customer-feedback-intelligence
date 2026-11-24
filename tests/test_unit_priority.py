"""Unit tests for src/priority.py module."""

from pathlib import Path
import pandas as pd
import pytest

from src.priority import (
    CUSTOMER_TYPE_POINTS,
    RATING_POINTS,
    SENTIMENT_POINTS,
    URGENCY_POINTS,
    add_priority_columns,
    assign_priority_level,
    calculate_priority_score,
    get_priority_reason,
    validate_priority_inputs,
)


class TestCalculatePriorityScore:
    """Tests for calculate_priority_score formula and point weightings."""

    def test_maximum_possible_score_equals_100(self):
        # Critical (50) + Enterprise (25) + Negative (15) + Rating 1 (10) = 100
        score = calculate_priority_score(
            urgency="Critical", customer_type="Enterprise", sentiment="Negative", rating=1
        )
        assert score == 100

    def test_minimum_possible_score_equals_18(self):
        # Low (10) + Standard (8) + Positive (0) + Rating 5 (0) = 18
        score = calculate_priority_score(
            urgency="Low", customer_type="Standard", sentiment="Positive", rating=5
        )
        assert score == 18

    def test_customer_tier_points_differentiation(self):
        s_score = calculate_priority_score("High", "Standard", "Negative", 3)
        p_score = calculate_priority_score("High", "Premium", "Negative", 3)
        e_score = calculate_priority_score("High", "Enterprise", "Negative", 3)

        assert p_score - s_score == CUSTOMER_TYPE_POINTS["Premium"] - CUSTOMER_TYPE_POINTS["Standard"]
        assert e_score - p_score == CUSTOMER_TYPE_POINTS["Enterprise"] - CUSTOMER_TYPE_POINTS["Premium"]

    def test_urgency_points_differentiation(self):
        low_score = calculate_priority_score("Low", "Standard", "Neutral", 3)
        med_score = calculate_priority_score("Medium", "Standard", "Neutral", 3)
        high_score = calculate_priority_score("High", "Standard", "Neutral", 3)
        crit_score = calculate_priority_score("Critical", "Standard", "Neutral", 3)

        assert crit_score > high_score > med_score > low_score

    def test_score_boundary_clamping(self):
        # Even with extreme inputs, score must stay within 0-100
        score = calculate_priority_score("Critical", "Enterprise", "Negative", 1)
        assert 0 <= score <= 100


class TestAssignPriorityLevel:
    """Tests for business realism guardrails and PriorityLevel assignment."""

    def test_guardrail_1_low_urgency_positive_is_always_low_priority(self):
        level = assign_priority_level(score=45, urgency="Low", sentiment="Positive", customer_type="Enterprise", rating=5)
        assert level == "Low Priority"

    def test_guardrail_1_low_urgency_never_exceeds_medium_priority(self):
        level = assign_priority_level(score=75, urgency="Low", sentiment="Negative", customer_type="Enterprise", rating=1)
        assert level in ["Low Priority", "Medium Priority"]
        assert level != "High Priority"
        assert level != "Critical Priority"

    def test_guardrail_2_positive_sentiment_cannot_exceed_low_priority_unless_high_urgency(self):
        level_med = assign_priority_level(score=50, urgency="Medium", sentiment="Positive", customer_type="Enterprise", rating=5)
        assert level_med == "Low Priority"

        level_high = assign_priority_level(score=65, urgency="High", sentiment="Positive", customer_type="Enterprise", rating=4)
        assert level_high == "Medium Priority"

    def test_guardrail_3_critical_urgency_with_enterprise_tier_is_critical_priority(self):
        level = assign_priority_level(score=80, urgency="Critical", sentiment="Negative", customer_type="Enterprise", rating=2)
        assert level == "Critical Priority"

    def test_critical_urgency_with_standard_tier_and_high_score_is_critical_priority(self):
        # Standard tier + score >= 85
        level = assign_priority_level(score=87, urgency="Critical", sentiment="Negative", customer_type="Standard", rating=1)
        assert level == "Critical Priority"

    def test_high_priority_assignment(self):
        level = assign_priority_level(score=70, urgency="High", sentiment="Negative", customer_type="Standard", rating=2)
        assert level == "High Priority"

    def test_medium_priority_assignment(self):
        level = assign_priority_level(score=45, urgency="Medium", sentiment="Neutral", customer_type="Standard", rating=3)
        assert level == "Medium Priority"

    def test_low_priority_assignment(self):
        level = assign_priority_level(score=25, urgency="Low", sentiment="Neutral", customer_type="Standard", rating=4)
        assert level == "Low Priority"


class TestPriorityReason:
    """Tests for deterministic PriorityReason generation."""

    def test_reason_for_critical_priority(self):
        reason = get_priority_reason("Critical", "Enterprise", "Negative", 1, "Critical Priority")
        assert "Critical urgency issue" in reason
        assert "Enterprise customer" in reason
        assert "negative sentiment" in reason

    def test_reason_for_high_priority(self):
        reason = get_priority_reason("High", "Premium", "Negative", 2, "High Priority")
        assert "High urgency" in reason
        assert "Premium customer" in reason
        assert "timely intervention" in reason

    def test_reason_for_low_priority_positive(self):
        reason = get_priority_reason("Low", "Standard", "Positive", 5, "Low Priority")
        assert "Positive customer feedback" in reason
        assert "Standard customer" in reason


class TestValidatePriorityInputs:
    """Tests for validate_priority_inputs and logging."""

    def test_validate_priority_inputs_clean_dataset(self, sample_classified_data: pd.DataFrame, temp_dir: Path):
        log_file = temp_dir / "priority_errors.log"
        errors = validate_priority_inputs(sample_classified_data, error_log_path=log_file)
        assert len(errors) == 0
        assert log_file.exists()
        assert "0 Errors Found" in log_file.read_text(encoding="utf-8")

    def test_validate_priority_inputs_detects_and_logs_anomalies(self, temp_dir: Path):
        df_invalid = pd.DataFrame([{
            "FeedbackID": "BAD_1",
            "CustomerType": "UnknownTier",
            "Urgency": "Urgent",  # invalid
            "Sentiment": "Happy",  # invalid
            "Rating": 99,         # invalid
        }])
        log_file = temp_dir / "priority_errors.log"
        errors = validate_priority_inputs(df_invalid, error_log_path=log_file)
        assert len(errors) == 4
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "Total Errors: 4" in content


class TestPriorityDefectReproductions:
    """Defect verification tests confirming fixes in src/priority.py."""

    def test_fix_verification_add_priority_columns_with_none_error_log_path(self):
        """VERIFIED FIX (DEF-01):

        When `error_log_path=None` (the default) and validation anomalies exist,
        add_priority_columns logs to memory and completes cleanly without AttributeError.
        """
        df_invalid = pd.DataFrame([{
            "FeedbackID": "BAD_1",
            "CustomerType": "InvalidTier",
            "Urgency": "UltraHigh",
            "Sentiment": "Angry",
            "Rating": 10,
        }])

        enriched = add_priority_columns(df_invalid, error_log_path=None)
        assert isinstance(enriched, pd.DataFrame)
        assert "PriorityScore" in enriched.columns

    def test_fix_verification_calculate_priority_score_with_float_rating(self):
        """VERIFIED FIX (DEF-02):

        In `calculate_priority_score()`, float rating 2.0 produces the exact same score (70)
        as integer rating 2, resolving the float rating distortion bug.
        """
        score_int = calculate_priority_score("High", "Standard", "Negative", 2)
        score_float = calculate_priority_score("High", "Standard", "Negative", 2.0)

        assert score_int == 70
        assert score_float == 70
        assert score_float == score_int
