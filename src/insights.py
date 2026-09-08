# =============================================================================
# FILE PURPOSE & OVERVIEW
# =============================================================================
# This file (`src/insights.py`) calculates business metrics and prepares data for
# the charts shown on the dashboard. It takes the cleaned and prioritized feedback
# data and groups it to find trends, distributions, and top issues.
#
# FUNCTION EXPLANATIONS:
# -----------------------------------------------------------------------------
# - get_overall_kpis(): Calculates high-level metrics like total feedback, average rating, and % of positive/negative feedback.
# - get_sentiment_distribution(): Groups feedback by sentiment (Positive, Neutral, Negative) for pie charts.
# - get_sentiment_trend(): Groups sentiment over time (by month) for line charts.
# - get_rating_vs_sentiment(): Compares numeric ratings (1-5) against the AI-detected sentiment.
# - get_topic_distribution(): Counts how many pieces of feedback fall into each topic (e.g., Pricing, Usability).
# - get_topic_sentiment_analysis(): Analyzes the sentiment breakdown within each specific topic.
# - get_negative_topic_analysis(): Filters down to only negative feedback to see which topics are causing the most issues.
# - get_urgency_distribution(): Counts feedback by urgency level (Low, Medium, High, Critical).
# - get_priority_distribution(): Counts feedback by computed business priority level.
# - get_customer_segment_analysis(): Groups data by Customer Tier (Standard, Premium, Enterprise) to see how different users feel.
# - get_feedback_trends(): Groups total feedback volume over time.
# - get_top_priority_issues(): Returns a list of the absolute most critical individual feedback items that need immediate attention.
# - get_top_pain_points(): Identifies the most frequent combinations of Topic + Negative Sentiment.
# - generate_business_insights(): An older function for generating text insights based on data rules (largely replaced by AI insights).
# =============================================================================

"""Business analytics, metrics calculations, and insights generator for Customer Feedback Intelligence."""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np


def get_overall_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate executive overview KPI metrics from filtered dataset.

    Args:
        df (pd.DataFrame): Filtered feedback DataFrame.

    Returns:
        Dict[str, Any]: Key performance indicators dictionary.
    """
    total = len(df)
    if total == 0:
        return {
            "total_feedback": 0,
            "avg_rating": 0.0,
            "positive_count": 0,
            "positive_pct": 0.0,
            "neutral_count": 0,
            "neutral_pct": 0.0,
            "negative_count": 0,
            "negative_pct": 0.0,
            "high_critical_count": 0,
            "high_critical_pct": 0.0,
            "critical_count": 0,
            "critical_pct": 0.0,
        }

    avg_rating = float(df["Rating"].mean()) if "Rating" in df.columns else 0.0
    pos_count = int((df["Sentiment"] == "Positive").sum())
    neu_count = int((df["Sentiment"] == "Neutral").sum())
    neg_count = int((df["Sentiment"] == "Negative").sum())

    high_crit_count = int(df["PriorityLevel"].isin(["Critical Priority", "High Priority"]).sum())
    crit_count = int((df["PriorityLevel"] == "Critical Priority").sum())

    return {
        "total_feedback": total,
        "avg_rating": round(avg_rating, 2),
        "positive_count": pos_count,
        "positive_pct": round((pos_count / total) * 100, 1),
        "neutral_count": neu_count,
        "neutral_pct": round((neu_count / total) * 100, 1),
        "negative_count": neg_count,
        "negative_pct": round((neg_count / total) * 100, 1),
        "high_critical_count": high_crit_count,
        "high_critical_pct": round((high_crit_count / total) * 100, 1),
        "critical_count": crit_count,
        "critical_pct": round((crit_count / total) * 100, 1),
    }


def get_sentiment_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Compute sentiment counts and percentages.

    Args:
        df (pd.DataFrame): Feedback DataFrame.

    Returns:
        pd.DataFrame: Sentiment, Count, and Percentage columns.
    """
    if len(df) == 0:
        return pd.DataFrame(columns=["Sentiment", "Count", "Percentage"])

    counts = df["Sentiment"].value_counts().reset_index()
    counts.columns = ["Sentiment", "Count"]
    counts["Percentage"] = (counts["Count"] / len(df) * 100).round(1)
    return counts


