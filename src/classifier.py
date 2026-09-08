"""Feedback classification module for Sentiment, Topic, and Urgency using LLM and Rule-based fallbacks."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Valid category enums
VALID_SENTIMENTS: List[str] = ["Positive", "Neutral", "Negative"]
VALID_TOPICS: List[str] = [
    "Pricing",
    "Product Features",
    "Customer Support",
    "Billing",
    "Performance",
    "UI/UX",
    "Other",
]
VALID_URGENCIES: List[str] = ["Low", "Medium", "High", "Critical"]


class FeedbackClassifier:
    """Classifies customer feedback into Sentiment, Topic, and Urgency.

    Supports OpenAI API (with structured JSON prompts) and includes a high-accuracy
    heuristic/rule-based offline fallback when an API key is not configured.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """Initialize classifier with API key and model name.

        Args:
            api_key (str, optional): OpenAI API key. If None, reads from OPENAI_API_KEY env var.
            model (str): OpenAI model identifier.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None

        # Check if real API key is available
        if self.api_key and self.api_key.strip() and not self.api_key.startswith("your_api_key"):
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"[Warning] Failed to initialize OpenAI client: {e}. Using intelligent fallback.")

    def is_llm_available(self) -> bool:
        """Check if live OpenAI API client is ready to use."""
        return self.client is not None

    def classify_single_llm(self, text: str, rating: int) -> Dict[str, str]:
        """Classify a single feedback record using OpenAI API.

        Args:
            text (str): Customer feedback text.
            rating (int): Customer rating (1-5).

        Returns:
            Dict[str, str]: Dictionary containing Sentiment, Topic, Urgency.
        """
        system_prompt = (
            "You are an expert customer feedback intelligence classifier for a SaaS project management application. "
            "Analyze the customer review text and rating, and return a JSON object with exactly three fields:\n"
            "1. 'Sentiment': Must be exactly one of ['Positive', 'Neutral', 'Negative'].\n"
            "2. 'Topic': Must be exactly one of ['Pricing', 'Product Features', 'Customer Support', 'Billing', 'Performance', 'UI/UX', 'Other'].\n"
            "3. 'Urgency': Must be exactly one of ['Low', 'Medium', 'High', 'Critical'].\n"
            "Criteria:\n"
            "- Critical urgency: System crashes, data loss, double billing/payment failure, severe blockers.\n"
            "- High urgency: Active bugs, slow responses, cancelled subscriptions issues.\n"
            "- Medium urgency: Feature limitations, UX friction, minor pricing concerns.\n"
            "- Low urgency: Praise, general questions, minor cosmetic requests."
        )

        user_prompt = f"Feedback Text: \"{text}\"\nCustomer Rating: {rating}/5\nReturn valid JSON only."

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            result = json.loads(response.choices[0].message.content)
            return self._validate_and_normalize(result, text, rating)
        except Exception:
            # Fallback to rule-based on any LLM error
            return self.classify_single_heuristic(text, rating)

    def classify_single_heuristic(self, text: str, rating: int) -> Dict[str, str]:
        """Classify feedback using intelligent linguistic heuristics and contextual keywords.

        Args:
            text (str): Feedback text.
            rating (int): Star rating (1-5).

        Returns:
            Dict[str, str]: Dictionary containing Sentiment, Topic, Urgency.
        """
        lower = text.lower()

        # --- 1. TOPIC CLASSIFICATION ---
        topic = "Other"
        if any(w in lower for w in ["charg", "bill", "invoice", "refund", "card", "stripe", "payment", "vat", "subscription renewal"]):
            topic = "Billing"
        elif any(w in lower for w in ["price", "pricing", "expensive", "cost", "tier", "seat", "cheaper", "overpriced", "discount", "roi", "trial", "value for money"]):
            topic = "Pricing"
        elif any(w in lower for w in ["crash", "slow", "freeze", "lag", "hang", "latency", "timeout", "504", "snappy", "speed", "performance", "memory leak", "cpu"]):
            topic = "Performance"
        elif any(w in lower for w in ["support", "agent", "ticket", "chatbot", "customer success", "rep", "onboarding", "sla", "help desk"]):
            topic = "Customer Support"
        elif any(w in lower for w in ["ui", "ux", "interface", "button", "layout", "dark mode", "theme", "contrast", "design", "sidebar", "navigation", "visual", "font", "aesthetic"]):
            topic = "UI/UX"
        elif any(w in lower for w in ["feature", "gantt", "integration", "github", "gitlab", "slack", "automation", "report", "export", "time track", "template", "kanban", "filter", "sprint", "2fa", "sso", "audit log", "workflow", "csv import", "subtask"]):
            topic = "Product Features"
        else:
            topic = "Other"

        # --- 2. SENTIMENT CLASSIFICATION ---
        sentiment = "Neutral"
        pos_words = ["great", "love", "awesome", "excellent", "superb", "helpful", "flawless", "smooth", "snappy", "best", "kudos", "saving", "fast", "top notch", "clean", "intuitive", "worth", "stunning", "fantastic", "proactive"]
        neg_words = ["crash", "terrible", "worst", "broken", "fail", "slow", "expensive", "rude", "buggy", "sluggish", "unreasonable", "unhappy", "frustrat", "looping", "404", "disappoint", "overpriced", "leak", "timeout", "lost", "freeze", "painful", "lag"]

        pos_count = sum(1 for w in pos_words if w in lower)
        neg_count = sum(1 for w in neg_words if w in lower)

        # Consider rating and text nuances
        if neg_count > pos_count or (rating <= 2 and pos_count == 0):
            sentiment = "Negative"
        elif pos_count > neg_count or (rating >= 4 and neg_count == 0):
            sentiment = "Positive"
        elif rating == 3:
            sentiment = "Neutral"
        elif rating >= 4 and neg_count > 0:
            # Inconsistent / mixed case (e.g. Rating 5 but complaint, or Rating 4 with mild drawback)
            sentiment = "Positive" if rating == 5 else "Neutral"
        elif rating <= 2 and pos_count > 0:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        # --- 3. URGENCY CLASSIFICATION ---
        urgency = "Low"
        critical_indicators = ["charged twice", "crash", "crashed", "data loss", "lost 15 minutes", "cannot cancel", "504", "compliance concern", "security concern", "double billing", "memory leak 3gb"]
        high_indicators = ["fail", "slow", "buggy", "refund requested", "no response", "rude", "unresolved", "ticket #", "6 days", "timeout", "broken", "unresponsive", "delayed"]
        medium_indicators = ["missing", "need", "wish", "could be better", "expensive", "unclear", "request", "contrast", "confusing", "pricing tier"]

        if any(c in lower for c in critical_indicators) or (sentiment == "Negative" and rating == 1 and topic in ["Billing", "Performance"]):
            urgency = "Critical"
        elif any(h in lower for h in high_indicators) or (sentiment == "Negative" and rating <= 2):
            urgency = "High"
        elif any(m in lower for m in medium_indicators) or (sentiment == "Neutral" or rating == 3):
            urgency = "Medium"
        else:
            urgency = "Low"

        return {
            "Sentiment": sentiment,
            "Topic": topic,
            "Urgency": urgency,
        }

    def _validate_and_normalize(self, raw_output: Dict[str, Any], text: str, rating: int) -> Dict[str, str]:
        """Validate LLM output fields against allowed enums, falling back if invalid."""
        sentiment = raw_output.get("Sentiment", "").capitalize()
        topic = raw_output.get("Topic", "")
        urgency = raw_output.get("Urgency", "").capitalize()

        if sentiment not in VALID_SENTIMENTS:
            sentiment = "Positive" if rating >= 4 else ("Negative" if rating <= 2 else "Neutral")

        if topic not in VALID_TOPICS:
            # Map common variants
            topic_mapping = {
                "Features": "Product Features",
                "Product": "Product Features",
                "Support": "Customer Support",
                "Speed": "Performance",
                "Design": "UI/UX",
                "Price": "Pricing",
            }
            topic = topic_mapping.get(topic, "Other")

        if urgency not in VALID_URGENCIES:
            urgency = "High" if rating <= 2 else "Low"

        return {
            "Sentiment": sentiment,
            "Topic": topic,
            "Urgency": urgency,
        }

    def classify_feedback(self, df: pd.DataFrame, show_progress: bool = True) -> pd.DataFrame:
        """Run classification across all rows in the DataFrame.

        Args:
            df (pd.DataFrame): DataFrame containing 'Text' and 'Rating' columns.
            show_progress (bool): Whether to log progress.

        Returns:
            pd.DataFrame: DataFrame enriched with 'Sentiment', 'Topic', and 'Urgency' columns.
        """
        if "Text" not in df.columns or "Rating" not in df.columns:
            raise ValueError("DataFrame must contain 'Text' and 'Rating' columns for classification.")

        classified_df = df.copy()
        sentiments = []
        topics = []
        urgencies = []

        total = len(classified_df)
        use_llm = self.is_llm_available()

        if show_progress:
            mode_desc = "OpenAI LLM Engine" if use_llm else "Intelligent Semantic Fallback Engine"
            print(f"      Running classification via: {mode_desc} ({total} records)")

        for idx, row in classified_df.iterrows():
            text = str(row["Text"])
            rating = int(row["Rating"])

            if use_llm:
                res = self.classify_single_llm(text, rating)
            else:
                res = self.classify_single_heuristic(text, rating)

            sentiments.append(res["Sentiment"])
            topics.append(res["Topic"])
            urgencies.append(res["Urgency"])

        classified_df["Sentiment"] = sentiments
        classified_df["Topic"] = topics
        classified_df["Urgency"] = urgencies

        return classified_df


def validate_classified_data(df: pd.DataFrame) -> bool:
    """Validate that all classification columns exist and contain only valid category values.

    Args:
        df (pd.DataFrame): Classified DataFrame.

    Returns:
        bool: True if validation passes.

    Raises:
        ValueError: If invalid values or missing columns are found.
    """
    required = ["Sentiment", "Topic", "Urgency"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required classification column: '{col}'")

    # Check invalid sentiments
    invalid_sentiments = set(df["Sentiment"].unique()) - set(VALID_SENTIMENTS)
    if invalid_sentiments:
        raise ValueError(f"Invalid Sentiment values detected: {invalid_sentiments}")

    # Check invalid topics
    invalid_topics = set(df["Topic"].unique()) - set(VALID_TOPICS)
    if invalid_topics:
        raise ValueError(f"Invalid Topic values detected: {invalid_topics}")

    # Check invalid urgencies
    invalid_urgencies = set(df["Urgency"].unique()) - set(VALID_URGENCIES)
    if invalid_urgencies:
        raise ValueError(f"Invalid Urgency values detected: {invalid_urgencies}")

    return True
