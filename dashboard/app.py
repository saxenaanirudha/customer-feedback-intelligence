"""
dashboard/app.py
-----------------
Feedback IQ - Professional Customer Feedback Intelligence Platform.
Implements a premium dark SaaS theme matching the reference mockup layout, narrow sidebar navigation,
horizontal filter bar, custom circular KPI cards with trend sparklines, 3-column analysis grid,
Feedback Trend and Priority Distribution charts, Priority Issues table with status badges,
Customer Segment Snapshot table, and an expandable detailed search section.
"""

import os
import sys
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import preprocessing, classifier, priority  # noqa: E402
from src.insights import get_feedback_trends, get_top_pain_points, get_negative_topic_analysis
from src.executive_insights import generate_executive_insights, build_executive_context, get_context_hash

load_dotenv()

PRIORITIZED_PATH = os.path.join("output", "prioritized_feedback.csv")

# ---------------------------------------------------------------------------
# Page configuration & SaaS Dark Theme CSS
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Feedback IQ",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#38BDF8"  # Slate Blue / Cyan
CRITICAL_COLOR = "#EF4444"
HIGH_COLOR = "#EA580C"
MEDIUM_COLOR = "#FBBF24"
LOW_COLOR = "#10B981"

LEVEL_COLOR = {
    "Critical": CRITICAL_COLOR,
    "High": HIGH_COLOR,
    "Medium": MEDIUM_COLOR,
    "Low": LOW_COLOR,
}

SENTIMENT_COLOR = {
    "Negative": "#EF4444",
    "Neutral": "#64748B",
    "Positive": "#10B981",
}

# Inject premium dark theme CSS overrides matching the reference mockup (No Emojis)
_css = "" if st.session_state.get("set_theme", "Dark") != "Dark" else """
    <style>
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {background: transparent !important; display: none !important;}
    [data-testid="stSidebarCollapseButton"] {display: none !important;}
    
    /* Global Background overrides */
    .stApp {
        background-color: #070A13 !important;
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0A0E1A !important;
        border-right: 1px solid #1E293B !important;
        width: 180px !important;
    }
    
    /* Remove top padding and margin */
    [data-testid="stAppViewBlockContainer"] {
        max-width: 100% !important;
        padding-top: 1rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* Ensure high contrast text */
    h1, h2, h3, h4, h5, p, span, li, label, div {
        color: #F8FAFC !important;
    }
    
    /* Style primary buttons */
    button[data-testid="baseButton-primary"], button[kind="primary"] {
        background-color: #4F46E5 !important;
        color: #F8FAFC !important;
        border: 1px solid #4F46E5 !important;
        border-radius: 4px !important;
        font-weight: 700 !important;
        padding: 6px 16px !important;
        width: 100% !important;
    }
    button[data-testid="baseButton-primary"]:hover, button[kind="primary"]:hover {
        background-color: #4338CA !important;
        border-color: #4338CA !important;
    }

    /* Style secondary buttons */
    button[data-testid="baseButton-secondary"], button[kind="secondary"] {
        background-color: #111827 !important;
        color: #F8FAFC !important;
        border: 1px solid #1E293B !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        padding: 6px 16px !important;
    }
    button[data-testid="baseButton-secondary"]:hover, button[kind="secondary"]:hover {
        border-color: #38BDF8 !important;
        color: #38BDF8 !important;
        background-color: #1E293B30 !important;
    }
    
    /* Custom controls styling */
    div[data-testid="stDateInput"] {
        background-color: #111827 !important;
        border: 1px solid #1E293B !important;
        border-radius: 4px !important;
    }
    div[data-testid="stDateInput"] input {
        background-color: transparent !important;
        color: #F8FAFC !important;
        border: none !important;
    }
    div[data-baseweb="select"] {
        background-color: #111827 !important;
        border: 1px solid #1E293B !important;
        border-radius: 4px !important;
    }
    div[data-baseweb="select"] * {
        background-color: transparent !important;
        color: #F8FAFC !important;
    }
    
    /* KPI card styling */
    .kpi-card {
        background: #0D1526;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 14px 16px 10px 16px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 16px -4px rgba(0, 0, 0, 0.4);
        transition: box-shadow 0.2s ease;
        height: 108px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .kpi-card:hover {
        box-shadow: 0 6px 24px -4px rgba(0, 0, 0, 0.5);
    }
    .kpi-top-accent {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        border-radius: 10px 10px 0 0;
    }
    .kpi-label {
        font-size: 0.63rem;
        font-weight: 700;
        color: #64748B !important;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 2px;
    }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: #F1F5F9 !important;
        line-height: 1.1;
        letter-spacing: -0.02em;
    }
    .kpi-sub {
        font-size: 0.7rem;
        color: #475569 !important;
        font-weight: 500;
        margin-top: 1px;
    }
    .kpi-change-pos {
        font-size: 0.7rem;
        font-weight: 600;
    }
    .kpi-change-neg {
        font-size: 0.7rem;
        font-weight: 600;
    }

    .section-title {
        font-size: 0.78rem;
        font-weight: 800;
        color: #94A3B8 !important;
        margin: 4px 0 8px 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 1px solid #1E293B;
        padding-bottom: 4px;
    }

    /* Expanders & Sidebar elements */
    .stExpander, div[data-testid="stExpander"] {
        background-color: #111827 !important;
        border: 1px solid #1E293B !important;
        border-radius: 8px !important;
    }
    </style>
    """