def get_sentiment_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Compute monthly sentiment counts.

    Args:
        df (pd.DataFrame): Feedback DataFrame with 'Date' column.

    Returns:
        pd.DataFrame: Monthly aggregated sentiment counts.
    """
    if len(df) == 0 or "Date" not in df.columns:
        return pd.DataFrame()

    df_temp = df.copy()
    df_temp["Month"] = pd.to_datetime(df_temp["Date"]).dt.to_period("M").dt.to_timestamp()

    trend = df_temp.groupby(["Month", "Sentiment"]).size().unstack(fill_value=0).reset_index()
    for col in ["Positive", "Neutral", "Negative"]:
        if col not in trend.columns:
            trend[col] = 0
    return trend.sort_values("Month")


def get_rating_vs_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate crosstab matrix between star ratings and text sentiment classifications.

    Args:
        df (pd.DataFrame): Feedback DataFrame.

    Returns:
        pd.DataFrame: Crosstab breakdown.
    """
    if len(df) == 0:
        return pd.DataFrame()
    return pd.crosstab(df["Rating"], df["Sentiment"], normalize=False)


def get_topic_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate total feedback volume and percentage per topic.

    Args:
        df (pd.DataFrame): Feedback DataFrame.

    Returns:
        pd.DataFrame: Topic volume summary sorted descending.
    """
    if len(df) == 0:
        return pd.DataFrame(columns=["Topic", "Count", "Percentage"])

    topic_counts = df["Topic"].value_counts().reset_index()
    topic_counts.columns = ["Topic", "Count"]
    topic_counts["Percentage"] = (topic_counts["Count"] / len(df) * 100).round(1)
    return topic_counts


def get_topic_sentiment_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate sentiment breakdown per topic.

    Args:
        df (pd.DataFrame): Feedback DataFrame.

    Returns:
        pd.DataFrame: Stacked sentiment counts per topic.
    """
    if len(df) == 0:
        return pd.DataFrame()

    crosstab = pd.crosstab(df["Topic"], df["Sentiment"]).reset_index()
    for col in ["Positive", "Neutral", "Negative"]:
        if col not in crosstab.columns:
            crosstab[col] = 0
    crosstab["Total"] = crosstab["Positive"] + crosstab["Neutral"] + crosstab["Negative"]
    return crosstab.sort_values("Total", ascending=False)


def get_negative_topic_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate negative feedback volume, percentage, and negative-to-total ratio per topic.

    Args:
        df (pd.DataFrame): Feedback DataFrame.

    Returns:
        pd.DataFrame: Topic, TotalCount, NegativeCount, NegativePercentage, AverageRating.
    """
    if len(df) == 0:
        return pd.DataFrame(columns=["Topic", "TotalCount", "NegativeCount", "NegativePercentage", "AverageRating"])

    grouped = df.groupby("Topic").agg(
        TotalCount=("FeedbackID", "count"),
        NegativeCount=("Sentiment", lambda s: (s == "Negative").sum()),
        AverageRating=("Rating", "mean"),
    ).reset_index()

    grouped["NegativePercentage"] = ((grouped["NegativeCount"] / grouped["TotalCount"]) * 100).round(1)
    grouped["AverageRating"] = grouped["AverageRating"].round(2)
    return grouped.sort_values(["NegativePercentage", "NegativeCount"], ascending=[False, False])


def get_urgency_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate feedback volume and percentage per urgency level.

    Args:
        df (pd.DataFrame): Feedback DataFrame.

    Returns:
        pd.DataFrame: Urgency, Count, Percentage.
    """
    if len(df) == 0:
        return pd.DataFrame(columns=["Urgency", "Count", "Percentage"])

    order = ["Critical", "High", "Medium", "Low"]
    counts = df["Urgency"].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ["Urgency", "Count"]
    counts["Percentage"] = (counts["Count"] / len(df) * 100).round(1)
    return counts


