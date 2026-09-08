# =============================================================================
# FILE PURPOSE & OVERVIEW
# =============================================================================
# This file (`src/priority.py`) calculates a final "Business Priority Score" (0-100)
# for every piece of feedback. It uses a rules-based engine that weighs who the customer
# is (Enterprise vs Standard), the AI-detected Urgency, the Sentiment, and the Topic.
#
# FUNCTION EXPLANATIONS:
# -----------------------------------------------------------------------------
# - calculate_priority_score(): The core math function. It adds points for Enterprise tier, Critical urgency, Negative sentiment, etc., to calculate a final score out of 100.
# - assign_priority_level(): Takes the 0-100 score and assigns a bucket like "Critical Priority" (if score >= 80) or "Low Priority".
# - get_priority_reason(): Generates a human-readable sentence explaining *why* the feedback got the score it did (e.g., "Enterprise customer reported a Critical Bug").
# - validate_priority_inputs(): Checks the input data to make sure it has the Urgency, CustomerType, and Sentiment columns needed for the math.
# - add_priority_columns(): The main function that applies the above math to the entire DataFrame, adding new columns for Score, Level, and Reason.
# =============================================================================

"""Business Priority Scoring Engine for Customer Feedback Intelligence.

Computes a deterministic, explainable 0-100 PriorityScore, assigns business PriorityLevel,
generates human-readable PriorityReason, and applies realistic business guardrails.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

# Point weight mappings
URGENCY_POINTS: Dict[str, int] = {
    "Low": 10,
    "Medium": 25,
    "High": 40,
    "Critical": 50,
}

CUSTOMER_TYPE_POINTS: Dict[str, int] = {
    "Standard": 8,
    "Premium": 16,
    "Enterprise": 25,
}

SENTIMENT_POINTS: Dict[str, int] = {
    "Positive": 0,
    "Neutral": 5,
    "Negative": 15,
}

RATING_POINTS: Dict[int, int] = {
    1: 10,
    2: 7,
    3: 4,
    4: 1,
    5: 0,
}


def calculate_priority_score(
    urgency: str,
    customer_type: str,
    sentiment: str,
    rating: int,
) -> int:
    """Calculate raw weighted priority score between 0 and 100.

    Formula:
        Score = Urgency (max 50) + CustomerType (max 25) + Sentiment (max 15) + Rating (max 10)

    Args:
        urgency (str): Low, Medium, High, Critical
        customer_type (str): Standard, Premium, Enterprise
        sentiment (str): Positive, Neutral, Negative
        rating (int): 1 to 5

    Returns:
        int: Computed priority score bounded between 0 and 100.
    """
    u_pts = URGENCY_POINTS.get(urgency, 10)
    c_pts = CUSTOMER_TYPE_POINTS.get(customer_type, 8)
    s_pts = SENTIMENT_POINTS.get(sentiment, 5)
    r_pts = RATING_POINTS.get(int(rating) if str(rating).isdigit() else 3, 4)

    raw_score = u_pts + c_pts + s_pts + r_pts
    return max(0, min(100, int(round(raw_score))))


def assign_priority_level(
    score: int,
    urgency: str,
    sentiment: str,
    customer_type: str,
    rating: int,
) -> str:
    """Assign human-readable PriorityLevel with business realism guardrails.

    Guardrails:
    1. Low urgency issues can NEVER be 'High Priority' or 'Critical Priority'.
    2. Positive feedback cannot exceed 'Low Priority' (or 'Medium Priority' for High urgency).
    3. Critical Priority is reserved for Critical urgency incidents with severe impact (Score >= 85 or Enterprise).

    Args:
        score (int): Computed numerical priority score (0-100).
        urgency (str): Urgency level.
        sentiment (str): Sentiment classification.
        customer_type (str): Customer tier.
        rating (int): Numerical star rating.

    Returns:
        str: 'Low Priority', 'Medium Priority', 'High Priority', or 'Critical Priority'.
    """
    # Guardrail 1: Low Urgency
    if urgency == "Low":
        if sentiment == "Positive":
            return "Low Priority"
        return "Low Priority" if score <= 32 else "Medium Priority"

    # Guardrail 2: Positive Sentiment
    if sentiment == "Positive":
        return "Medium Priority" if urgency == "High" else "Low Priority"

    # Critical Priority: Critical urgency incidents with high business impact
    if urgency == "Critical" and (score >= 85 or customer_type == "Enterprise"):
        return "Critical Priority"

    # High Priority: High urgency negative issues or Critical Standard issues
    if score >= 60 and (urgency in ["High", "Critical"]):
        return "High Priority"

    if score >= 30:
        return "Medium Priority"

    return "Low Priority"


def get_priority_reason(
    urgency: str,
    customer_type: str,
    sentiment: str,
    rating: int,
    priority_level: str,
) -> str:
    """Generate concise, deterministic human-readable justification for the assigned priority.

    Args:
        urgency (str): Urgency level.
        customer_type (str): Customer tier.
        sentiment (str): Sentiment classification.
        rating (int): Numerical rating.
        priority_level (str): Assigned PriorityLevel.

    Returns:
        str: Concise explanatory sentence.
    """
    rating_desc = f"{rating}-star rating"

    if priority_level == "Critical Priority":
        return f"Critical urgency issue reported by an {customer_type} customer with negative sentiment ({rating_desc})."
    elif priority_level == "High Priority":
        return f"High urgency {sentiment.lower()} feedback from a {customer_type} customer requiring timely intervention."
    elif priority_level == "Medium Priority":
        if sentiment == "Negative":
            return f"Moderate impact {sentiment.lower()} feedback from a {customer_type} customer ({rating_desc})."
        elif sentiment == "Neutral":
            return f"Neutral inquiry or feature request from a {customer_type} customer."
        else:
            return f"Feature enhancement suggestion from a {customer_type} customer."
    else:  # Low Priority
        if sentiment == "Positive":
            return f"Positive customer feedback ({rating_desc}) from a {customer_type} customer."
        else:
            return f"Low urgency cosmetic or minor feedback from a {customer_type} customer."


def validate_priority_inputs(df: pd.DataFrame, error_log_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Validate DataFrame inputs for priority calculation and log any anomalies.

    Args:
        df (pd.DataFrame): DataFrame containing classification columns.
        error_log_path (Path, optional): Path to write error logs.

    Returns:
        List[Dict[str, Any]]: List of recorded validation errors.
    """
    errors: List[Dict[str, Any]] = []

    valid_urgencies = set(URGENCY_POINTS.keys())
    valid_types = set(CUSTOMER_TYPE_POINTS.keys())
    valid_sentiments = set(SENTIMENT_POINTS.keys())
    valid_ratings = set(RATING_POINTS.keys())

    for idx, row in df.iterrows():
        fid = row.get("FeedbackID", f"Row_{idx}")

        # Check Urgency
        u = row.get("Urgency")
        if u not in valid_urgencies:
            errors.append({"FeedbackID": fid, "Field": "Urgency", "Value": u, "Reason": f"Must be in {valid_urgencies}"})

        # Check CustomerType
        c = row.get("CustomerType")
        if c not in valid_types:
            errors.append({"FeedbackID": fid, "Field": "CustomerType", "Value": c, "Reason": f"Must be in {valid_types}"})

        # Check Sentiment
        s = row.get("Sentiment")
        if s not in valid_sentiments:
            errors.append({"FeedbackID": fid, "Field": "Sentiment", "Value": s, "Reason": f"Must be in {valid_sentiments}"})

        # Check Rating
        try:
            r = int(row.get("Rating"))
            if r not in valid_ratings:
                errors.append({"FeedbackID": fid, "Field": "Rating", "Value": r, "Reason": "Rating must be 1 to 5"})
        except (ValueError, TypeError):
            errors.append({"FeedbackID": fid, "Field": "Rating", "Value": row.get("Rating"), "Reason": "Non-numeric rating"})

    # Write errors to log if requested
    if error_log_path:
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        if errors:
            with open(error_log_path, "w", encoding="utf-8") as f:
                f.write(f"--- PRIORITY VALIDATION ERROR LOG (Total Errors: {len(errors)}) ---\n")
                for err in errors:
                    f.write(f"[{err['FeedbackID']}] Field '{err['Field']}' has invalid value '{err['Value']}': {err['Reason']}\n")
        else:
            # Empty / clean log
            with open(error_log_path, "w", encoding="utf-8") as f:
                f.write("--- PRIORITY VALIDATION ERROR LOG: 0 Errors Found ---\n")

    return errors


