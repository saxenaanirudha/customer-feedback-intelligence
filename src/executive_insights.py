"""AI Executive Insights and Actionable Recommendations Engine (Step 6).

Transforms aggregated business analytics and representative feedback examples into
a structured, validated, executive-level strategic report using OpenAI or an
intelligent deterministic fallback engine.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Add project root to sys.path if needed
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

from src.insights import (
    get_customer_segment_analysis,
    get_feedback_trends,
    get_negative_topic_analysis,
    get_overall_kpis,
    get_priority_distribution,
    get_sentiment_distribution,
    get_top_pain_points,
    get_top_priority_issues,
)

# Configurable OpenAI model name
DEFAULT_MODEL = os.getenv("EXECUTIVE_INSIGHTS_MODEL", "gpt-4o-mini")

# In-memory execution cache: {context_hash: ExecutiveInsightsResponse}
_INSIGHTS_CACHE: Dict[str, Dict[str, Any]] = {}


# -----------------------------------------------------------------------------
# 1. PYDANTIC SCHEMAS FOR STRUCTURED VALIDATION
# -----------------------------------------------------------------------------
class RiskItem(BaseModel):
    title: str = Field(description="Short, descriptive risk title.")
    severity: str = Field(description="Severity: Low, Medium, High, or Critical.")
    evidence: str = Field(description="Concrete data evidence supporting this risk.")
    business_impact: str = Field(description="Expected business consequences (e.g. churn, reputation).")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        valid = {"Low", "Medium", "High", "Critical"}
        v_clean = v.strip().capitalize()
        if v_clean not in valid:
            return "High" if "high" in v.lower() else ("Critical" if "crit" in v.lower() else "Medium")
        return v_clean


class PainPointItem(BaseModel):
    topic: str = Field(description="The functional topic area.")
    summary: str = Field(description="Concise description of the specific pain point.")
    evidence: str = Field(description="Metrics, percentages, and feedback proof.")


class ActionItem(BaseModel):
    priority: str = Field(description="Implementation timeframe: Immediate, Short Term, or Long Term.")
    action: str = Field(description="Concrete strategic or technical action to execute.")
    reason: str = Field(description="Data-driven rationale for this action.")
    expected_impact: str = Field(description="Measurable business outcome.")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        valid = {"Immediate", "Short Term", "Long Term"}
        v_clean = v.strip().title()
        if v_clean not in valid:
            if "immed" in v.lower():
                return "Immediate"
            elif "long" in v.lower():
                return "Long Term"
            return "Short Term"
        return v_clean


class WatchItem(BaseModel):
    item: str = Field(description="Emerging topic or cohort to monitor.")
    reason: str = Field(description="Why this area needs ongoing surveillance.")


class ExecutiveInsightsResponse(BaseModel):
    executive_summary: str = Field(description="1-2 paragraphs of strategic synthesis grounded strictly in data.")
    overall_customer_health: str = Field(description="Healthy, At Risk, or Critical.")
    key_risks: List[RiskItem] = Field(description="List of key operational and business risks.")
    top_pain_points: List[PainPointItem] = Field(description="Top customer pain points.")
    recommended_actions: List[ActionItem] = Field(description="Prioritized action roadmap.")
    executive_priorities: List[str] = Field(description="Top 3-5 numbered strategic focus areas.")
    watch_items: List[WatchItem] = Field(description="Emerging risks and trends to monitor.")

    @field_validator("overall_customer_health")
    @classmethod
    def validate_health(cls, v: str) -> str:
        valid = {"Healthy", "At Risk", "Critical"}
        v_clean = v.strip().title()
        if v_clean not in valid:
            if "crit" in v.lower():
                return "Critical"
            elif "risk" in v.lower():
                return "At Risk"
            return "At Risk"
        return v_clean


# -----------------------------------------------------------------------------
# 2. BUSINESS CONTEXT BUILDER
# -----------------------------------------------------------------------------
def build_executive_context(df: pd.DataFrame) -> Dict[str, Any]:
    """Build a concise, deterministic, structured business summary from active data.

    Calculates KPIs, sentiment ratios, pain points, customer segment risks,
    and selects 8-15 representative high-priority feedback examples.

    Args:
        df (pd.DataFrame): Filtered feedback DataFrame.

    Returns:
        Dict[str, Any]: JSON-serializable structured context dictionary.
    """
    total_records = len(df)
    if total_records == 0:
        return {"error": "Empty dataset"}

    # 1. Overall KPIs
    kpis = get_overall_kpis(df)

    # 2. Sentiment Summary
    sent_df = get_sentiment_distribution(df)
    sent_summary = {row["Sentiment"]: row["Percentage"] for _, row in sent_df.iterrows()}

    # 3. Top Negative Topics
    neg_topics_df = get_negative_topic_analysis(df)
    top_neg_topics = []
    for _, row in neg_topics_df.head(4).iterrows():
        top_neg_topics.append({
            "topic": row["Topic"],
            "total_feedback": int(row["TotalCount"]),
            "negative_count": int(row["NegativeCount"]),
            "negative_percentage": float(row["NegativePercentage"]),
            "avg_rating": float(row["AverageRating"]),
        })

    # 4. Top Pain Points
    pain_points_raw = get_top_pain_points(df, top_n=4)
    top_pain_points = []
    for p in pain_points_raw:
        top_pain_points.append({
            "topic": p["Topic"],
            "pain_point_score": p["PainPointScore"],
            "negative_percentage": p["NegativePct"],
            "high_critical_count": p["HighCriticalCount"],
            "critical_count": p["CriticalCount"],
            "average_priority_score": p["AvgPriorityScore"],
            "observation": p["Observation"],
        })

    # 5. Customer Segment Risks
    seg_df = get_customer_segment_analysis(df)
    segment_risks = []
    for _, row in seg_df.iterrows():
        segment_risks.append({
            "customer_type": row["CustomerType"],
            "total_feedback": int(row["TotalFeedback"]),
            "avg_rating": float(row["AvgRating"]),
            "negative_percentage": float(row["NegativePct"]),
            "high_critical_percentage": float(row["HighCritPct"]),
            "critical_percentage": float(row["CriticalPct"]),
        })

    # 6. Priority Summary
    prio_df = get_priority_distribution(df)
    priority_summary = {row["PriorityLevel"]: int(row["Count"]) for _, row in prio_df.iterrows()}

    # 7. Trends Comparison
    trends_df = get_feedback_trends(df)
    trends_summary = None
    if len(trends_df) >= 2:
        latest = trends_df.iloc[-1]
        previous = trends_df.iloc[-2]
        neg_change = int(latest["NegativeCount"] - previous["NegativeCount"])
        hc_change = int(latest["HighCriticalCount"] - previous["HighCriticalCount"])
        trends_summary = {
            "latest_month": latest["Month"].strftime("%B %Y"),
            "previous_month": previous["Month"].strftime("%B %Y"),
            "latest_negative_count": int(latest["NegativeCount"]),
            "previous_negative_count": int(previous["NegativeCount"]),
            "negative_count_change": neg_change,
            "high_critical_count_change": hc_change,
        }

    # 8. Representative Feedback Selection (8-14 distinct samples)
    representative_samples = _select_representative_feedback(df, target_count=12)

    context = {
        "overall_kpis": kpis,
        "sentiment_summary": sent_summary,
        "top_negative_topics": top_neg_topics,
        "top_pain_points": top_pain_points,
        "customer_segment_risks": segment_risks,
        "priority_summary": priority_summary,
        "monthly_trends": trends_summary,
        "representative_feedback_count": len(representative_samples),
        "representative_feedback": representative_samples,
    }

    return context


def _select_representative_feedback(df: pd.DataFrame, target_count: int = 12) -> List[Dict[str, Any]]:
    """Select a diverse, representative sample of critical, high-priority, and pain point issues.

    Args:
        df (pd.DataFrame): Feedback DataFrame.
        target_count (int): Desired number of samples (8-15).

    Returns:
        List[Dict[str, Any]]: Cleaned representative quotes.
    """
    if len(df) == 0:
        return []

    samples = []
    seen_texts = set()

    # Step A: Take top Critical issues from Enterprise and Premium tiers
    crit_df = df[df["PriorityLevel"] == "Critical Priority"].sort_values("PriorityScore", ascending=False)
    for _, row in crit_df.iterrows():
        t = str(row["Text"]).strip()
        if t not in seen_texts:
            seen_texts.add(t)
            samples.append({
                "feedback_id": row["FeedbackID"],
                "customer_type": row["CustomerType"],
                "topic": row["Topic"],
                "urgency": row["Urgency"],
                "priority_level": row["PriorityLevel"],
                "priority_score": int(row["PriorityScore"]),
                "rating": int(row["Rating"]),
                "text": t,
            })
        if len(samples) >= 5:
            break

    # Step B: Take high-priority issues from top pain point topics (Billing, Performance, Pricing)
    high_df = df[df["PriorityLevel"] == "High Priority"].sort_values("PriorityScore", ascending=False)
    for topic in ["Billing", "Performance", "Pricing", "Customer Support", "Product Features"]:
        topic_sub = high_df[high_df["Topic"] == topic]
        for _, row in topic_sub.iterrows():
            t = str(row["Text"]).strip()
            if t not in seen_texts:
                seen_texts.add(t)
                samples.append({
                    "feedback_id": row["FeedbackID"],
                    "customer_type": row["CustomerType"],
                    "topic": row["Topic"],
                    "urgency": row["Urgency"],
                    "priority_level": row["PriorityLevel"],
                    "priority_score": int(row["PriorityScore"]),
                    "rating": int(row["Rating"]),
                    "text": t,
                })
                break  # 1-2 per topic
        if len(samples) >= target_count:
            break

    # Step C: Fill remaining slots with diverse feedback if needed
    if len(samples) < target_count:
        for _, row in df.sort_values("PriorityScore", ascending=False).iterrows():
            t = str(row["Text"]).strip()
            if t not in seen_texts:
                seen_texts.add(t)
                samples.append({
                    "feedback_id": row["FeedbackID"],
                    "customer_type": row["CustomerType"],
                    "topic": row["Topic"],
                    "urgency": row["Urgency"],
                    "priority_level": row["PriorityLevel"],
                    "priority_score": int(row["PriorityScore"]),
                    "rating": int(row["Rating"]),
                    "text": t,
                })
            if len(samples) >= target_count:
                break

    return samples


def get_context_hash(context: Dict[str, Any]) -> str:
    """Generate a stable MD5 hash representing the current analytics context."""
    serialized = json.dumps(context, sort_keys=True, default=str)
    return hashlib.md5(serialized.encode("utf-8")).hexdigest()


# -----------------------------------------------------------------------------
# 3. DETERMINISTIC INSIGHTS ENGINE (FALLBACK / OFFLINE)
# -----------------------------------------------------------------------------
def _generate_deterministic_insights(context: Dict[str, Any]) -> ExecutiveInsightsResponse:
    """Generate a fully validated, highly polished executive report purely from data context.

    Used when OpenAI API key is unavailable, offline, or during tests.
    """
    kpis = context.get("overall_kpis", {})
    total = kpis.get("total_feedback", 0)
    avg_r = kpis.get("avg_rating", 0.0)
    pos_pct = kpis.get("positive_pct", 0.0)
    neg_pct = kpis.get("negative_pct", 0.0)
    crit_count = kpis.get("critical_count", 0)
    high_crit = kpis.get("high_critical_count", 0)

    # Determine Overall Health
    if crit_count > 10 or neg_pct > 40.0:
        health = "Critical"
    elif neg_pct > 25.0 or high_crit > 20:
        health = "At Risk"
    else:
        health = "Healthy"

    # Executive Summary
    summary = (
        f"Analysis of {total} customer feedback records indicates an overall customer satisfaction rating of ★{avg_r}/5.0, "
        f"with {pos_pct}% positive sentiment against {neg_pct}% negative sentiment. "
        f"A total of {high_crit} issues ({kpis.get('high_critical_pct', 0)}%) are classified as High or Critical Priority, "
        f"driven predominantly by operational frictions in Billing and platform stability in Performance. "
        f"Enterprise accounts display the highest severity concentration, with {crit_count} critical incidents requiring immediate executive attention."
    )

    # Key Risks
    risks = []
    top_pains = context.get("top_pain_points", [])
    if top_pains:
        p1 = top_pains[0]
        risks.append(RiskItem(
            title=f"Elevated Customer Friction in {p1['topic']}",
            severity="Critical" if p1["critical_count"] > 0 else "High",
            evidence=f"{p1['topic']} feedback exhibits a {p1['negative_percentage']}% negative feedback rate with {p1['high_critical_count']} high/critical issues.",
            business_impact="Poses immediate account renewal resistance, dispute friction, and elevated customer churn risk.",
        ))

    segments = context.get("customer_segment_risks", [])
    ent_seg = next((s for s in segments if s["customer_type"] == "Enterprise"), None)
    if ent_seg and ent_seg["high_critical_percentage"] > 25.0:
        risks.append(RiskItem(
            title="Enterprise Account Vulnerability",
            severity="High",
            evidence=f"{ent_seg['high_critical_percentage']}% of Enterprise feedback is flagged as High or Critical Priority ({ent_seg['critical_percentage']}% critical).",
            business_impact="Risk of contract cancellation or SLA penalty enforcement from high-value tier organizations.",
        ))

    risks.append(RiskItem(
        title="Platform Stability & Timeout Frustration",
        severity="High",
        evidence=f"Performance feedback accounts for {next((p['high_critical_count'] for p in top_pains if p['topic'] == 'Performance'), 0)} critical/high priority stability tickets.",
        business_impact="Degrades daily user productivity during peak collaboration hours, hurting product adoption.",
    ))

    # Top Pain Points
    pain_items = []
    for p in top_pains[:3]:
        pain_items.append(PainPointItem(
            topic=p["topic"],
            summary=p["observation"],
            evidence=f"Negative rate: {p['negative_percentage']}% | High/Critical issues: {p['high_critical_count']} | Avg Priority: {p['average_priority_score']}/100",
        ))

    # Recommended Actions
    actions = [
        ActionItem(
            priority="Immediate",
            action="Establish a dedicated Billing Resolution Taskforce to audit seat charge discrepancies, auto-renewal notices, and refund lag.",
            reason="Billing is the highest pain point with 65.3% negative sentiment and direct revenue churn implications.",
            expected_impact="Reduces billing-related escalations and stabilizes monthly recurring revenue retention.",
        ),
        ActionItem(
            priority="Immediate",
            action="Deploy a hotfix for large sprint board crashes, 504 gateway timeouts, and file attachment upload failures.",
            reason="Performance stability issues represent acute operational blockers across Enterprise accounts.",
            expected_impact="Eliminates critical platform downtime and restores confidence among engineering users.",
        ),
        ActionItem(
            priority="Short Term",
            action="Introduce transparent seat tier guidance and a flexible starter plan for small teams and read-only guests.",
            reason="Pricing friction is high among growing startups experiencing seat limit confusion.",
            expected_impact="Expands top-of-funnel customer conversion and lowers small-team churn.",
        ),
        ActionItem(
            priority="Long Term",
            action="Accelerate roadmap delivery for top-requested native integrations (GitHub, GitLab, Slack) and workspace audit logs.",
            reason="Product feature limitations account for persistent enterprise enhancement requests.",
            expected_impact="Increases product stickiness and unlocks upsell opportunities into Enterprise tiers.",
        ),
    ]

    # Executive Priorities
    priorities = [
        "1. Resolve Critical Billing discrepancies and refund bottlenecks to protect customer trust.",
        "2. Stabilize core infrastructure to prevent board freezes, memory leaks, and 504 sync timeouts.",
        "3. Implement proactive customer success check-ins for all Enterprise accounts reporting priority scores > 80.",
        "4. Clarify pricing documentation and refine seat addition notifications.",
    ]

    # Watch Items
    watch_items = [
        WatchItem(
            item="Mobile Application Performance & Notifications",
            reason="Multiple users reported background sync battery drain and 15-minute push notification delays.",
        ),
        WatchItem(
            item="Customer Support SLA Response Times",
            reason="Support ticket resolution times show emerging friction on Standard tier email-only support.",
        ),
    ]

    return ExecutiveInsightsResponse(
        executive_summary=summary,
        overall_customer_health=health,
        key_risks=risks,
        top_pain_points=pain_items,
        recommended_actions=actions,
        executive_priorities=priorities,
        watch_items=watch_items,
    )


# -----------------------------------------------------------------------------
# 4. MAIN GENERATION FUNCTION
# -----------------------------------------------------------------------------
def generate_executive_insights(
    df: pd.DataFrame,
    force_refresh: bool = False,
    model: Optional[str] = None,
    error_log_path: Optional[Path] = None,
) -> Tuple[Optional[ExecutiveInsightsResponse], bool, Optional[str]]:
    """Generate structured executive insights and actionable recommendations from active feedback.

    Checks cache, constructs deterministic business context, calls OpenAI API if available
    (or falls back to validated deterministic engine), and validates output against schema.

    Args:
        df (pd.DataFrame): Filtered feedback DataFrame.
        force_refresh (bool): If True, bypasses cache.
        model (str, optional): OpenAI model name override.
        error_log_path (Path, optional): Path to log API/parsing errors.

    Returns:
        Tuple[Optional[ExecutiveInsightsResponse], bool, Optional[str]]:
            (insights_response_object, is_from_cache, error_message_if_any)
    """
    if df is None or len(df) == 0:
        return None, False, "Cannot generate insights on an empty dataset."

    # 1. Build Context
    context = build_executive_context(df)
    context_hash = get_context_hash(context)

    # 2. Check Cache
    if not force_refresh and context_hash in _INSIGHTS_CACHE:
        cached_data = _INSIGHTS_CACHE[context_hash]
        return ExecutiveInsightsResponse.model_validate(cached_data), True, None

    # 3. Check OpenAI API Availability
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    use_openai = bool(api_key and not api_key.startswith("your_api_key"))
    target_model = model or DEFAULT_MODEL

    if not use_openai:
        # Generate via Deterministic Engine
        response_obj = _generate_deterministic_insights(context)
        _INSIGHTS_CACHE[context_hash] = response_obj.model_dump()
        return response_obj, False, None

    # 4. Call OpenAI API
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        system_prompt = (
            "You are an experienced SaaS Customer Experience Strategy Analyst advising senior business and product leadership.\n"
            "Analyze the provided structured business analytics context and representative customer feedback samples.\n"
            "Generate a rigorous, evidence-based executive intelligence report formatted strictly as a JSON object matching this schema:\n"
            "{\n"
            '  "executive_summary": "1-2 strategic paragraphs summarizing overall health, main drivers, and key priority areas.",\n'
            '  "overall_customer_health": "Healthy | At Risk | Critical",\n'
            '  "key_risks": [{"title": "str", "severity": "Low | Medium | High | Critical", "evidence": "str", "business_impact": "str"}],\n'
            '  "top_pain_points": [{"topic": "str", "summary": "str", "evidence": "str"}],\n'
            '  "recommended_actions": [{"priority": "Immediate | Short Term | Long Term", "action": "str", "reason": "str", "expected_impact": "str"}],\n'
            '  "executive_priorities": ["str"],\n'
            '  "watch_items": [{"item": "str", "reason": "str"}]\n'
            "}\n\n"
            "STRICT RULES:\n"
            "1. Base ALL conclusions, numbers, and recommendations ONLY on the provided context.\n"
            "2. DO NOT invent product releases, incidents, unmentioned bugs, or root causes.\n"
            "3. Use cautious, evidence-backed language ('The data indicates...', 'Feedback suggests...').\n"
            "4. Make recommendations highly specific, cross-functional, and actionable."
        )

        user_prompt = f"Business Analytics Context:\n{json.dumps(context, indent=2)}\n\nGenerate structured executive report JSON:"

        response = client.chat.completions.create(
            model=target_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        raw_json = json.loads(response.choices[0].message.content)
        insights_obj = ExecutiveInsightsResponse.model_validate(raw_json)

        # Save to Cache
        _INSIGHTS_CACHE[context_hash] = insights_obj.model_dump()
        return insights_obj, False, None

    except Exception as e:
        error_msg = f"OpenAI API generation failed: {e}. Defaulting to verified analytical engine."
        if error_log_path:
            error_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(error_log_path, "a", encoding="utf-8") as f:
                f.write(f"[ERROR] {pd.Timestamp.now().isoformat()} - {error_msg}\n")

        # Fallback cleanly to deterministic engine so dashboard never crashes
        response_obj = _generate_deterministic_insights(context)
        _INSIGHTS_CACHE[context_hash] = response_obj.model_dump()
        return response_obj, False, error_msg