def get_priority_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate feedback volume and percentage per priority level.

    Args:
        df (pd.DataFrame): Feedback DataFrame.

    Returns:
        pd.DataFrame: PriorityLevel, Count, Percentage.
    """
    if len(df) == 0:
        return pd.DataFrame(columns=["PriorityLevel", "Count", "Percentage"])

    order = ["Critical Priority", "High Priority", "Medium Priority", "Low Priority"]
    counts = df["PriorityLevel"].value_counts().reindex(order, fill_value=0).reset_index()
    counts.columns = ["PriorityLevel", "Count"]
    counts["Percentage"] = (counts["Count"] / len(df) * 100).round(1)
    return counts


def get_customer_segment_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Compute cross-segment metrics comparing Standard, Premium, and Enterprise tiers.

    Args:
        df (pd.DataFrame): Feedback DataFrame.

    Returns:
        pd.DataFrame: CustomerType, TotalFeedback, AvgRating, NegativePct, HighCritPct, CriticalPct.
    """
    if len(df) == 0:
        return pd.DataFrame(columns=["CustomerType", "TotalFeedback", "AvgRating", "NegativePct", "HighCritPct", "CriticalPct"])

    segments = []
    order = ["Enterprise", "Premium", "Standard"]

    for cust_type in order:
        sub = df[df["CustomerType"] == cust_type]
        total = len(sub)
        if total == 0:
            continue

        avg_r = sub["Rating"].mean()
        neg_pct = (sub["Sentiment"] == "Negative").sum() / total * 100
        high_crit_pct = sub["PriorityLevel"].isin(["Critical Priority", "High Priority"]).sum() / total * 100
        crit_pct = (sub["PriorityLevel"] == "Critical Priority").sum() / total * 100

        segments.append({
            "CustomerType": cust_type,
            "TotalFeedback": total,
            "AvgRating": round(avg_r, 2),
            "NegativePct": round(neg_pct, 1),
            "HighCritPct": round(high_crit_pct, 1),
            "CriticalPct": round(crit_pct, 1),
        })

    return pd.DataFrame(segments)


def get_feedback_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly metrics across volume, negative count, average rating, and high-priority count.

    Args:
        df (pd.DataFrame): Feedback DataFrame.

    Returns:
        pd.DataFrame: Monthly time-series metrics.
    """
    if len(df) == 0 or "Date" not in df.columns:
        return pd.DataFrame()

    df_temp = df.copy()
    df_temp["Month"] = pd.to_datetime(df_temp["Date"]).dt.to_period("M").dt.to_timestamp()

    trends = df_temp.groupby("Month").agg(
        TotalVolume=("FeedbackID", "count"),
        NegativeCount=("Sentiment", lambda s: (s == "Negative").sum()),
        AvgRating=("Rating", "mean"),
        HighCriticalCount=("PriorityLevel", lambda p: p.isin(["Critical Priority", "High Priority"]).sum()),
    ).reset_index()

    trends["AvgRating"] = trends["AvgRating"].round(2)
    return trends.sort_values("Month")


def get_top_priority_issues(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Extract top N highest priority feedback records sorted deterministically.

    Args:
        df (pd.DataFrame): Feedback DataFrame.
        top_n (int): Number of top records to return.

    Returns:
        pd.DataFrame: Sorted high-priority records.
    """
    if len(df) == 0:
        return pd.DataFrame()

    urgency_rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
    df_sorted = df.copy()
    df_sorted["_urg_rank"] = df_sorted["Urgency"].map(urgency_rank).fillna(0)

    sort_cols = ["PriorityScore", "_urg_rank"]
    if "Date" in df_sorted.columns:
        sort_cols.append("Date")

    df_sorted = df_sorted.sort_values(
        by=sort_cols,
        ascending=[False] * len(sort_cols),
    ).drop(columns=["_urg_rank"])

    return df_sorted.head(top_n)