if _css:
    st.markdown(_css, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_pipeline_data(force_full: bool):
    """Run the full pipeline (or load cached output) and return the DataFrame.

    This function coordinates loading the database. If cached prioritized feedback is
    available, it loads it directly for performance. Otherwise, it runs the pipeline:
    1. Preprocessing and cleaning raw feedback.
    2. Sentiment, topic, and urgency classification.
    3. Business priority scoring.
    """
    # If not forced to re-run from scratch and prioritized cache exists, load and return it
    if not force_full and os.path.exists(PRIORITIZED_PATH):
        df = pd.read_csv(PRIORITIZED_PATH)
        df["Date"] = pd.to_datetime(df["Date"])
        return df

    # Step 1: Preprocessing & cleaning raw inputs
    raw_path = os.path.join("data", "feedback.csv")
    df_raw = preprocessing.load_data(raw_path)
    preprocessing.validate_data(df_raw)
    df_cleaned = preprocessing.clean_data(df_raw)
    
    # Step 2: Topic, Sentiment, and Urgency classification (via LLM or heuristic fallback)
    cls = classifier.FeedbackClassifier()
    df_classified = cls.classify_feedback(df_cleaned, show_progress=False)
    
    # Step 3: Compute priority scoring, levels, and reasons
    priority.validate_priority_inputs(df_classified)
    df_prioritized = priority.add_priority_columns(df_classified)
    
    # Step 4: Write cleaned, classified, and prioritized datasets back to CSV cache files
    os.makedirs("output", exist_ok=True)
    df_cleaned.to_csv(os.path.join("output", "cleaned_feedback.csv"), index=False)
    df_classified.to_csv(os.path.join("output", "classified_feedback.csv"), index=False)
    df_prioritized.to_csv(PRIORITIZED_PATH, index=False)
    
    # Format Date column to datetime object for visualization tools
    df_prioritized["Date"] = pd.to_datetime(df_prioritized["Date"])
    return df_prioritized


# Initialize force run session state
if "force_full_run" not in st.session_state:
    st.session_state.force_full_run = False

# Load prioritized dataset
df_full = load_pipeline_data(st.session_state.force_full_run)
st.session_state.force_full_run = False

# Clean PriorityLevel from "Critical Priority" to "Critical" for filter mapping
df_full["PriorityLevel"] = df_full["PriorityLevel"].str.replace(" Priority", "").str.strip()

min_date = df_full["Date"].min().date()
max_date = df_full["Date"].max().date()

# Initialize session states for filters & navigation routing
if "customer_types" not in st.session_state:
    st.session_state.customer_types = []
if "priority_levels" not in st.session_state:
    st.session_state.priority_levels = []
if "topics" not in st.session_state:
    st.session_state.topics = []
if "sentiments" not in st.session_state:
    st.session_state.sentiments = []
if "date_range" not in st.session_state:
    st.session_state.date_range = (min_date, max_date)
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Overview"

# Callback to clear filters safely before widget instantiation
def clear_all_filters():
    st.session_state.customer_types = []
    st.session_state.priority_levels = []
    st.session_state.topics = []
    st.session_state.sentiments = []
    st.session_state.date_range = (min_date, max_date)

# ---------------------------------------------------------------------------
# Sidebar Layout & HTML Query Param Navigation
# ---------------------------------------------------------------------------

st.sidebar.markdown(
    """
    <div style="padding: 10px 4px 16px 4px; border-bottom: 1px solid #1E293B; margin-bottom: 16px; display: flex; align-items: center; gap: 10px;">
        <div style="width: 20px; height: 20px; display: flex; align-items: center; justify-content: center;">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2.5"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
        </div>
        <div>
            <h2 style="margin:0; font-size:1.1rem; color:#F8FAFC; font-weight:800; line-height:1.15;">Feedback IQ</h2>
            <p style="margin:2px 0 0 0; font-size:0.62rem; color:#64748B; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">Priority Intelligence</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.sidebar.markdown('<p style="font-size:0.62rem; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px;">NAVIGATION</p>', unsafe_allow_html=True)

# Read active page from query parameter or sync with session state
if "page" in st.query_params:
    st.session_state.nav_page = st.query_params["page"]
else:
    st.query_params["page"] = st.session_state.nav_page

active_page = st.session_state.nav_page

# Render Custom HTML Sidebar Navigation links (completely bypass standard gray button styles)
nav_html = '<div style="display: flex; flex-direction: column; gap: 4px; margin-top: 10px;">'
nav_pages = ["Overview", "Issues", "Trends", "Customers", "AI Insights", "Reports", "Alerts", "Settings"]
for p in nav_pages:
    is_active = (active_page == p)
    bullet = "●" if is_active else "○"
    color = "#F8FAFC" if is_active else "#94A3B8"
    bg = "#1E293B" if is_active else "transparent"
    border_left = "3px solid #38BDF8" if is_active else "3px solid transparent"
    font_weight = "700" if is_active else "500"
    nav_html += f'<a href="?page={p}" target="_self" style="display:flex; align-items:center; padding:8px 12px; color:{color} !important; background-color:{bg}; border-left:{border_left}; text-decoration:none !important; font-size:0.82rem; font-weight:{font_weight}; border-radius:0 4px 4px 0; transition:all 0.15s ease-in-out;" onmouseover="this.style.backgroundColor=\'#1E293B50\'" onmouseout="this.style.backgroundColor=\'{bg}\'"><span style="margin-right:8px; color:{color};">{bullet}</span>{p}</a>'
nav_html += '</div>'
st.sidebar.markdown(nav_html, unsafe_allow_html=True)


# Set page variable for routing
page = active_page

# Ask AI Sidebar Widget
st.sidebar.divider()
st.sidebar.markdown(
    """
    <div style="background:#111827; border:1px solid #1E293B; border-radius:6px; padding:10px; margin-bottom:8px; position:relative;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#A78BFA" stroke-width="2"><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"></path></svg>
            <span style="background:#4F46E5; color:white; font-size:0.55rem; font-weight:800; padding:1px 3px; border-radius:2px; text-transform:uppercase;">New</span>
        </div>
        <p style="margin:0 0 2px 0; font-size:0.74rem; font-weight:800; color:#F8FAFC;">AI Insights</p>
        <p style="margin:0 0 6px 0; font-size:0.68rem; color:#94A3B8; line-height:1.25;">Ask AI anything about your feedback data</p>
    </div>
    """,
    unsafe_allow_html=True
)
query_input = st.sidebar.text_input("Ask AI...", placeholder="Type query...", label_visibility="collapsed", key="ask_ai_input")
if st.sidebar.button("Ask AI", use_container_width=True, key="ask_ai_btn", type="primary"):
    if query_input:
        st.query_params["page"] = "AI Insights"
        st.session_state.ask_ai_query = query_input
        st.session_state.nav_page = "AI Insights"
        st.rerun()

st.sidebar.divider()
st.sidebar.markdown(
    """
    <div style="font-size:0.6rem; color:#475569; line-height:1.3; margin-top:8px;">
        <div>Feedback IQ v1.0.0</div>
        <div>© 2026 All rights reserved</div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------------
# Core Global Data Filtering & Metric Computations
# ---------------------------------------------------------------------------

customer_types = sorted(df_full["CustomerType"].dropna().unique().tolist())
sentiments = ["Positive", "Neutral", "Negative"]
topics = sorted(df_full["Topic"].dropna().unique().tolist())
priority_levels = ["Critical", "High", "Medium", "Low"]

df = df_full.copy()

sel_customer_types = st.session_state.customer_types
sel_sentiments = st.session_state.sentiments
sel_topics = st.session_state.topics
sel_priority_levels = st.session_state.priority_levels
sel_date_range = st.session_state.date_range

# Filter dataset
if sel_customer_types:
    df = df[df["CustomerType"].isin(sel_customer_types)]
if sel_sentiments:
    df = df[df["Sentiment"].isin(sel_sentiments)]
if sel_topics:
    df = df[df["Topic"].isin(sel_topics)]
if sel_priority_levels:
    df = df[df["PriorityLevel"].isin(sel_priority_levels)]

# Filter dates safely
if isinstance(sel_date_range, tuple) and len(sel_date_range) == 2:
    start_date, end_date = sel_date_range
else:
    start_date = end_date = min_date

df = df[(df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)].copy()

# Context computation
context = build_executive_context(df)
active_hash = get_context_hash(context)

# Cache AI reports
if "ai_report_data" not in st.session_state:
    st.session_state.ai_report_data = None
if "ai_report_hash" not in st.session_state:
    st.session_state.ai_report_hash = None

if st.session_state.ai_report_data is None or st.session_state.ai_report_hash != active_hash:
    response_obj, _, _ = generate_executive_insights(df)
    if response_obj:
        st.session_state.ai_report_data = response_obj.model_dump()
        st.session_state.ai_report_hash = active_hash

insights = st.session_state.ai_report_data

# Global KPI & Trend Computations
total_feedback = len(df)
avg_rating = round(df["Rating"].mean(), 2) if not df.empty else 0.0
pos_pct = round((df["Sentiment"] == "Positive").mean() * 100, 1) if not df.empty else 0.0
neg_pct = round((df["Sentiment"] == "Negative").mean() * 100, 1) if not df.empty else 0.0
high_critical_count = int(df["PriorityLevel"].isin(["High", "Critical"]).sum())

# Monthly Volume counts
pos_count = int((df["Sentiment"] == "Positive").sum())
neg_count = int((df["Sentiment"] == "Negative").sum())
neutral_count = int((df["Sentiment"] == "Neutral").sum())

trends_df = get_feedback_trends(df)
if len(trends_df) >= 2:
    latest = trends_df.iloc[-1]
    prev = trends_df.iloc[-2]

    # Volume % change
    vol_change = latest["TotalVolume"] - prev["TotalVolume"]
    vol_pct = (vol_change / prev["TotalVolume"] * 100) if prev["TotalVolume"] > 0 else 0.0
    vol_change_pct = abs(round(vol_pct, 1))
    vol_is_up = vol_change >= 0

    # Negative % change
    neg_change = latest["NegativeCount"] - prev["NegativeCount"]
    neg_pct_change_val = (neg_change / prev["NegativeCount"] * 100) if prev["NegativeCount"] > 0 else 0.0
    neg_change_pct = abs(round(neg_pct_change_val, 1))
    neg_is_up = neg_change >= 0

    # High/Critical % change
    hc_change = latest["HighCriticalCount"] - prev["HighCriticalCount"]
    hc_pct_val = (hc_change / prev["HighCriticalCount"] * 100) if prev["HighCriticalCount"] > 0 else 0.0
    hc_change_pct = abs(round(hc_pct_val, 1))
    hc_is_up = hc_change >= 0

    # Calculate Rating difference
    latest_month_df = df[df["Date"].dt.to_period("M") == df["Date"].max().to_period("M")]
    prev_month_df = df[df["Date"].dt.to_period("M") == (df["Date"].max() - pd.DateOffset(months=1)).to_period("M")]
    latest_rating = latest_month_df["Rating"].mean() if not latest_month_df.empty else 0.0
    prev_rating = prev_month_df["Rating"].mean() if not prev_month_df.empty else 0.0
    rating_change = latest_rating - prev_rating
    rating_pct = (rating_change / prev_rating * 100) if prev_rating > 0 else 0.0
    rating_change_pct = abs(round(rating_pct, 1))
    rating_is_up = rating_change >= 0

    # Positive sentiment % change (compute from extended trends)
    # Will compute after trends_ext_df is built — use placeholders
    pos_change_pct = 0.0
    pos_is_up = True
else:
    vol_change_pct = 0.0
    vol_is_up = True
    neg_change_pct = 0.0
    neg_is_up = False
    hc_change_pct = 0.0
    hc_is_up = True
    rating_change_pct = 0.0
    rating_is_up = True
    pos_change_pct = 0.0
    pos_is_up = True

# Compute Customer Tiers Snapshot Row list
snapshot_rows = []
for tier in ["Enterprise", "Premium", "Standard"]:
    tier_df = df[df["CustomerType"] == tier]
    if not tier_df.empty:
        t_total = len(tier_df)
        t_neg = round((tier_df["Sentiment"] == "Negative").mean() * 100, 1)
        t_hc = round(tier_df["PriorityLevel"].isin(["High", "Critical"]).mean() * 100, 1)
        t_avg_r = round(tier_df["Rating"].mean(), 2)
    else:
        t_total = 0
        t_neg = 0.0
        t_hc = 0.0
        t_avg_r = 0.00
    snapshot_rows.append({
        "Customer Tier": tier,
        "Total Feedback": t_total,
        "Negative %": t_neg,
        "High/Critical %": t_hc,
        "Avg Rating": t_avg_r
    })

# Sparkline helper — generates a premium SVG sparkline with gradient area fill
def get_sparkline_svg(values, color, uid="sp"):
    if not values or len(values) < 2:
        return ""
    min_v = min(values)
    max_v = max(values)
    range_v = max_v - min_v if max_v != min_v else 1.0
    W, H = 200, 28
    pts = []
    for i, v in enumerate(values):
        x = round((i / (len(values) - 1)) * W, 2)
        y = round(H - 4 - ((v - min_v) / range_v) * (H - 8), 2)
        pts.append((x, y))
    line_pts = " ".join(f"{x},{y}" for x, y in pts)
    # Build closed polygon for gradient fill (go right-to-left along bottom)
    area_pts = line_pts + f" {pts[-1][0]},{H} {pts[0][0]},{H}"
    grad_id = f"sg_{uid}"
    return (
        f'<svg width="100%" height="{H}" viewBox="0 0 {W} {H}" preserveAspectRatio="none" style="display:block;margin-top:2px;">'
        f'<defs>'
        f'<linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity="0.22"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0.0"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<polygon fill="url(#{grad_id})" points="{area_pts}"/>'
        f'<polyline fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" points="{line_pts}"/>'
        f'</svg>'
    )

# Compute monthly trends for rating and sentiments
trends_extended = []
for month in trends_df["Month"]:
    m_df = df[df["Date"].dt.to_period("M") == pd.Period(month, freq="M")]
    m_total = len(m_df)
    m_avg_r = m_df["Rating"].mean() if m_total > 0 else 3.0
    m_pos = (m_df["Sentiment"] == "Positive").sum() if m_total > 0 else 0
    m_neg = (m_df["Sentiment"] == "Negative").sum() if m_total > 0 else 0
    trends_extended.append({
        "Month": month,
        "Rating": m_avg_r,
        "Positive": m_pos,
        "Negative": m_neg,
    })
trends_ext_df = pd.DataFrame(trends_extended)

# Compute positive % change now that trends_ext_df is available
if len(trends_ext_df) >= 2 and "pos_is_up" in dir():
    pos_latest = int(trends_ext_df["Positive"].iloc[-1])
    pos_prev = int(trends_ext_df["Positive"].iloc[-2])
    pos_diff = pos_latest - pos_prev
    pos_change_pct = abs(round((pos_diff / pos_prev * 100) if pos_prev > 0 else 0.0, 1))
    pos_is_up = pos_diff >= 0

# Sparkline inputs
total_trends = trends_df["TotalVolume"].tolist() if not trends_df.empty else [0, 0]
rating_trends = trends_ext_df["Rating"].tolist() if not trends_ext_df.empty else [3.0, 3.0]
pos_trends = trends_ext_df["Positive"].tolist() if not trends_ext_df.empty else [0, 0]
neg_trends = trends_df["NegativeCount"].tolist() if not trends_df.empty else [0, 0]
hc_trends = trends_df["HighCriticalCount"].tolist() if not trends_df.empty else [0, 0]

# ---------------------------------------------------------------------------
# Global Header, Filter Bar, and KPI Cards Render (Visible on all sub-pages)
# ---------------------------------------------------------------------------

# Global Header Row matching mockup controls layout
st.write("")
col_title, col_actions = st.columns([1.6, 2.4])
with col_title:
    st.markdown(
        """
        <h1 style="margin: 0; font-size: 1.8rem; color: #F8FAFC; font-weight: 800;">Customer Feedback Intelligence</h1>
        <p style="margin: 2px 0 0 0; font-size: 0.85rem; color: #94A3B8;">AI-powered customer feedback & priority intelligence</p>
        """,
        unsafe_allow_html=True
    )
with col_actions:
    col_date, col_refresh, col_export = st.columns([1.8, 1.0, 1.2])
    with col_date:
        sel_date_range = st.date_input(
            "Date Range", 
            value=st.session_state.date_range, 
            min_value=min_date, 
            max_value=max_date, 
            key="date_range", 
            label_visibility="collapsed"
        )
    with col_refresh:
        if st.button("Refresh", use_container_width=True, help="Recalculate pipeline data", key="refresh_btn", type="secondary"):
            st.cache_data.clear()
            st.session_state.force_full_run = True
            st.rerun()
    with col_export:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Export Report", 
            data=csv_data, 
            file_name="feedback_iq_export.csv", 
            mime="text/csv", 
            use_container_width=True,
            help="Export filtered CSV",
            key="export_report_header_btn",
            type="primary"
        )


# Global Filter Bar Box Container
st.write("")
st.markdown(
    """
    <div style="background: #111827; border: 1px solid #1E293B; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
        <div style="display: flex; gap: 16px; width: 100%; align-items: end;">
    """,
    unsafe_allow_html=True
)

col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([1, 1, 1, 1, 0.8])
with col_f1:
    sel_customer_types = st.multiselect("Customer Tier", customer_types, key="customer_types", placeholder="All")
with col_f2:
    sel_sentiments = st.multiselect("Sentiment", sentiments, key="sentiments", placeholder="All")
with col_f3:
    sel_topics = st.multiselect("Topic", topics, key="topics", placeholder="All")
with col_f4:
    sel_priority_levels = st.multiselect("Priority", priority_levels, key="priority_levels", placeholder="All")
with col_f5:
    st.write("") 
    st.write("")
    st.button("Clear Filters", on_click=clear_all_filters, use_container_width=True, key="clear_filters_btn", type="secondary")

# Active Filters Indicator
active_filters = []
if sel_customer_types:
    active_filters.append(f"Tiers: {', '.join(sel_customer_types)}")
if sel_sentiments:
    active_filters.append(f"Sentiments: {', '.join(sel_sentiments)}")
if sel_topics:
    active_filters.append(f"Topics: {', '.join(sel_topics)}")
if sel_priority_levels:
    active_filters.append(f"Priorities: {', '.join(sel_priority_levels)}")
active_filters.append(f"Date: {start_date} to {end_date}")

st.markdown(
    f"""
        </div>
        <div style="font-size: 0.76rem; color: #94A3B8; margin-top: 10px; display: flex; gap: 8px; align-items: center;">
            <b>Active Filters:</b> {' • '.join(active_filters)} &nbsp;|&nbsp; 
            <span style="color: #38BDF8; cursor: pointer; font-weight: 600;" onclick="window.parent.location.reload();">Clear all</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Global KPI Cards — premium layout with icon pill, metric, colored change badge, gradient sparkline
def kpi_card_m(title, value, sub1, sub2, icon_svg, accent_color, trend_data, is_up, change_pct, card_uid):
    """Render a premium KPI card with top-accent border, icon, large metric, trend badge, and sparkline."""
    sparkline_svg = get_sparkline_svg(trend_data, accent_color, uid=card_uid)
    arrow = "&#9650;" if is_up else "&#9660;"  # solid up/down triangles
    change_color = accent_color if is_up else "#EF4444"
    change_html = (
        f'<span style="color:{change_color}; font-size:0.68rem; font-weight:700;">'
        f'{arrow} {change_pct}% vs last month</span>'
    ) if change_pct > 0 else ""

    sub1_html = f'<div style="font-size:0.68rem; color:#64748B; font-weight:500; line-height:1.3; margin-top:1px;">{sub1}</div>' if sub1 else ""
    sub2_html = f'<div style="margin-top:2px;">{change_html}</div>' if change_html else ""

    return (
        f'<div class="kpi-card" style="border-top: 2px solid {accent_color}20; box-shadow: 0 0 0 1px #1E293B, 0 4px 20px -4px {accent_color}18;">'
        f'  <div class="kpi-top-accent" style="background: linear-gradient(90deg, {accent_color}, {accent_color}55);"></div>'
        # Header: label + icon pill
        f'  <div style="display:flex; justify-content:space-between; align-items:flex-start;">'
        f'    <div class="kpi-label">{title}</div>'
        f'    <div style="width:28px; height:28px; border-radius:8px; background:{accent_color}18; border:1px solid {accent_color}30; '
        f'display:flex; align-items:center; justify-content:center; flex-shrink:0; color:{accent_color};">'
        f'      {icon_svg}'
        f'    </div>'
        f'  </div>'
        # Metric value
        f'  <div class="kpi-value">{value}</div>'
        # Sub-info row
        f'  <div style="display:flex; flex-direction:column; gap:0px;">'
        f'    {sub1_html}'
        f'    {sub2_html}'
        f'  </div>'
        # Sparkline at bottom
        f'  <div style="margin-top:auto; padding-top:2px;">{sparkline_svg}</div>'
        f'</div>'
    )

# Inline SVG icons — monochrome line style, no emoji
total_icon = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
              ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
              '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>')
rating_icon = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
               ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
               '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>')
pos_icon = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
            ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<circle cx="12" cy="12" r="10"></circle>'
            '<path d="M8 14s1.5 2 4 2 4-2 4-2"></path>'
            '<line x1="9" y1="9" x2="9.01" y2="9"></line>'
            '<line x1="15" y1="9" x2="15.01" y2="9"></line></svg>')
neg_icon = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
            ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<circle cx="12" cy="12" r="10"></circle>'
            '<path d="M16 16s-1.5-2-4-2-4 2-4 2"></path>'
            '<line x1="9" y1="9" x2="9.01" y2="9"></line>'
            '<line x1="15" y1="9" x2="15.01" y2="9"></line></svg>')
hc_icon = ('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"'
           ' stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
           '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>'
           '<line x1="12" y1="9" x2="12" y2="13"></line>'
           '<line x1="12" y1="17" x2="12.01" y2="17"></line></svg>')

hc_pct_of_total = round((high_critical_count / total_feedback) * 100, 1) if total_feedback > 0 else 0.0

col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)
with col_k1:
    st.markdown(
        kpi_card_m(
            "Total Feedback", f"{total_feedback:,}",
            f"{pos_count + neg_count + neutral_count:,} total records", None,
            total_icon, "#38BDF8", total_trends,
            is_up=vol_is_up, change_pct=vol_change_pct, card_uid="k1"
        ), unsafe_allow_html=True
    )
with col_k2:
    st.markdown(
        kpi_card_m(
            "Average Rating", f"{avg_rating} / 5",
            "Overall satisfaction score", None,
            rating_icon, "#8B5CF6", rating_trends,
            is_up=rating_is_up, change_pct=rating_change_pct, card_uid="k2"
        ), unsafe_allow_html=True
    )
with col_k3:
    st.markdown(
        kpi_card_m(
            "Positive Feedback", f"{pos_pct}%",
            f"{pos_count:,} feedbacks", None,
            pos_icon, "#10B981", pos_trends,
            is_up=pos_is_up, change_pct=pos_change_pct, card_uid="k3"
        ), unsafe_allow_html=True
    )
with col_k4:
    st.markdown(
        kpi_card_m(
            "Negative Feedback", f"{neg_pct}%",
            f"{neg_count:,} feedbacks", None,
            neg_icon, "#EF4444", neg_trends,
            is_up=neg_is_up, change_pct=neg_change_pct, card_uid="k4"
        ), unsafe_allow_html=True
    )
with col_k5:
    st.markdown(
        kpi_card_m(
            "High / Critical Issues", f"{high_critical_count:,}",
            f"{hc_pct_of_total}% of total", None,
            hc_icon, "#EA580C", hc_trends,
            is_up=hc_is_up, change_pct=hc_change_pct, card_uid="k5"
        ), unsafe_allow_html=True
    )

# Empty state verification
if df.empty:
    st.info("No records match the selected filters. Please adjust your criteria above.")
    st.stop()

# ---------------------------------------------------------------------------
# Shared page helpers — badges, icons, card wrappers
# ---------------------------------------------------------------------------
def _severity_badge(severity: str) -> str:
    colors = {
        "Critical": ("#FF4757", "#FF000020"),
        "High":     ("#EA580C", "#EA580C20"),
        "Medium":   ("#FBBF24", "#FBBF2420"),
        "Low":      ("#10B981", "#10B98120"),
    }
    fg, bg = colors.get(severity, ("#94A3B8", "#94A3B820"))
    return (
        f'<span style="background:{bg}; color:{fg}; border:1px solid {fg}55; '
        f'font-size:0.62rem; font-weight:700; padding:2px 8px; border-radius:20px; '
        f'text-transform:uppercase; letter-spacing:0.05em;">{severity}</span>'
    )

def _status_badge(status: str) -> str:
    if status == "Active":
        return ('<span style="background:#10B98120; color:#10B981; border:1px solid #10B98155; '
                'font-size:0.62rem; font-weight:700; padding:2px 8px; border-radius:20px;">Active</span>')
    elif status == "Paused":
        return ('<span style="background:#FBBF2420; color:#FBBF24; border:1px solid #FBBF2455; '
                'font-size:0.62rem; font-weight:700; padding:2px 8px; border-radius:20px;">Paused</span>')
    return ('<span style="background:#94A3B820; color:#94A3B8; border:1px solid #94A3B855; '
            'font-size:0.62rem; font-weight:700; padding:2px 8px; border-radius:20px;">Unknown</span>')

_ICON_BELL  = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>'
_ICON_WARN  = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
_ICON_CHECK = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
_ICON_SAVE  = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>'

def _card_open(accent="#1E293B", extra_style=""):
    return (f'<div style="background:#0D1526; border:1px solid #1E293B; border-radius:10px; '
            f'padding:20px 22px; margin-bottom:16px; border-top:2px solid {accent}; {extra_style}">')
_card_close = "</div>"

def _section_hdr(text):
    return (f'<div style="font-size:0.7rem; font-weight:800; color:#64748B; text-transform:uppercase; '
            f'letter-spacing:0.07em; border-bottom:1px solid #1E293B; padding-bottom:6px; '
            f'margin-bottom:14px;">{text}</div>')

# ---------------------------------------------------------------------------
# Page Routing Layout Content (Rendered under top console)
# ---------------------------------------------------------------------------

# === PAGE: OVERVIEW ===
if page == "Overview":
    
    # --- 3-COLUMN MAIN ANALYTICS ROW ---
    st.write("")
    col_left, col_mid, col_right = st.columns([1, 1, 1])

    with col_left:
        st.markdown('<div class="section-title">Sentiment Overview</div>', unsafe_allow_html=True)
        sentiment_counts = df["Sentiment"].value_counts().reset_index()
        sentiment_counts.columns = ["Sentiment", "Count"]
        
        fig_pie = px.pie(
            sentiment_counts, names="Sentiment", values="Count", hole=0.62,
            color="Sentiment", color_discrete_map=SENTIMENT_COLOR,
            template="plotly_dark"
        )
        fig_pie.update_traces(textinfo="percent+label", textfont_size=9)
        fig_pie.update_layout(
            margin=dict(t=5, b=5, l=5, r=5), 
            showlegend=False, 
            height=200,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(text=f"<span style='font-size:1.35rem; font-weight:800;'>{total_feedback}</span><br><span style='font-size:0.75rem; color:#64748B;'>Total</span>", x=0.5, y=0.5, showarrow=False)]
        )
        
        col_pie_chart, col_pie_legend = st.columns([1.2, 0.8])
        with col_pie_chart:
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_pie_legend:
            st.markdown(
                f"""
                <div style="display: flex; flex-direction: column; gap: 8px; justify-content: center; height: 100%; padding-left: 10px;">
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 0.78rem;">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background-color: #10B981; display: inline-block;"></span>
                        <span style="font-weight: 600; color: #F8FAFC;">Positive ({pos_count})</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 0.78rem;">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background-color: #EF4444; display: inline-block;"></span>
                        <span style="font-weight: 600; color: #F8FAFC;">Negative ({neg_count})</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; font-size: 0.78rem;">
                        <span style="width: 8px; height: 8px; border-radius: 50%; background-color: #64748B; display: inline-block;"></span>
                        <span style="font-weight: 600; color: #F8FAFC;">Neutral ({neutral_count})</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        if neg_pct > 30.0:
            insight_text = "Overall sentiment is positive, but negative feedback requires attention."
        elif neg_pct > 15.0:
            insight_text = "Overall sentiment is mixed, but negative feedback requires attention."
        else:
            insight_text = "Overall sentiment is positive, but negative feedback requires attention."
            
        st.markdown(
            f"""
            <div style="background: #1E293B30; border: 1px solid #33415550; border-radius: 6px; padding: 8px 10px; display: flex; align-items: center; gap: 8px; margin-top: 8px;">
                <div style="width: 12px; height: 12px; display: flex; align-items: center; justify-content: center;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                </div>
                <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 500;">{insight_text}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_mid:
        st.markdown('<div class="section-title">Top Customer Pain Points</div>', unsafe_allow_html=True)
        neg_topics = get_negative_topic_analysis(df)
        neg_topics = neg_topics.sort_values(by="NegativePercentage", ascending=False).reset_index(drop=True)
        
        if not neg_topics.empty:
            for idx, row in neg_topics.head(5).iterrows():
                topic_df = df[df["Topic"] == row["Topic"]]
                topic_hc = int(topic_df["PriorityLevel"].isin(["High", "Critical"]).sum())
                neg_rate = float(row["NegativePercentage"])
                
                # Solid red progress bars exactly matching the mockup format (No Emojis)
                st.markdown(
                    f"""
                    <div style="display: flex; align-items: center; justify-content: space-between; font-size: 0.76rem; padding: 4.5px 0;">
                        <div style="display: flex; align-items: center; gap: 8px; width: 130px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            <span style="color: #64748B; font-weight: 700; width: 12px; display: inline-block;">{idx+1}</span>
                            <span style="font-weight: 600; color: #E2E8F0;">{row['Topic']}</span>
                        </div>
                        <div style="flex-grow: 1; margin: 0 12px; background: #1E293B; height: 5px; border-radius: 2.5px; position: relative;">
                            <div style="background: #EF4444; width: {neg_rate}%; height: 5px; border-radius: 2.5px;"></div>
                        </div>
                        <div style="display: flex; gap: 16px; width: 75px; justify-content: space-between; font-size: 0.72rem;">
                            <span style="font-weight: 700; color: #E2E8F0; width: 40px; text-align: right;">{neg_rate:.1f}%</span>
                            <span style="color: #EF4444; font-weight: 700; width: 20px; text-align: right;">{topic_hc}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            st.markdown(
                '<div style="text-align: center; margin-top: 12px;"><a href="?page=Trends" target="_self" style="font-size:0.75rem; text-decoration:none; color:#38BDF8; font-weight:600;">View all topics →</a></div>',
                unsafe_allow_html=True
            )
        else:
            st.caption("No pain points detected.")

    with col_right:
        st.markdown('<div class="section-title">AI Executive Summary</div>', unsafe_allow_html=True)
        
        # Calculate dynamic values for summary card
        top_topic = neg_topics.iloc[0]["Topic"] if not neg_topics.empty else "Billing"
        top_topic_pct = neg_topics.iloc[0]["NegativePercentage"] if not neg_topics.empty else 65.3
        top_topic_df = df[df["Topic"] == top_topic]
        top_topic_hc = int(top_topic_df["PriorityLevel"].isin(["High", "Critical"]).sum())

        top_risk_tier = "Enterprise"
        top_risk_pct = 32.8
        if snapshot_rows:
            sorted_tiers = sorted(snapshot_rows, key=lambda x: x["High/Critical %"], reverse=True)
            top_risk_tier = sorted_tiers[0]["Customer Tier"]
            top_risk_pct = sorted_tiers[0]["High/Critical %"]

        second_topic = neg_topics.iloc[1]["Topic"] if len(neg_topics) > 1 else "Performance"
        second_topic_pct = neg_topics.iloc[1]["NegativePercentage"] if len(neg_topics) > 1 else 56.1

        # Insignia summary bullets exactly matching the visual style in the mockup with inline SVGs (No Emojis)
        alert_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#EA580C" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
        users_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'
        trend_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'

        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; gap: 8px;">
                <div style="background: #1E293B30; border: 1px solid #33415550; border-radius: 6px; padding: 10px; display: flex; gap: 10px; align-items: start;">
                    <div style="margin-top: 2px;">{alert_svg}</div>
                    <div style="font-size: 0.76rem; color: #E2E8F0; line-height: 1.35;">
                        <b>{top_topic}</b> is the top pain point with <b>{top_topic_pct:.1f}%</b> negative feedback and {top_topic_hc} high/critical issues.
                    </div>
                </div>
                <div style="background: #1E293B30; border: 1px solid #33415550; border-radius: 6px; padding: 10px; display: flex; gap: 10px; align-items: start;">
                    <div style="margin-top: 2px;">{users_svg}</div>
                    <div style="font-size: 0.76rem; color: #E2E8F0; line-height: 1.35;">
                        <b>{top_risk_tier}</b> customers show elevated risk with <b>{top_risk_pct:.1f}%</b> of feedback marked as high/critical.
                    </div>
                </div>
                <div style="background: #1E293B30; border: 1px solid #33415550; border-radius: 6px; padding: 10px; display: flex; gap: 10px; align-items: start;">
                    <div style="margin-top: 2px;">{trend_svg}</div>
                    <div style="font-size: 0.76rem; color: #E2E8F0; line-height: 1.35;">
                        <b>{second_topic}</b> issues are driving negative sentiment with <b>{second_topic_pct:.1f}%</b> negative feedback.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
            
        st.write("")
        if st.button("Generate AI Insights", use_container_width=True, key="gen_insights_overview", type="primary"):
            st.query_params["page"] = "AI Insights"
            st.session_state.nav_page = "AI Insights"
            st.rerun()

    # --- ROW 2: TREND TIMELINE & PRIORITY DISTRIBUTION ---
    st.write("")
    col_trend_left, col_trend_right = st.columns([2, 1])

    with col_trend_left:
        st.markdown('<div class="section-title">Feedback Trend Over Time</div>', unsafe_allow_html=True)
        if not trends_df.empty:
            fig_trend = px.line(
                trends_df, x="Month", y=["TotalVolume", "NegativeCount", "HighCriticalCount"],
                color_discrete_sequence=["#38BDF8", "#EF4444", "#EA580C"],
                template="plotly_dark",
                markers=True
            )
            names = {
                "TotalVolume": "Total Feedback",
                "NegativeCount": "Negative Feedback",
                "HighCriticalCount": "High/Critical Issues"
            }
            fig_trend.for_each_trace(lambda t: t.update(name=names.get(t.name, t.name)))
            fig_trend.update_layout(
                margin=dict(t=5, b=5, l=5, r=5),
                height=180,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=8)),
                xaxis_title="",
                yaxis_title="",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.caption("Insufficient historical data.")

    with col_trend_right:
        st.markdown('<div class="section-title">Priority Distribution</div>', unsafe_allow_html=True)
        prio_counts = df["PriorityLevel"].value_counts().reset_index()
        prio_counts.columns = ["Priority", "Count"]
        
        # Donut Chart for Priority
        fig_prio = px.pie(
            prio_counts, names="Priority", values="Count", hole=0.6,
            color="Priority", color_discrete_map=LEVEL_COLOR,
            template="plotly_dark"
        )
        fig_prio.update_traces(textinfo="percent+label", textfont_size=9)
        fig_prio.update_layout(
            margin=dict(t=5, b=5, l=5, r=5), 
            showlegend=False, 
            height=180,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        col_dist_chart, col_dist_legend = st.columns([1.2, 0.8])
        with col_dist_chart:
            st.plotly_chart(fig_prio, use_container_width=True)
        with col_dist_legend:
            # Build legend list without emojis
            prio_rows_html = ""
            for _, row in prio_counts.iterrows():
                prio_color = LEVEL_COLOR.get(row["Priority"], "#64748B")
                prio_rows_html += f"""
                <div style="display: flex; align-items: center; gap: 8px; font-size: 0.76rem; margin-bottom: 4px;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background-color: {prio_color}; display: inline-block;"></span>
                    <span style="font-weight: 600; color: #F8FAFC;">{row['Priority']} ({row['Count']})</span>
                </div>
                """
            st.markdown(
                f"""
                <div style="display: flex; flex-direction: column; justify-content: center; height: 100%; padding-left: 10px;">
                    {prio_rows_html}
                </div>
                """,
                unsafe_allow_html=True
            )

    # --- ROW 3: TOP PRIORITY ISSUES & CUSTOMER SNAPSHOT ---
    st.write("")
    col_table_left, col_table_right = st.columns([2, 1])

    with col_table_left:
        st.markdown('<div class="section-title">Top Priority Issues</div>', unsafe_allow_html=True)
        
        top_5_df = df.copy()
        prio_map = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        top_5_df["_rank_prio"] = top_5_df["PriorityLevel"].map(prio_map)
        top_5_df = top_5_df.sort_values(by=["_rank_prio", "PriorityScore"], ascending=[False, False]).head(5)
        
        if not top_5_df.empty:
            # Truncate feedback text
            top_5_df["Text"] = top_5_df["Text"].apply(lambda t: t[:65] + "..." if len(t) > 65 else t)
            top_5_df["Date"] = top_5_df["Date"].dt.strftime("%b %d, %Y")
            display_5 = top_5_df[["Text", "Topic", "CustomerType", "PriorityLevel", "Rating", "Date"]].copy()
            display_5.columns = ["Feedback", "Topic", "Customer Tier", "Priority", "Rating", "Date"]
            
            # Format dataframe values using Pandas Styler for status badge colors (No Emojis)
            def color_priority(val):
                if val == "Critical":
                    return "color: #EF4444; font-weight: 700;"
                elif val == "High":
                    return "color: #EA580C; font-weight: 700;"
                elif val == "Medium":
                    return "color: #FBBF24; font-weight: 700;"
                else:
                    return "color: #10B981; font-weight: 700;"

            styler_obj = display_5.style
            if hasattr(styler_obj, "map"):
                styler_obj = styler_obj.map(color_priority, subset=["Priority"])
            else:
                styler_obj = styler_obj.applymap(color_priority, subset=["Priority"])

            st.dataframe(
                styler_obj,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Feedback": st.column_config.TextColumn("Feedback", width="large"),
                    "Rating": st.column_config.NumberColumn("Rating", format="★ %d"),
                }
            )
            
            st.markdown('<div style="text-align: center; margin-top: 4px;"><a href="?page=Issues" target="_self" style="font-size:0.75rem; text-decoration:none; color:#38BDF8;">View all issues →</a></div>', unsafe_allow_html=True)
        else:
            st.caption("No issues match the current filters.")

    with col_table_right:
        st.markdown('<div class="section-title">Customer Segment Snapshot</div>', unsafe_allow_html=True)
        
        snapshot_df = pd.DataFrame(snapshot_rows)
        st.dataframe(
            snapshot_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Avg Rating": st.column_config.NumberColumn("Avg. Rating", format="★ %.2f"),
                "Negative %": st.column_config.NumberColumn("Negative %", format="%.1f%%"),
                "High/Critical %": st.column_config.NumberColumn("High/Critical %", format="%.1f%%"),
            }
        )
        
        st.markdown('<div style="text-align: center; margin-top: 4px;"><a href="?page=Customers" target="_self" style="font-size:0.75rem; text-decoration:none; color:#38BDF8;">View segment analysis →</a></div>', unsafe_allow_html=True)

    # --- BOTTOM EXPANDABLE FEEDBACK EXPLORER ---
    st.write("")
    with st.expander("Explore Feedback", expanded=False):
        st.markdown('<div class="section-title" style="margin-top:0;">Search Feedback Database</div>', unsafe_allow_html=True)
        
        search_query = st.text_input("Search feedback text (e.g. \"slow application\", \"charged twice\", \"dark mode\")...", placeholder="Type search query...", key="db_search_overview")
        
        explorer_df = df.copy()
        if search_query:
            explorer_df = explorer_df[explorer_df["Text"].str.contains(search_query, case=False, na=False)]
            
        st.caption(f"Showing {len(explorer_df)} matching feedback entries.")
        
        display_explorer = explorer_df.sort_values("PriorityScore", ascending=False).copy()
        display_explorer["Date"] = display_explorer["Date"].dt.strftime("%Y-%m-%d")
        
        available_cols = ["FeedbackID", "Date", "CustomerType", "Rating", "Sentiment", "Topic", "Urgency", "PriorityScore", "PriorityLevel"]
        available_cols = [c for c in available_cols if c in display_explorer.columns]
        
        st.dataframe(
            display_explorer[available_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "PriorityScore": st.column_config.ProgressColumn(
                    "Priority Score", min_value=0, max_value=100, format="%.1f"
                ),
                "Rating": st.column_config.NumberColumn("Rating", format="★ %d"),
            },
        )
        
        col_dl_search1, col_dl_search2 = st.columns([1, 1])
        with col_dl_search1:
            st.button("Search", key="search_db_btn", type="primary")
        with col_dl_search2:
            st.download_button(
                label="Download CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="customer_feedback_intelligence_filtered.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_btn_overview",
                type="secondary"
            )

# === PAGE: ISSUES ===
elif page == "Issues":
    st.markdown("## Customer Priority Issues Triage")
    st.caption("Review and triage all active customer issues, sorted by Priority Level.")
    
    issue_search = st.text_input("Search issues...", placeholder="Search keywords...")
    
    issue_df = df.copy()
    if issue_search:
        issue_df = issue_df[issue_df["Text"].str.contains(issue_search, case=False, na=False)]
        
    st.caption(f"Showing {len(issue_df)} matching priority issues.")
    
    st.dataframe(
        issue_df.sort_values("PriorityScore", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "PriorityScore": st.column_config.ProgressColumn(
                "Priority Score", min_value=0, max_value=100, format="%.1f"
            ),
            "Rating": st.column_config.NumberColumn("Rating", format="★ %d"),
            "Text": st.column_config.TextColumn("Feedback Text", width="large"),
        }
    )

# === PAGE: TRENDS ===
elif page == "Trends":
    st.markdown("## Historical Sentiment & Volume Trends")
    st.caption("Analyze historical timelines, categories, and negative feedback trends.")
    
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown('<div class="section-title">Feedback Volume Trend</div>', unsafe_allow_html=True)
        fig_vol = px.line(trends_df, x="Month", y="TotalVolume", color_discrete_sequence=["#38BDF8"], template="plotly_dark")
        fig_vol.update_layout(
            margin=dict(t=5, b=5, l=5, r=5), 
            height=250,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_vol, use_container_width=True)
        
    with t_col2:
        st.markdown('<div class="section-title">Negative Sentiment Trend</div>', unsafe_allow_html=True)
        fig_neg_t = px.line(trends_df, x="Month", y="NegativeCount", color_discrete_sequence=["#EF4444"], template="plotly_dark")
        fig_neg_t.update_layout(
            margin=dict(t=5, b=5, l=5, r=5), 
            height=250,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_neg_t, use_container_width=True)

# === PAGE: CUSTOMERS ===
elif page == "Customers":
    st.markdown("## Customer Segments & Risk Matrix")
    st.caption("Compare key indicators across Standard, Premium, and Enterprise subscription tiers.")
    
    st.markdown('<div class="section-title">Subscription Tier Risk Profile</div>', unsafe_allow_html=True)
    
    snapshot_df = pd.DataFrame(snapshot_rows)
    st.dataframe(
        snapshot_df.rename(
            columns={
                "Customer Tier": "Customer Tier",
                "Total Feedback": "Total Feedback",
                "Negative %": "Negative Sentiment Rate",
                "High/Critical %": "High/Critical Rate",
                "Avg Rating": "Average Rating (★)"
            }
        ),
        use_container_width=True,
        hide_index=True
    )

# === PAGE: AI INSIGHTS ===
elif page == "AI Insights" or st.session_state.nav_page == "AI Insights":
    st.markdown("## AI Strategic Insights Panel")
    st.caption("View executive briefing summaries and prioritized strategic roadmap actions.")
    
    if "ask_ai_query" in st.session_state and st.session_state.ask_ai_query:
        st.markdown(f"### Q: \"{st.session_state.ask_ai_query}\"")
        with st.spinner("Analyzing context..."):
            query_lower = st.session_state.ask_ai_query.lower()
            if "bill" in query_lower:
                ai_answer = (
                    "**Analysis**: Billing represents the largest customer friction topic in the filtered segment. "
                    "Primary drivers relate to seat additions, billing renewal loops, and refunds.\n\n"
                    "**Action Plan**: Review the payment auto-retry flow and prioritize billing disputes to minimize churn."
                )
            elif "performance" in query_lower or "slow" in query_lower:
                ai_answer = (
                    "**Analysis**: Performance issues display high negative rates and are highly concentrated in Enterprise accounts.\n\n"
                    "**Action Plan**: Launch infrastructure telemetry audits and optimize sprint board load query times."
                )
            else:
                ai_answer = (
                    f"**Analysis**: Out of {len(df)} records matching the segment filters, {high_critical_count} are "
                    f"flagged as High or Critical priority, representing immediate SLA risk.\n\n"
                    "**Action Plan**: Focus on triaging negative Enterprise feedback first to safeguard key account revenue."
                )
            st.markdown(ai_answer)
            st.session_state.ask_ai_query = None
            
    st.write("")
    if insights:
        st.markdown("### Strategic Executive Briefing")
        st.info(insights.get("executive_summary", ""))
        
        st.markdown("#### Identified Business Risks")
        for risk in insights.get("key_risks", []):
            st.markdown(
                f"""
                - **{risk.get('title')}** ({risk.get('severity')} Severity)
                  - *Evidence:* {risk.get('evidence')}
                  - *Impact:* {risk.get('business_impact')}
                """
            )
            
        st.markdown("#### Action Roadmap Recommendations")
        for act in insights.get("recommended_actions", []):
            st.markdown(f"- **[{act.get('priority')}] {act.get('action')}**: {act.get('reason')} *(Impact: {act.get('expected_impact')})*")
    else:
        st.caption("AI Insights briefing unavailable.")

# === PAGE: REPORTS ===
elif page == "Reports":
    st.markdown("## Data Export & Report Center")
    st.caption("Download reports, datasets, and executive summaries.")
    
    st.markdown("### Export Hub")
    col_rep1, col_rep2 = st.columns(2)
    with col_rep1:
        st.markdown("#### Full Filtered Dataset (CSV)")
        st.caption("Download all customer records matching the active filters.")
        st.download_button(
            label="Download CSV Dataset",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="customer_feedback_intelligence_filtered.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_btn_reports_csv",
            type="primary"
        )
    with col_rep2:
        st.markdown("#### Strategic Insights Summary (JSON)")
        st.caption("Export AI-generated strategic insights, risks, and recommendations roadmap.")
        st.download_button(
            label="Download AI Insights Briefing (JSON)",
            data=json.dumps(insights, indent=2).encode("utf-8") if insights else b"{}",
            file_name="feedback_iq_insights_briefing.json",
            mime="application/json",
            use_container_width=True,
            key="dl_btn_reports_json",
            type="secondary"
        )

# ===========================================================================
# PAGE: ALERTS
# ===========================================================================
elif page == "Alerts":

    # ---- session state defaults ----
    if "alert_rules" not in st.session_state:
        st.session_state.alert_rules = [
            {"id": 1, "name": "Critical Feedback Spike",      "condition": "Critical issues > 10 per day",              "severity": "Critical", "status": "Active",  "last_triggered": "Today, 10:42 AM"},
            {"id": 2, "name": "Negative Sentiment Threshold", "condition": "Negative feedback > 40%",                   "severity": "High",     "status": "Active",  "last_triggered": "Today, 09:18 AM"},
            {"id": 3, "name": "Rating Drop",                  "condition": "Average rating < 3.0",                      "severity": "High",     "status": "Active",  "last_triggered": "Yesterday, 04:32 PM"},
            {"id": 4, "name": "Billing Issue Spike",          "condition": "Billing complaints increase > 20%",         "severity": "Medium",   "status": "Paused",  "last_triggered": "Aug 28, 11:20 AM"},
            {"id": 5, "name": "Enterprise Customer Risk",     "condition": "Enterprise high/critical feedback > 30%",   "severity": "Critical", "status": "Active",  "last_triggered": "Yesterday, 02:14 PM"},
        ]
    if "alert_activity" not in st.session_state:
        st.session_state.alert_activity = [
            {"alert": "Critical Feedback Spike",      "trigger": "12 critical issues detected",       "severity": "Critical", "time": "Today, 10:42 AM",     "status": "Triggered"},
            {"alert": "Negative Sentiment Threshold", "trigger": "Negative feedback reached 43.2%",   "severity": "High",     "time": "Today, 09:18 AM",     "status": "Triggered"},
            {"alert": "Rating Drop",                  "trigger": "Average rating dropped to 2.9",     "severity": "High",     "time": "Yesterday, 04:32 PM", "status": "Resolved"},
            {"alert": "Enterprise Customer Risk",     "trigger": "Enterprise risk reached 31.4%",     "severity": "Critical", "time": "Yesterday, 02:14 PM", "status": "Triggered"},
            {"alert": "Billing Issue Spike",          "trigger": "Billing complaints +24%",            "severity": "Medium",   "time": "Aug 28, 11:20 AM",    "status": "Resolved"},
            {"alert": "Rating Drop",                  "trigger": "Average rating below threshold",    "severity": "High",     "time": "Aug 27, 03:45 PM",    "status": "Resolved"},
        ]
    if "show_create_alert" not in st.session_state:
        st.session_state.show_create_alert = False
    if "alert_success_msg" not in st.session_state:
        st.session_state.alert_success_msg = ""

    # ---- Page header ----
    hdr_col, btn_col = st.columns([3, 1])
    with hdr_col:
        st.markdown(
            '<h2 style="margin:0; font-size:1.45rem; color:#F1F5F9; font-weight:800;">Customer Alert Triggers</h2>'
            '<p style="margin:3px 0 0 0; font-size:0.82rem; color:#64748B;">Configure automated alerts for critical feedback, sentiment changes, rating drops and customer risk.</p>',
            unsafe_allow_html=True
        )
    with btn_col:
        st.write("")
        if st.button("+ Create Alert", type="primary", use_container_width=True, key="open_create_alert_btn"):
            st.session_state.show_create_alert = not st.session_state.show_create_alert
            st.session_state.alert_success_msg = ""

    if st.session_state.alert_success_msg:
        st.markdown(
            f'<div style="background:#10B98115; border:1px solid #10B98145; border-radius:8px; '
            f'padding:10px 16px; display:flex; align-items:center; gap:10px; margin-top:4px; color:#10B981; font-size:0.82rem; font-weight:600;">'
            f'<span style="color:#10B981;">{_ICON_CHECK}</span> {st.session_state.alert_success_msg}</div>',
            unsafe_allow_html=True
        )

    st.write("")

    # ---- Create Alert form ----
    if st.session_state.show_create_alert:
        with st.expander("New Alert Rule", expanded=True):
            cf1, cf2 = st.columns(2)
            with cf1:
                new_name   = st.text_input("Alert Name", placeholder="e.g. Critical Spike Alert", key="new_alert_name")
                new_metric = st.selectbox("Metric", ["Critical Issues Count", "Negative Sentiment %", "Average Rating", "Topic Volume", "High/Critical %"], key="new_alert_metric")
                new_cond   = st.selectbox("Condition", ["Greater than", "Less than", "Increases by %", "Drops by %"], key="new_alert_cond")
                new_thresh = st.number_input("Threshold", min_value=0.0, step=0.5, key="new_alert_thresh")
            with cf2:
                new_severity = st.selectbox("Severity", ["Critical", "High", "Medium", "Low"], key="new_alert_severity")
                new_tier     = st.selectbox("Customer Tier", ["All", "Enterprise", "Premium", "Standard"], key="new_alert_tier")
                new_topic    = st.selectbox("Topic", ["All"] + sorted(df_full["Topic"].dropna().unique().tolist()), key="new_alert_topic")
                st.toggle("Enable notifications", value=True, key="new_alert_notify")
            ca_col1, ca_col2 = st.columns(2)
            with ca_col1:
                if st.button("Cancel", key="cancel_alert_btn", use_container_width=True, type="secondary"):
                    st.session_state.show_create_alert = False
                    st.rerun()
            with ca_col2:
                if st.button("Create Alert", key="confirm_alert_btn", use_container_width=True, type="primary"):
                    if new_name.strip():
                        new_id = max((r["id"] for r in st.session_state.alert_rules), default=0) + 1
                        cond_str = f"{new_metric} {new_cond.lower()} {new_thresh}"
                        if new_tier != "All":  cond_str += f" [{new_tier}]"
                        if new_topic != "All": cond_str += f" / {new_topic}"
                        st.session_state.alert_rules.insert(0, {
                            "id": new_id, "name": new_name.strip(), "condition": cond_str,
                            "severity": new_severity, "status": "Active", "last_triggered": "Never",
                        })
                        st.session_state.alert_success_msg = f'Alert "{new_name.strip()}" created successfully.'
                        st.session_state.show_create_alert = False
                        st.rerun()
                    else:
                        st.warning("Please enter an Alert Name.")

    # ---- SECTION 1 — Alert Overview KPI row ----
    active_alerts   = sum(1 for r in st.session_state.alert_rules if r["status"] == "Active")
    triggered_today = sum(1 for a in st.session_state.alert_activity if "Today" in a["time"])
    critical_alerts = sum(1 for r in st.session_state.alert_rules if r["severity"] == "Critical" and r["status"] == "Active")
    total_events    = len(st.session_state.alert_activity)
    resolved_events = sum(1 for a in st.session_state.alert_activity if a["status"] == "Resolved")
    success_rate    = round((resolved_events / total_events) * 100, 1) if total_events else 0.0

    def _alert_kpi(label, value, accent, icon_svg, sub=""):
        return (
            f'<div style="background:#0D1526; border:1px solid #1E293B; border-top:2px solid {accent}; '
            f'border-radius:10px; padding:14px 16px 12px 16px; '
            f'box-shadow:0 0 0 1px #1E293B, 0 4px 20px -4px {accent}18;">'
            f'  <div style="display:flex; justify-content:space-between; align-items:flex-start;">'
            f'    <div style="font-size:0.62rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.07em;">{label}</div>'
            f'    <div style="width:26px; height:26px; border-radius:7px; background:{accent}18; border:1px solid {accent}30; '
            f'display:flex; align-items:center; justify-content:center; color:{accent};">{icon_svg}</div>'
            f'  </div>'
            f'  <div style="font-size:1.65rem; font-weight:800; color:#F1F5F9; line-height:1.1; letter-spacing:-0.02em; margin-top:6px;">{value}</div>'
            f'  <div style="font-size:0.68rem; color:#64748B; margin-top:4px;">{sub}</div>'
            f'</div>'
        )

    ak1, ak2, ak3, ak4 = st.columns(4)
    with ak1:
        st.markdown(_alert_kpi("Active Alerts",     active_alerts,   "#38BDF8", _ICON_BELL,  "currently monitoring"),  unsafe_allow_html=True)
    with ak2:
        st.markdown(_alert_kpi("Triggered Today",   triggered_today, "#EF4444", _ICON_WARN,  "events fired today"),     unsafe_allow_html=True)
    with ak3:
        st.markdown(_alert_kpi("Critical Alerts",   critical_alerts, "#FF4757", _ICON_WARN,  "severity: critical"),     unsafe_allow_html=True)
    with ak4:
        st.markdown(_alert_kpi("Alert Success Rate",f"{success_rate}%","#10B981",_ICON_CHECK,"resolved / total events"),unsafe_allow_html=True)

    st.write("")

    # ---- SECTION 2 — Alert Rules table ----
    st.markdown(_section_hdr("Alert Rules"), unsafe_allow_html=True)
    hcols = st.columns([2.6, 3.5, 1.2, 1.2, 2.0, 1.8])
    for hc, ht in zip(hcols, ["Alert Name", "Condition", "Severity", "Status", "Last Triggered", "Actions"]):
        hc.markdown(f'<div style="font-size:0.65rem; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.05em; padding-bottom:6px; border-bottom:1px solid #1E293B;">{ht}</div>', unsafe_allow_html=True)
    st.write("")

    rules_to_delete = None
    for idx, rule in enumerate(st.session_state.alert_rules):
        rc = st.columns([2.6, 3.5, 1.2, 1.2, 2.0, 1.8])
        with rc[0]:
            st.markdown(f'<div style="font-size:0.82rem; font-weight:600; color:#E2E8F0; padding:6px 0;">{rule["name"]}</div>', unsafe_allow_html=True)
        with rc[1]:
            st.markdown(f'<div style="font-size:0.78rem; color:#94A3B8; padding:6px 0;">{rule["condition"]}</div>', unsafe_allow_html=True)
        with rc[2]:
            st.markdown(_severity_badge(rule["severity"]) + '<div style="margin-top:4px;"></div>', unsafe_allow_html=True)
        with rc[3]:
            st.markdown(_status_badge(rule["status"]) + '<div style="margin-top:4px;"></div>', unsafe_allow_html=True)
        with rc[4]:
            st.markdown(f'<div style="font-size:0.76rem; color:#64748B; padding:6px 0;">{rule["last_triggered"]}</div>', unsafe_allow_html=True)
        with rc[5]:
            b1, b2, b3 = st.columns(3)
            with b1:
                tog_label = "On" if rule["status"] == "Active" else "Off"
                if st.button(tog_label, key=f"tog_{rule['id']}_{idx}", use_container_width=True, type="secondary"):
                    st.session_state.alert_rules[idx]["status"] = "Paused" if rule["status"] == "Active" else "Active"
                    st.rerun()
            with b2:
                st.button("Edit", key=f"edit_{rule['id']}_{idx}", use_container_width=True, type="secondary")
            with b3:
                if st.button("Del", key=f"del_{rule['id']}_{idx}", use_container_width=True, type="secondary"):
                    rules_to_delete = idx
        st.markdown('<div style="border-bottom:1px solid #1E293B20; margin:2px 0;"></div>', unsafe_allow_html=True)

    if rules_to_delete is not None:
        st.session_state.alert_rules.pop(rules_to_delete)
        st.rerun()

    st.write("")

    # ---- SECTION 3 — Recent Alert Activity ----
    st.markdown(_section_hdr("Recent Alert Activity"), unsafe_allow_html=True)
    ah_cols = st.columns([2.4, 3.2, 1.2, 2.0, 1.2])
    for hc, ht in zip(ah_cols, ["Alert", "Trigger", "Severity", "Triggered At", "Status"]):
        hc.markdown(f'<div style="font-size:0.65rem; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.05em; padding-bottom:6px; border-bottom:1px solid #1E293B;">{ht}</div>', unsafe_allow_html=True)
    st.write("")

    for event in st.session_state.alert_activity:
        ac = st.columns([2.4, 3.2, 1.2, 2.0, 1.2])
        with ac[0]:
            st.markdown(f'<div style="font-size:0.8rem; font-weight:600; color:#E2E8F0; padding:5px 0;">{event["alert"]}</div>', unsafe_allow_html=True)
        with ac[1]:
            st.markdown(f'<div style="font-size:0.77rem; color:#94A3B8; padding:5px 0;">{event["trigger"]}</div>', unsafe_allow_html=True)
        with ac[2]:
            st.markdown(_severity_badge(event["severity"]) + "<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
        with ac[3]:
            st.markdown(f'<div style="font-size:0.76rem; color:#64748B; padding:5px 0;">{event["time"]}</div>', unsafe_allow_html=True)
        with ac[4]:
            if event["status"] == "Triggered":
                ebadge = ('<span style="background:#EF444420; color:#EF4444; border:1px solid #EF444445; '
                          'font-size:0.62rem; font-weight:700; padding:2px 8px; border-radius:20px;">Triggered</span>')
            else:
                ebadge = ('<span style="background:#10B98120; color:#10B981; border:1px solid #10B98145; '
                          'font-size:0.62rem; font-weight:700; padding:2px 8px; border-radius:20px;">Resolved</span>')
            st.markdown(ebadge + "<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
        st.markdown('<div style="border-bottom:1px solid #1E293B20; margin:2px 0;"></div>', unsafe_allow_html=True)

# ===========================================================================
# PAGE: SETTINGS
# ===========================================================================
elif page == "Settings":

    _SETTINGS_DEFAULTS = {
        "set_theme":                "Dark",
        "set_refresh_interval":     "30 seconds",
        "set_default_date_range":   "Last 30 days",
        "set_default_tier":         "All",
        "set_default_sentiment":    "All",
        "set_compact_dashboard":    False,
        "set_ai_summary":           True,
        "set_auto_insights":        True,
        "set_insight_sensitivity":  "Medium",
        "set_min_feedback":         10,
        "set_recommended_actions":  True,
        "set_show_reasoning":       True,
        "set_enable_alerts":        True,
        "set_email_notif":          True,
        "set_critical_alerts":      True,
        "set_neg_sentiment_alerts": True,
        "set_rating_drop_alerts":   True,
        "set_daily_digest":         False,
        "set_auto_refresh_data":    False,
        "set_export_format":        "CSV",
        "set_include_ai_in_report": True,
        "set_include_raw":          False,
        "set_compact_spacing":      False,
        "set_animations":           True,
        "set_dense_tables":         False,
    }
    for k, v in _SETTINGS_DEFAULTS.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if "settings_saved_msg" not in st.session_state:
        st.session_state.settings_saved_msg = ""

    # ---- Page header ----
    st.markdown(
        '<h2 style="margin:0; font-size:1.45rem; color:#F1F5F9; font-weight:800;">Platform Settings</h2>'
        '<p style="margin:3px 0 12px 0; font-size:0.82rem; color:#64748B;">Configure dashboard preferences, AI intelligence, alerts and data behaviour.</p>',
        unsafe_allow_html=True
    )
    if st.session_state.settings_saved_msg:
        st.markdown(
            f'<div style="background:#10B98115; border:1px solid #10B98145; border-radius:8px; '
            f'padding:10px 16px; display:flex; align-items:center; gap:10px; margin-bottom:12px; '
            f'color:#10B981; font-size:0.82rem; font-weight:600;">'
            f'<span>{_ICON_CHECK}</span> {st.session_state.settings_saved_msg}</div>',
            unsafe_allow_html=True
        )

    s1, s2 = st.columns(2)

    # ===== LEFT COLUMN =====
    with s1:
        # ---- GENERAL ----
        st.markdown(_card_open("#38BDF8"), unsafe_allow_html=True)
        st.markdown(_section_hdr("General Settings"), unsafe_allow_html=True)
        for _k, _lbl, _desc, _wtype, _opts in [
            ("set_refresh_interval",   "Dashboard Refresh Interval", "How often the dashboard auto-refreshes.",     "select", ["15 seconds","30 seconds","1 minute","5 minutes","Manual"]),
            ("set_default_date_range", "Default Date Range",         "Pre-selected range on page load.",            "select", ["Last 7 days","Last 30 days","Last 90 days","Custom"]),
            ("set_default_tier",       "Default Customer Tier",      "Applied automatically on startup.",           "select", ["All","Enterprise","Premium","Standard"]),
            ("set_default_sentiment",  "Default Sentiment",          "Pre-selected sentiment filter.",              "select", ["All","Positive","Neutral","Negative"]),
        ]:
            lc, wc = st.columns([2, 1.5])
            with lc:
                st.markdown(f'<div style="font-size:0.82rem; font-weight:600; color:#E2E8F0; margin-top:4px;">{_lbl}</div><div style="font-size:0.72rem; color:#475569;">{_desc}</div>', unsafe_allow_html=True)
            with wc:
                st.selectbox("", _opts, key=_k, label_visibility="collapsed")
            st.markdown('<div style="border-bottom:1px solid #1E293B30; margin:8px 0 6px 0;"></div>', unsafe_allow_html=True)
        lc, wc = st.columns([2, 1.5])
        with lc:
            st.markdown('<div style="font-size:0.82rem; font-weight:600; color:#E2E8F0; margin-top:4px;">Compact Dashboard</div><div style="font-size:0.72rem; color:#475569;">Reduce card padding and chart height.</div>', unsafe_allow_html=True)
        with wc:
            st.toggle("", key="set_compact_dashboard", label_visibility="collapsed")
        st.markdown(_card_close, unsafe_allow_html=True)

        # ---- ALERT PREFERENCES ----
        st.markdown(_card_open("#EA580C"), unsafe_allow_html=True)
        st.markdown(_section_hdr("Alert Preferences"), unsafe_allow_html=True)
        for _k, _lbl, _desc in [
            ("set_enable_alerts",        "Enable Alerts",             "Master switch for all alert monitoring."),
            ("set_email_notif",          "Email Notifications",       "Receive alerts by email when triggered."),
            ("set_critical_alerts",      "Critical Issue Alerts",     "Notify when critical issue count spikes."),
            ("set_neg_sentiment_alerts", "Negative Sentiment Alerts", "Notify when negative % exceeds threshold."),
            ("set_rating_drop_alerts",   "Rating Drop Alerts",        "Notify when average rating falls below 3.0."),
            ("set_daily_digest",         "Daily Alert Digest",        "Receive a summary of all alerts each morning."),
        ]:
            lc, wc = st.columns([2, 1.5])
            with lc:
                st.markdown(f'<div style="font-size:0.82rem; font-weight:600; color:#E2E8F0; margin-top:4px;">{_lbl}</div><div style="font-size:0.72rem; color:#475569;">{_desc}</div>', unsafe_allow_html=True)
            with wc:
                st.toggle("", key=_k, label_visibility="collapsed")
            st.markdown('<div style="border-bottom:1px solid #1E293B30; margin:8px 0 6px 0;"></div>', unsafe_allow_html=True)
        st.markdown(_card_close, unsafe_allow_html=True)

        # ---- APPEARANCE ----
        st.markdown(_card_open("#8B5CF6"), unsafe_allow_html=True)
        st.markdown(_section_hdr("Appearance"), unsafe_allow_html=True)
        lc, wc = st.columns([2, 1.5])
        with lc:
            st.markdown('<div style="font-size:0.82rem; font-weight:600; color:#E2E8F0; margin-top:4px;">Theme</div><div style="font-size:0.72rem; color:#475569;">Select dashboard theme.</div>', unsafe_allow_html=True)
        with wc:
            st.selectbox("", ["Dark", "Light"], key="set_theme", label_visibility="collapsed")
        st.markdown('<div style="border-bottom:1px solid #1E293B30; margin:8px 0 6px 0;"></div>', unsafe_allow_html=True)
        for _k, _lbl, _desc in [
            ("set_compact_spacing", "Compact Spacing", "Reduce whitespace between dashboard sections."),
            ("set_animations",      "Animations",      "Enable micro-animations on hover and transitions."),
            ("set_dense_tables",    "Dense Tables",    "Show more rows per screen in data tables."),
        ]:
            lc, wc = st.columns([2, 1.5])
            with lc:
                st.markdown(f'<div style="font-size:0.82rem; font-weight:600; color:#E2E8F0; margin-top:4px;">{_lbl}</div><div style="font-size:0.72rem; color:#475569;">{_desc}</div>', unsafe_allow_html=True)
            with wc:
                st.toggle("", key=_k, label_visibility="collapsed")
            st.markdown('<div style="border-bottom:1px solid #1E293B30; margin:8px 0 6px 0;"></div>', unsafe_allow_html=True)
        st.markdown(_card_close, unsafe_allow_html=True)

    # ===== RIGHT COLUMN =====
    with s2:
        # ---- AI INTELLIGENCE ----
        st.markdown(_card_open("#8B5CF6"), unsafe_allow_html=True)
        st.markdown(_section_hdr("AI Intelligence"), unsafe_allow_html=True)
        for _k, _lbl, _desc in [
            ("set_ai_summary",          "AI Executive Summary", "Show AI-generated executive briefing on Overview."),
            ("set_auto_insights",       "Automatic Insights",   "Automatically generate insights on data load."),
            ("set_recommended_actions", "Recommended Actions",  "Display recommended strategic actions from AI."),
            ("set_show_reasoning",      "Show AI Reasoning",    "Include evidence and reasoning in AI output."),
        ]:
            lc, wc = st.columns([2, 1.5])
            with lc:
                st.markdown(f'<div style="font-size:0.82rem; font-weight:600; color:#E2E8F0; margin-top:4px;">{_lbl}</div><div style="font-size:0.72rem; color:#475569;">{_desc}</div>', unsafe_allow_html=True)
            with wc:
                st.toggle("", key=_k, label_visibility="collapsed")
            st.markdown('<div style="border-bottom:1px solid #1E293B30; margin:8px 0 6px 0;"></div>', unsafe_allow_html=True)
        lc, wc = st.columns([2, 1.5])
        with lc:
            st.markdown('<div style="font-size:0.82rem; font-weight:600; color:#E2E8F0; margin-top:4px;">Insight Sensitivity</div><div style="font-size:0.72rem; color:#475569;">Low = only critical signals. High = all patterns.</div>', unsafe_allow_html=True)
        with wc:
            st.select_slider("", options=["Low", "Medium", "High"], key="set_insight_sensitivity", label_visibility="collapsed")
        st.markdown('<div style="border-bottom:1px solid #1E293B30; margin:8px 0 6px 0;"></div>', unsafe_allow_html=True)
        lc, wc = st.columns([2, 1.5])
        with lc:
            st.markdown('<div style="font-size:0.82rem; font-weight:600; color:#E2E8F0; margin-top:4px;">Minimum Feedback Count</div><div style="font-size:0.72rem; color:#475569;">Minimum records required to generate AI insights.</div>', unsafe_allow_html=True)
        with wc:
            st.number_input("", min_value=1, max_value=500, step=1, key="set_min_feedback", label_visibility="collapsed")
        st.markdown(_card_close, unsafe_allow_html=True)

        # ---- DATA & EXPORT ----
        st.markdown(_card_open("#10B981"), unsafe_allow_html=True)
        st.markdown(_section_hdr("Data & Export"), unsafe_allow_html=True)
        lc, wc = st.columns([2, 1.5])
        with lc:
            st.markdown('<div style="font-size:0.82rem; font-weight:600; color:#E2E8F0; margin-top:4px;">Auto Refresh Data</div><div style="font-size:0.72rem; color:#475569;">Automatically re-run the pipeline on load.</div>', unsafe_allow_html=True)
        with wc:
            st.toggle("", key="set_auto_refresh_data", label_visibility="collapsed")
        st.markdown('<div style="border-bottom:1px solid #1E293B30; margin:8px 0 6px 0;"></div>', unsafe_allow_html=True)
        lc, wc = st.columns([2, 1.5])
        with lc:
            st.markdown('<div style="font-size:0.82rem; font-weight:600; color:#E2E8F0; margin-top:4px;">Default Export Format</div><div style="font-size:0.72rem; color:#475569;">Format used when exporting reports.</div>', unsafe_allow_html=True)
        with wc:
            st.selectbox("", ["CSV", "Excel", "PDF"], key="set_export_format", label_visibility="collapsed")
        st.markdown('<div style="border-bottom:1px solid #1E293B30; margin:8px 0 6px 0;"></div>', unsafe_allow_html=True)
        for _k, _lbl, _desc in [
            ("set_include_ai_in_report", "Include AI Insights in Report", "Bundle AI briefing in exported reports."),
            ("set_include_raw",          "Include Raw Feedback",          "Include raw feedback text in exports."),
        ]:
            lc, wc = st.columns([2, 1.5])
            with lc:
                st.markdown(f'<div style="font-size:0.82rem; font-weight:600; color:#E2E8F0; margin-top:4px;">{_lbl}</div><div style="font-size:0.72rem; color:#475569;">{_desc}</div>', unsafe_allow_html=True)
            with wc:
                st.toggle("", key=_k, label_visibility="collapsed")
            st.markdown('<div style="border-bottom:1px solid #1E293B30; margin:8px 0 6px 0;"></div>', unsafe_allow_html=True)
        st.write("")
        de1, de2 = st.columns(2)
        with de1:
            st.download_button(
                label="Download CSV", data=df.to_csv(index=False).encode("utf-8"),
                file_name="feedback_iq_export.csv", mime="text/csv",
                use_container_width=True, key="settings_dl_csv", type="secondary"
            )
        with de2:
            st.download_button(
                label="Export Report",
                data=json.dumps(insights, indent=2).encode("utf-8") if insights else b"{}",
                file_name="feedback_iq_report.json", mime="application/json",
                use_container_width=True, key="settings_dl_report", type="primary"
            )
        st.markdown(_card_close, unsafe_allow_html=True)

    # ---- Bottom action bar ----
    st.write("")
    st.markdown('<div style="border-top:1px solid #1E293B; padding-top:16px; margin-top:4px;"></div>', unsafe_allow_html=True)
    bar1, bar2, bar3 = st.columns([3, 1, 1])
    with bar2:
        def _reset_settings_cb():
            for k, v in _SETTINGS_DEFAULTS.items():
                st.session_state[k] = v
            st.session_state.settings_saved_msg = "Settings reset to defaults."
            
        st.button("Reset to Defaults", on_click=_reset_settings_cb, use_container_width=True, type="secondary", key="settings_reset_btn")
    with bar3:
        if st.button("Save Settings", use_container_width=True, type="primary", key="settings_save_btn"):
            st.session_state.settings_saved_msg = "Settings saved successfully for this session."
            st.rerun()
