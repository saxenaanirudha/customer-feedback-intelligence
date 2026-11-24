"""Performance, memory, and scalability benchmark test suite."""

import time
import pandas as pd
import pytest

from src import executive_insights, insights, preprocessing, priority


class TestPerformanceAndScalability:
    """Evaluates throughput, memory consumption, and caching performance."""

    @pytest.fixture
    def large_synthetic_feedback(self) -> pd.DataFrame:
        """Generates 1,000 synthetic feedback records for performance testing."""
        records = []
        customer_types = ["Standard", "Premium", "Enterprise"]
        topics = ["Billing", "Pricing", "Performance", "Product Features", "Customer Support"]
        urgencies = ["Low", "Medium", "High", "Critical"]
        sentiments = ["Positive", "Neutral", "Negative"]

        for i in range(1000):
            records.append({
                "FeedbackID": f"F_PERF_{i:04d}",
                "Text": f"Synthetic customer review #{i} regarding application stability and pricing tier options.",
                "Rating": (i % 5) + 1,
                "Date": f"2026-{(i % 9) + 1:02d}-15",
                "CustomerType": customer_types[i % 3],
                "Sentiment": sentiments[i % 3],
                "Topic": topics[i % 5],
                "Urgency": urgencies[i % 4],
            })
        return pd.DataFrame(records)

    def test_performance_preprocessing_throughput(self, large_synthetic_feedback: pd.DataFrame):
        """Benchmark clean_data throughput on 1,000 records."""
        start_time = time.perf_counter()
        cleaned = preprocessing.clean_data(large_synthetic_feedback)
        elapsed = time.perf_counter() - start_time

        assert len(cleaned) == 1000
        # Processing 1,000 rows in memory should take under 0.5 seconds
        assert elapsed < 0.5, f"Preprocessing took too long: {elapsed:.3f}s"

    def test_performance_priority_scoring_throughput(self, large_synthetic_feedback: pd.DataFrame):
        """Benchmark add_priority_columns throughput on 1,000 records."""
        start_time = time.perf_counter()
        prioritized = priority.add_priority_columns(large_synthetic_feedback)
        elapsed = time.perf_counter() - start_time

        assert len(prioritized) == 1000
        # Scoring 1,000 rows should take under 0.5 seconds
        assert elapsed < 0.5, f"Priority scoring took too long: {elapsed:.3f}s"

    def test_performance_insights_kpi_latency(self, large_synthetic_feedback: pd.DataFrame):
        """Benchmark insights calculation on 1,000 records."""
        prioritized = priority.add_priority_columns(large_synthetic_feedback)

        start_time = time.perf_counter()
        kpis = insights.get_overall_kpis(prioritized)
        trends = insights.get_feedback_trends(prioritized)
        pain_points = insights.get_top_pain_points(prioritized)
        elapsed = time.perf_counter() - start_time

        assert kpis["total_feedback"] == 1000
        assert not trends.empty
        # All analytics aggregations should take under 0.25 seconds
        assert elapsed < 0.25, f"Insights calculations took too long: {elapsed:.3f}s"

    def test_performance_executive_insights_caching_speedup(
        self, large_synthetic_feedback: pd.DataFrame, monkeypatch
    ):
        """Benchmark cache hit vs cache miss latency in executive insights."""
        monkeypatch.setenv("OPENAI_API_KEY", "")
        prioritized = priority.add_priority_columns(large_synthetic_feedback)

        # Cache miss (cold run)
        t0 = time.perf_counter()
        resp1, is_cached1, _ = executive_insights.generate_executive_insights(
            prioritized, force_refresh=True
        )
        cold_time = time.perf_counter() - t0
        assert is_cached1 is False

        # Cache hit (warm run)
        t1 = time.perf_counter()
        resp2, is_cached2, _ = executive_insights.generate_executive_insights(
            prioritized, force_refresh=False
        )
        warm_time = time.perf_counter() - t1
        assert is_cached2 is True

        # Cache hit should be significantly faster than cold generation
        assert warm_time < cold_time or warm_time < 0.05
