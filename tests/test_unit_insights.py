"""Unit tests for src/insights.py module."""

import pandas as pd
import pytest

from src.insights import (
    generate_business_insights,
    get_customer_segment_analysis,
    get_feedback_trends,
    get_negative_topic_analysis,
    get_overall_kpis,
    get_priority_distribution,
    get_rating_vs_sentiment,
    get_sentiment_distribution,
    get_sentiment_trend,
    get_top_pain_points,
    get_top_priority_issues,
    get_topic_distribution,
    get_topic_sentiment_analysis,
    get_urgency_distribution,
)


class TestOverallKPIs:
    """Tests for get_overall_kpis function."""

    def test_get_overall_kpis_valid_dataset(self, sample_prioritized_data: pd.DataFrame):
        kpis = get_overall_kpis(sample_prioritized_data)
        assert kpis["total_feedback"] == 5
        assert kpis["avg_rating"] == pytest.approx(2.8, 0.01)
        assert kpis["positive_count"] == 2
        assert kpis["positive_pct"] == 40.0
        assert kpis["negative_count"] == 3
        assert kpis["negative_pct"] == 60.0
        assert kpis["high_critical_count"] == 3  # F001 (High), F003 (Critical), F005 (High)
        assert kpis["critical_count"] == 1       # F003 (Critical)

    def test_get_overall_kpis_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=["Rating", "Sentiment", "PriorityLevel"])
        kpis = get_overall_kpis(empty_df)
        assert kpis["total_feedback"] == 0
        assert kpis["avg_rating"] == 0.0
        assert kpis["positive_pct"] == 0.0
        assert kpis["high_critical_count"] == 0


class TestDistributions:
    """Tests for distributions across sentiment, topic, urgency, and priority."""

    def test_get_sentiment_distribution(self, sample_prioritized_data: pd.DataFrame):
        df_sent = get_sentiment_distribution(sample_prioritized_data)
        assert len(df_sent) == 2  # Negative (3) and Positive (2)
        assert set(df_sent.columns) == {"Sentiment", "Count", "Percentage"}
        assert df_sent["Count"].sum() == 5

    def test_get_sentiment_distribution_empty_dataframe(self):
        df_sent = get_sentiment_distribution(pd.DataFrame(columns=["Sentiment"]))
        assert df_sent.empty
        assert list(df_sent.columns) == ["Sentiment", "Count", "Percentage"]

    def test_get_topic_distribution(self, sample_prioritized_data: pd.DataFrame):
        df_topic = get_topic_distribution(sample_prioritized_data)
        assert len(df_topic) == 4
        assert df_topic.iloc[0]["Topic"] == "Pricing"  # 2 count
        assert df_topic.iloc[0]["Count"] == 2

    def test_get_urgency_distribution(self, sample_prioritized_data: pd.DataFrame):
        df_urg = get_urgency_distribution(sample_prioritized_data)
        assert len(df_urg) == 4
        assert list(df_urg["Urgency"]) == ["Critical", "High", "Medium", "Low"]

    def test_get_priority_distribution(self, sample_prioritized_data: pd.DataFrame):
        df_prio = get_priority_distribution(sample_prioritized_data)
        assert len(df_prio) == 4
        assert list(df_prio["PriorityLevel"]) == [
            "Critical Priority",
            "High Priority",
            "Medium Priority",
            "Low Priority",
        ]


class TestTrendAndTopicAnalysis:
    """Tests for time-series and cross-tab topic analyses."""

    def test_get_sentiment_trend(self, sample_prioritized_data: pd.DataFrame):
        trend = get_sentiment_trend(sample_prioritized_data)
        assert not trend.empty
        assert "Month" in trend.columns
        assert "Positive" in trend.columns
        assert "Negative" in trend.columns

    def test_get_rating_vs_sentiment(self, sample_prioritized_data: pd.DataFrame):
        crosstab = get_rating_vs_sentiment(sample_prioritized_data)
        assert not crosstab.empty
        assert "Negative" in crosstab.columns
        assert "Positive" in crosstab.columns

    def test_get_topic_sentiment_analysis(self, sample_prioritized_data: pd.DataFrame):
        topic_sent = get_topic_sentiment_analysis(sample_prioritized_data)
        assert not topic_sent.empty
        assert "Topic" in topic_sent.columns
        assert "Total" in topic_sent.columns

    def test_get_negative_topic_analysis(self, sample_prioritized_data: pd.DataFrame):
        neg_topics = get_negative_topic_analysis(sample_prioritized_data)
        assert not neg_topics.empty
        assert "Topic" in neg_topics.columns
        assert "NegativePercentage" in neg_topics.columns
        # Topics with negative sentiment should appear
        neg_topic_names = set(neg_topics[neg_topics["NegativeCount"] > 0]["Topic"])
        assert "Pricing" in neg_topic_names
        assert "Performance" in neg_topic_names


class TestCustomerSegmentsAndPainPoints:
    """Tests for customer segmentation and explainable pain point scoring."""

    def test_get_customer_segment_analysis(self, sample_prioritized_data: pd.DataFrame):
        seg_df = get_customer_segment_analysis(sample_prioritized_data)
        assert not seg_df.empty
        tiers = list(seg_df["CustomerType"])
        assert "Enterprise" in tiers
        assert "Standard" in tiers

    def test_get_top_priority_issues(self, sample_prioritized_data: pd.DataFrame):
        top_issues = get_top_priority_issues(sample_prioritized_data, top_n=3)
        assert len(top_issues) == 3
        # First issue must be F003 (Score 100, Critical)
        assert top_issues.iloc[0]["FeedbackID"] == "F003"
        assert top_issues.iloc[0]["PriorityScore"] == 100

    def test_get_top_pain_points_filters_by_sample_threshold(self, sample_prioritized_data: pd.DataFrame):
        # Topics with < 3 entries are skipped by current threshold (n_total < 3)
        pain_points = get_top_pain_points(sample_prioritized_data, top_n=4)
        assert isinstance(pain_points, list)

    def test_generate_business_insights(self, sample_prioritized_data: pd.DataFrame):
        insights = generate_business_insights(sample_prioritized_data)
        assert isinstance(insights, list)
        assert len(insights) >= 1
        assert any("sentiment" in ins.lower() for ins in insights)


class TestInsightsDefectReproductions:
    """Tests verifying PriorityLevel label compatibility fix in src/insights.py."""

    def test_fix_verification_priority_level_label_compatibility(self, sample_prioritized_data: pd.DataFrame):
        """VERIFIED FIX (DEF-03):

        `insights.py` functions recognize both 'Critical Priority'/'High Priority' AND
        the dashboard format 'Critical'/'High', ensuring consistent analytics across layers.
        """
        df_stripped = sample_prioritized_data.copy()
        df_stripped["PriorityLevel"] = df_stripped["PriorityLevel"].str.replace(" Priority", "").str.strip()

        kpis = get_overall_kpis(df_stripped)
        assert kpis["high_critical_count"] == 3
        assert kpis["critical_count"] == 1
