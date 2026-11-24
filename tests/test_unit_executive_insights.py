"""Unit tests for src/executive_insights.py module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from pydantic import ValidationError

from src.executive_insights import (
    ActionItem,
    ExecutiveInsightsResponse,
    PainPointItem,
    RiskItem,
    WatchItem,
    build_executive_context,
    generate_executive_insights,
    get_context_hash,
)


class TestPydanticSchemas:
    """Tests for Pydantic schema validation and field validators."""

    def test_risk_item_valid(self):
        risk = RiskItem(
            title="Billing disputes",
            severity="High",
            evidence="65% negative billing feedback",
            business_impact="Revenue churn",
        )
        assert risk.severity == "High"

    def test_risk_item_normalizes_severity_casing_and_variants(self):
        risk = RiskItem(
            title="Crash",
            severity="critical",
            evidence="Data loss",
            business_impact="SLA breach",
        )
        assert risk.severity == "Critical"

    def test_action_item_validates_priority(self):
        action = ActionItem(
            priority="immediate",
            action="Fix memory leak",
            reason="Enterprise complaints",
            expected_impact="Stability",
        )
        assert action.priority == "Immediate"

    def test_executive_insights_response_full_schema_valid(self):
        data = {
            "executive_summary": "Overall customer satisfaction is stable.",
            "overall_customer_health": "Healthy",
            "key_risks": [
                {
                    "title": "Pricing concern",
                    "severity": "Medium",
                    "evidence": "12 tickets",
                    "business_impact": "Lower conversion",
                }
            ],
            "top_pain_points": [
                {
                    "topic": "Pricing",
                    "summary": "High price for small teams",
                    "evidence": "Multiple 1-star reviews",
                }
            ],
            "recommended_actions": [
                {
                    "priority": "Immediate",
                    "action": "Introduce starter tier",
                    "reason": "Reduce friction",
                    "expected_impact": "+15% conversions",
                }
            ],
            "executive_priorities": ["1. Starter tier", "2. Dark mode"],
            "watch_items": [{"item": "Mobile app", "reason": "Sync latency"}],
        }
        resp = ExecutiveInsightsResponse.model_validate(data)
        assert resp.overall_customer_health == "Healthy"
        assert len(resp.key_risks) == 1
        assert len(resp.recommended_actions) == 1

    def test_executive_insights_response_invalid_missing_fields_raises_error(self):
        with pytest.raises(ValidationError):
            ExecutiveInsightsResponse.model_validate({"executive_summary": "Incomplete data"})


class TestExecutiveContextBuilder:
    """Tests for build_executive_context function."""

    def test_build_executive_context_structure(self, sample_prioritized_data: pd.DataFrame):
        context = build_executive_context(sample_prioritized_data)
        assert "overall_kpis" in context
        assert "sentiment_summary" in context
        assert "top_negative_topics" in context
        assert "customer_segment_risks" in context
        assert "priority_summary" in context
        assert "representative_feedback" in context
        assert context["representative_feedback_count"] > 0

    def test_build_executive_context_empty_dataset(self):
        empty_df = pd.DataFrame(columns=["Rating", "Sentiment", "PriorityLevel", "Topic", "CustomerType"])
        context = build_executive_context(empty_df)
        assert context == {"error": "Empty dataset"}

    def test_get_context_hash_deterministic(self, sample_prioritized_data: pd.DataFrame):
        ctx1 = build_executive_context(sample_prioritized_data)
        ctx2 = build_executive_context(sample_prioritized_data)
        assert get_context_hash(ctx1) == get_context_hash(ctx2)


class TestGenerateExecutiveInsights:
    """Tests for generate_executive_insights with and without OpenAI API."""

    def test_generate_insights_empty_dataframe(self):
        empty_df = pd.DataFrame()
        resp, is_cached, err = generate_executive_insights(empty_df)
        assert resp is None
        assert is_cached is False
        assert "Cannot generate insights on an empty dataset" in err

    def test_generate_deterministic_fallback_when_no_api_key(
        self, sample_prioritized_data: pd.DataFrame, monkeypatch
    ):
        monkeypatch.setenv("OPENAI_API_KEY", "")
        resp, is_cached, err = generate_executive_insights(sample_prioritized_data, force_refresh=True)

        assert resp is not None
        assert isinstance(resp, ExecutiveInsightsResponse)
        assert is_cached is False
        assert err is None
        assert len(resp.recommended_actions) >= 1

    def test_generate_insights_serves_from_cache_on_repeat(
        self, sample_prioritized_data: pd.DataFrame, monkeypatch
    ):
        monkeypatch.setenv("OPENAI_API_KEY", "")
        # First call
        resp1, is_cached1, _ = generate_executive_insights(sample_prioritized_data, force_refresh=True)
        assert is_cached1 is False

        # Second call with identical data
        resp2, is_cached2, _ = generate_executive_insights(sample_prioritized_data, force_refresh=False)
        assert is_cached2 is True
        assert resp1.executive_summary == resp2.executive_summary

    def test_generate_insights_fallback_on_openai_error(
        self, sample_prioritized_data: pd.DataFrame, monkeypatch, temp_dir: Path
    ):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-live-key-999")
        error_log = temp_dir / "insights_err.log"

        with patch("openai.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = RuntimeError("OpenAI 500 Server Error")
            mock_openai_cls.return_value = mock_client

            resp, is_cached, err = generate_executive_insights(
                sample_prioritized_data, force_refresh=True, error_log_path=error_log
            )

            # Clean fallback to deterministic engine
            assert resp is not None
            assert isinstance(resp, ExecutiveInsightsResponse)
            assert is_cached is False
            assert "OpenAI API generation failed" in err
            assert error_log.exists()
            assert "OpenAI 500 Server Error" in error_log.read_text(encoding="utf-8")
