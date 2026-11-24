"""Shared pytest fixtures and test configuration for Customer Feedback Intelligence."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pandas as pd
import pytest


@pytest.fixture
def sample_raw_data() -> pd.DataFrame:
    """Fixture providing valid raw feedback records."""
    return pd.DataFrame([
        {
            "FeedbackID": "F001",
            "Text": "Subscription is too expensive for small teams.",
            "Rating": 2,
            "Date": "2025-08-14",
            "CustomerType": "Standard",
        },
        {
            "FeedbackID": "F002",
            "Text": "Great value for money compared to Jira.",
            "Rating": 5,
            "Date": "2025-08-19",
            "CustomerType": "Premium",
        },
        {
            "FeedbackID": "F003",
            "Text": "The app crashed and we lost data.",
            "Rating": 1,
            "Date": "2026-02-04",
            "CustomerType": "Enterprise",
        },
        {
            "FeedbackID": "F004",
            "Text": "Dark mode interface looks stunning and modern.",
            "Rating": 4,
            "Date": "2026-02-10",
            "CustomerType": "Standard",
        },
        {
            "FeedbackID": "F005",
            "Text": "Support ticket was resolved quickly by the agent.",
            "Rating": 4,
            "Date": "2026-02-12",
            "CustomerType": "Premium",
        },
    ])


@pytest.fixture
def sample_raw_data_with_anomalies() -> pd.DataFrame:
    """Fixture providing raw feedback with known data quality anomalies."""
    return pd.DataFrame([
        {"FeedbackID": "F001", "Text": "Valid text 1", "Rating": 5, "Date": "2025-08-14", "CustomerType": "Standard"},
        {"FeedbackID": "F001", "Text": "Duplicate ID record", "Rating": 3, "Date": "2025-08-15", "CustomerType": "Standard"},
        {"FeedbackID": "F002", "Text": "   ", "Rating": 4, "Date": "2025-08-16", "CustomerType": "Premium"},
        {"FeedbackID": "F003", "Text": None, "Rating": 4, "Date": "2025-08-17", "CustomerType": "Premium"},
        {"FeedbackID": "F004", "Text": "Valid text 4", "Rating": 7, "Date": "2025-08-18", "CustomerType": "Standard"},  # invalid rating
        {"FeedbackID": "F005", "Text": "Valid text 5", "Rating": -1, "Date": "2025-08-19", "CustomerType": "Enterprise"},  # invalid rating
        {"FeedbackID": "F006", "Text": "Valid text 6", "Rating": "abc", "Date": "2025-08-20", "CustomerType": "Standard"},  # non-numeric rating
        {"FeedbackID": "F007", "Text": "Valid text 7", "Rating": 4, "Date": "invalid-date", "CustomerType": "Enterprise"},  # invalid date
        {"FeedbackID": "F008", "Text": "Valid text 8", "Rating": 3, "Date": "2025-08-22", "CustomerType": "UnknownTier"},  # invalid customer type
        {"FeedbackID": "F009", "Text": "Valid text 9", "Rating": 2, "Date": "2025-08-23", "CustomerType": "Enterprise"},
    ])


@pytest.fixture
def sample_cleaned_data() -> pd.DataFrame:
    """Fixture providing cleaned and standardized feedback DataFrame."""
    return pd.DataFrame([
        {
            "FeedbackID": "F001",
            "Text": "Subscription is too expensive for small teams.",
            "Rating": 2,
            "Date": pd.to_datetime("2025-08-14"),
            "CustomerType": "Standard",
        },
        {
            "FeedbackID": "F002",
            "Text": "Great value for money compared to Jira.",
            "Rating": 5,
            "Date": pd.to_datetime("2025-08-19"),
            "CustomerType": "Premium",
        },
        {
            "FeedbackID": "F003",
            "Text": "The app crashed and we lost data.",
            "Rating": 1,
            "Date": pd.to_datetime("2026-02-04"),
            "CustomerType": "Enterprise",
        },
    ])


@pytest.fixture
def sample_classified_data() -> pd.DataFrame:
    """Fixture providing classified feedback records."""
    return pd.DataFrame([
        {
            "FeedbackID": "F001",
            "Text": "Subscription is too expensive for small teams.",
            "Rating": 2,
            "Date": pd.to_datetime("2025-08-14"),
            "CustomerType": "Standard",
            "Sentiment": "Negative",
            "Topic": "Pricing",
            "Urgency": "High",
        },
        {
            "FeedbackID": "F002",
            "Text": "Great value for money compared to Jira.",
            "Rating": 5,
            "Date": pd.to_datetime("2025-08-19"),
            "CustomerType": "Premium",
            "Sentiment": "Positive",
            "Topic": "Pricing",
            "Urgency": "Low",
        },
        {
            "FeedbackID": "F003",
            "Text": "The app crashed and we lost data.",
            "Rating": 1,
            "Date": pd.to_datetime("2026-02-04"),
            "CustomerType": "Enterprise",
            "Sentiment": "Negative",
            "Topic": "Performance",
            "Urgency": "Critical",
        },
        {
            "FeedbackID": "F004",
            "Text": "Dark mode looks great.",
            "Rating": 4,
            "Date": pd.to_datetime("2026-02-10"),
            "CustomerType": "Standard",
            "Sentiment": "Positive",
            "Topic": "UI/UX",
            "Urgency": "Low",
        },
        {
            "FeedbackID": "F005",
            "Text": "Need help with billing invoice charges.",
            "Rating": 2,
            "Date": pd.to_datetime("2026-02-15"),
            "CustomerType": "Enterprise",
            "Sentiment": "Negative",
            "Topic": "Billing",
            "Urgency": "High",
        },
    ])


@pytest.fixture
def sample_prioritized_data() -> pd.DataFrame:
    """Fixture providing prioritized feedback records matching pipeline output format."""
    return pd.DataFrame([
        {
            "FeedbackID": "F001",
            "Text": "Subscription is too expensive for small teams.",
            "Rating": 2,
            "Date": pd.to_datetime("2025-08-14"),
            "CustomerType": "Standard",
            "Sentiment": "Negative",
            "Topic": "Pricing",
            "Urgency": "High",
            "PriorityScore": 70,
            "PriorityLevel": "High Priority",
            "PriorityReason": "High urgency negative feedback from a Standard customer requiring timely intervention.",
        },
        {
            "FeedbackID": "F002",
            "Text": "Great value for money compared to Jira.",
            "Rating": 5,
            "Date": pd.to_datetime("2025-08-19"),
            "CustomerType": "Premium",
            "Sentiment": "Positive",
            "Topic": "Pricing",
            "Urgency": "Low",
            "PriorityScore": 26,
            "PriorityLevel": "Low Priority",
            "PriorityReason": "Positive customer feedback (5-star rating) from a Premium customer.",
        },
        {
            "FeedbackID": "F003",
            "Text": "The app crashed and we lost data.",
            "Rating": 1,
            "Date": pd.to_datetime("2026-02-04"),
            "CustomerType": "Enterprise",
            "Sentiment": "Negative",
            "Topic": "Performance",
            "Urgency": "Critical",
            "PriorityScore": 100,
            "PriorityLevel": "Critical Priority",
            "PriorityReason": "Critical urgency issue reported by an Enterprise customer with negative sentiment (1-star rating).",
        },
        {
            "FeedbackID": "F004",
            "Text": "Dark mode looks great.",
            "Rating": 4,
            "Date": pd.to_datetime("2026-02-10"),
            "CustomerType": "Standard",
            "Sentiment": "Positive",
            "Topic": "UI/UX",
            "Urgency": "Low",
            "PriorityScore": 19,
            "PriorityLevel": "Low Priority",
            "PriorityReason": "Positive customer feedback (4-star rating) from a Standard customer.",
        },
        {
            "FeedbackID": "F005",
            "Text": "Need help with billing invoice charges.",
            "Rating": 2,
            "Date": pd.to_datetime("2026-02-15"),
            "CustomerType": "Enterprise",
            "Sentiment": "Negative",
            "Topic": "Billing",
            "Urgency": "High",
            "PriorityScore": 87,
            "PriorityLevel": "High Priority",
            "PriorityReason": "High urgency negative feedback from a Enterprise customer requiring timely intervention.",
        },
    ])


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Fixture providing an isolated temporary directory for test file I/O."""
    return tmp_path


@pytest.fixture
def mock_openai_response() -> MagicMock:
    """Deterministic mock for OpenAI Chat Completions API."""
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = (
        '{"Sentiment": "Negative", "Topic": "Performance", "Urgency": "Critical"}'
    )
    mock_resp.choices = [mock_choice]
    return mock_resp
