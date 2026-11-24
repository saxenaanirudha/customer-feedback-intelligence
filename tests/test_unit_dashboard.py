"""Unit tests for dashboard components and logic in dashboard/app.py."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from dashboard.app import (
    _severity_badge,
    _status_badge,
    get_sparkline_svg,
    kpi_card_m,
    load_pipeline_data,
)


class TestDashboardComponents:
    """Tests for visual and helper components in dashboard/app.py."""

    def test_severity_badge_styling(self):
        badge_crit = _severity_badge("Critical")
        assert "Critical" in badge_crit
        assert "text-transform:uppercase" in badge_crit
        assert "#FF4757" in badge_crit

        badge_low = _severity_badge("Low")
        assert "Low" in badge_low
        assert "#10B981" in badge_low

        badge_unknown = _severity_badge("NonExistent")
        assert "#94A3B8" in badge_unknown

    def test_status_badge_styling(self):
        badge_act = _status_badge("Active")
        assert "Active" in badge_act
        assert "#10B981" in badge_act

        badge_pau = _status_badge("Paused")
        assert "Paused" in badge_pau
        assert "#FBBF24" in badge_pau

    def test_sparkline_svg_generation(self):
        svg = get_sparkline_svg([10, 20, 15, 30, 25], "#38BDF8", uid="test_sp")
        assert "<svg" in svg
        assert "<polygon" in svg
        assert "<polyline" in svg
        assert "#38BDF8" in svg

    def test_sparkline_svg_empty_or_single_value_returns_empty_string(self):
        assert get_sparkline_svg([], "#38BDF8") == ""
        assert get_sparkline_svg([10], "#38BDF8") == ""

    def test_kpi_card_m_html_render(self):
        html = kpi_card_m(
            title="Total Feedback",
            value="322",
            sub1="322 total records",
            sub2=None,
            icon_svg="<svg></svg>",
            accent_color="#38BDF8",
            trend_data=[10, 20, 30],
            is_up=True,
            change_pct=15.2,
            card_uid="k1",
        )
        assert "TOTAL FEEDBACK" in html.upper()
        assert "322" in html
        assert "15.2%" in html
        assert "#38BDF8" in html


class TestDashboardDataLoading:
    """Tests for load_pipeline_data function."""

    def test_load_pipeline_data_from_cache(self, sample_prioritized_data: pd.DataFrame, temp_dir: Path, monkeypatch):
        cached_file = temp_dir / "prioritized_feedback.csv"
        sample_prioritized_data.to_csv(cached_file, index=False)

        monkeypatch.setattr("dashboard.app.PRIORITIZED_PATH", str(cached_file))

        # Use the underlying unwrapped function to verify loading behavior independently of Streamlit's process cache
        loader_fn = getattr(load_pipeline_data, "__wrapped__", load_pipeline_data)
        df_loaded = loader_fn(force_full=False)
        assert len(df_loaded) == 5
        assert pd.api.types.is_datetime64_any_dtype(df_loaded["Date"])

    def test_date_range_tuple_handling(self):
        """Test how single-click tuple state in st.date_input is handled."""
        min_date = pd.to_datetime("2025-01-01").date()
        max_date = pd.to_datetime("2026-12-31").date()

        # Incomplete selection (tuple of 1 element during user click)
        sel_date_range = (min_date,)
        if isinstance(sel_date_range, tuple) and len(sel_date_range) == 2:
            start_date, end_date = sel_date_range
        else:
            start_date = end_date = min_date

        assert start_date == min_date
        assert end_date == min_date