def add_priority_columns(df: pd.DataFrame, error_log_path: Optional[Path] = None) -> pd.DataFrame:
    """Enrich classified DataFrame with PriorityScore, PriorityLevel, and PriorityReason.

    Args:
        df (pd.DataFrame): Classified feedback DataFrame.
        error_log_path (Path, optional): Path to write error logs.

    Returns:
        pd.DataFrame: Enriched DataFrame with priority attributes.
    """
    errors = validate_priority_inputs(df, error_log_path=error_log_path)
    if errors:
        print(f"      [Warning] Logged {len(errors)} validation anomalies to {error_log_path.name}")

    enriched = df.copy()

    scores: List[int] = []
    levels: List[str] = []
    reasons: List[str] = []

    for _, row in enriched.iterrows():
        urgency = str(row.get("Urgency", "Low"))
        customer_type = str(row.get("CustomerType", "Standard"))
        sentiment = str(row.get("Sentiment", "Neutral"))
        try:
            rating = int(row.get("Rating", 3))
        except (ValueError, TypeError):
            rating = 3

        score = calculate_priority_score(urgency, customer_type, sentiment, rating)
        level = assign_priority_level(score, urgency, sentiment, customer_type, rating)
        reason = get_priority_reason(urgency, customer_type, sentiment, rating, level)

        scores.append(score)
        levels.append(level)
        reasons.append(reason)

    enriched["PriorityScore"] = scores
    enriched["PriorityLevel"] = levels
    enriched["PriorityReason"] = reasons

    return enriched