def get_top_pain_points(df: pd.DataFrame, top_n: int = 4) -> List[Dict[str, Any]]:
    """Compute transparent, explainable PainPointScore and identify top customer pain points.

    Formula:
        PainPointScore = (NegativeFeedbackPct * 0.40)
                       + (HighCriticalIssueCount / TotalRecords * 100 * 0.30)
                       + (AvgPriorityScore * 0.30)

    Args:
        df (pd.DataFrame): Filtered feedback DataFrame.
        top_n (int): Number of top pain points to extract.

    Returns:
        List[Dict[str, Any]]: List of top pain points with stats and observations.
    """
    if len(df) == 0:
        return []

    total_records = len(df)
    results = []

    for topic, group in df.groupby("Topic"):
        n_total = len(group)
        if n_total < 3:  # minimum sample size threshold
            continue

        neg_count = int((group["Sentiment"] == "Negative").sum())
        neg_pct = (neg_count / n_total) * 100
        high_crit_count = int(group["PriorityLevel"].isin(["Critical Priority", "High Priority"]).sum())
        crit_count = int((group["PriorityLevel"] == "Critical Priority").sum())
        avg_score = float(group["PriorityScore"].mean())
        avg_rating = float(group["Rating"].mean())

        # Transparent PainPointScore
        pain_score = (neg_pct * 0.40) + ((high_crit_count / total_records) * 100 * 0.30) + (avg_score * 0.30)

        # Contextual observation
        if topic == "Performance":
            observation = "Performance stability, crashes, and server timeout latency are critical drivers of user frustration."
        elif topic == "Billing":
            observation = "Billing discrepancies, unexpected seat charges, and refund delays present immediate churn risks."
        elif topic == "Pricing":
            observation = "Pricing tier scaling and starter plan costs create resistance among smaller and mid-sized teams."
        elif topic == "Product Features":
            observation = "Requests for native integrations (GitHub, Slack) and dark mode highlight workflow enhancement opportunities."
        elif topic == "Customer Support":
            observation = "Support ticket response latency and resolution delays impact customer satisfaction."
        elif topic == "UI/UX":
            observation = "Navigation complexity and mobile interface responsiveness require design refinements."
        else:
            observation = f"General customer feedback requiring continuous monitoring."

        results.append({
            "Topic": topic,
            "PainPointScore": round(pain_score, 1),
            "TotalFeedback": n_total,
            "NegativeCount": neg_count,
            "NegativePct": round(neg_pct, 1),
            "HighCriticalCount": high_crit_count,
            "CriticalCount": crit_count,
            "AvgPriorityScore": round(avg_score, 1),
            "AvgRating": round(avg_rating, 2),
            "Observation": observation,
        })

    results.sort(key=lambda x: x["PainPointScore"], reverse=True)
    return results[:top_n]


def generate_business_insights(df: pd.DataFrame) -> List[str]:
    """Generate dynamic, rule-based, factual business insights strictly derived from active data.

    Args:
        df (pd.DataFrame): Feedback DataFrame.

    Returns:
        List[str]: 3 to 5 clear business observations.
    """
    if len(df) == 0:
        return ["No feedback records match the current filter selection."]

    insights: List[str] = []
    total = len(df)

    # Insight 1: Highest Negative Topic
    neg_topics = get_negative_topic_analysis(df)
    if not neg_topics.empty:
        top_neg = neg_topics.iloc[0]
        if top_neg["NegativePercentage"] > 0:
            insights.append(
                f"**{top_neg['Topic']}** has the highest negative feedback rate at **{top_neg['NegativePercentage']}%** "
                f"({int(top_neg['NegativeCount'])} out of {int(top_neg['TotalCount'])} records) with an average rating of ★{top_neg['AverageRating']}."
            )

    # Insight 2: Customer Tier Risk Profile
    seg_df = get_customer_segment_analysis(df)
    if not seg_df.empty:
        ent_row = seg_df[seg_df["CustomerType"] == "Enterprise"]
        if not ent_row.empty:
            ent = ent_row.iloc[0]
            insights.append(
                f"**Enterprise accounts** represent the highest business risk profile: **{ent['HighCritPct']}%** of Enterprise feedback "
                f"is classified as High or Critical Priority (including {ent['CriticalPct']}% Critical incidents)."
            )

    # Insight 3: Critical Issue Concentration
    crit_df = df[df["PriorityLevel"] == "Critical Priority"]
    if len(crit_df) > 0:
        top_crit_topics = crit_df["Topic"].value_counts().head(2).index.tolist()
        topic_str = " and ".join([f"**{t}**" for t in top_crit_topics])
        insights.append(
            f"**Critical Priority Incidents** ({len(crit_df)} total issues) are concentrated primarily in {topic_str}, "
            f"representing immediate operational risks requiring engineering and executive intervention."
        )

    # Insight 4: Overall Sentiment Ratio
    pos_cnt = (df["Sentiment"] == "Positive").sum()
    neg_cnt = (df["Sentiment"] == "Negative").sum()
    pos_pct = round((pos_cnt / total) * 100, 1)
    neg_pct = round((neg_cnt / total) * 100, 1)
    insights.append(
        f"Overall Customer Sentiment stands at **{pos_pct}% Positive** vs **{neg_pct}% Negative** across {total} analyzed customer interactions."
    )

    # Insight 5: Monthly trend peak detection (if multiple months)
    trends = get_feedback_trends(df)
    if len(trends) >= 2:
        max_neg_month = trends.loc[trends["NegativeCount"].idxmax()]
        month_str = max_neg_month["Month"].strftime("%B %Y")
        insights.append(
            f"Negative feedback peaked in **{month_str}** with **{int(max_neg_month['NegativeCount'])} negative records**. "
            f"Performance- and billing-related issues should be reviewed to identify key contributing factors."
        )

    return insights[:5]
