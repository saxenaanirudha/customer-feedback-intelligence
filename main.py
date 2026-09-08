# =============================================================================
# FILE PURPOSE & OVERVIEW
# =============================================================================
# This file (`main.py`) is the main entry point (runner) for the Customer Feedback
# Intelligence pipeline. It orchestrates the backend data processing steps in order:
# 1. Loads and cleans raw data (using preprocessing.py)
# 2. Uses AI to classify sentiment and topics (using classifier.py)
# 3. Computes a business priority score (using priority.py)
#
# FUNCTION EXPLANATIONS:
# -----------------------------------------------------------------------------
# - run_pipeline():
#   This is the core function that runs the 3 stages mentioned above. It reads the
#   CSV file, passes data through the cleaner, sends it to the AI classifier, and
#   then generates priority scores. Finally, it prints a summary report to the console.
#
# - main():
#   This function handles running the script from the command line. It parses command-line
#   arguments (like --full or --priority-only) and calls `run_pipeline` accordingly.
# =============================================================================

"""Customer Feedback Intelligence System - Main Pipeline Runner (Steps 1 to 4).

Orchestrates:
1. Data Preprocessing & Cleaning (output/cleaned_feedback.csv)
2. AI/LLM Classification (output/classified_feedback.csv)
3. Business Priority Scoring Engine (output/prioritized_feedback.csv)
"""

import argparse
import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from src.preprocessing import (
    load_data,
    validate_data,
    clean_data,
    get_data_quality_summary,
    print_data_quality_report,
)
from src.classifier import (
    FeedbackClassifier,
    validate_classified_data,
)
from src.priority import (
    add_priority_columns,
    validate_priority_inputs,
)


def run_pipeline(force_reclassify: bool = False, priority_only: bool = False) -> None:
    """Execute the end-to-end feedback intelligence and priority scoring pipeline.

    Args:
        force_reclassify (bool): If True, forces reprocessing and reclassification from scratch.
        priority_only (bool): If True, computes priority directly from existing classified CSV.
    """
    print("=" * 72)
    print("   CUSTOMER FEEDBACK INTELLIGENCE SYSTEM (v2.0) - END-TO-END PIPELINE   ")
    print("=" * 72)

    # 1. Define paths
    input_path = BASE_DIR / "data" / "feedback.csv"
    output_dir = BASE_DIR / "output"
    cleaned_output_path = output_dir / "cleaned_feedback.csv"
    classified_output_path = output_dir / "classified_feedback.csv"
    prioritized_output_path = output_dir / "prioritized_feedback.csv"
    error_log_path = output_dir / "priority_errors.log"

    output_dir.mkdir(parents=True, exist_ok=True)

    df_classified: pd.DataFrame

    try:
        # Check if we can reuse existing classified dataset for fast priority scoring
        can_reuse_classified = classified_output_path.exists() and not force_reclassify

        if priority_only or can_reuse_classified:
            print(f"\n[INFO] Loading existing classified dataset from: output/classified_feedback.csv")
            df_classified = pd.read_csv(classified_output_path)
            validate_classified_data(df_classified)
            print(f"       Loaded {len(df_classified)} classified records.")
        else:
            # -------------------------------------------------------------
            # STAGE 1: DATA PREPROCESSING
            # -------------------------------------------------------------
            print("\n" + "-" * 72)
            print(" [STAGE 1/3] DATA PREPROCESSING & CLEANING")
            print("-" * 72)

            print(f"\n[1/4] Loading raw feedback dataset from: data/feedback.csv")
            df_raw = load_data(input_path)
            print(f"      Loaded {len(df_raw)} raw feedback entries.")

            print(f"\n[2/4] Validating schema...")
            validate_data(df_raw)
            print(f"      Schema validation passed.")

            print(f"\n[3/4] Cleaning data & filtering anomalies...")
            df_cleaned = clean_data(df_raw)
            summary = get_data_quality_summary(df_raw, df_cleaned)
            print_data_quality_report(summary)

            print(f"[4/4] Saving cleaned dataset to: output/cleaned_feedback.csv")
            df_cleaned.to_csv(cleaned_output_path, index=False)

            # -------------------------------------------------------------
            # STAGE 2: AI / LLM CLASSIFICATION
            # -------------------------------------------------------------
            print("\n" + "-" * 72)
            print(" [STAGE 2/3] AI/LLM CLASSIFICATION (Sentiment, Topic, Urgency)")
            print("-" * 72)

            classifier = FeedbackClassifier()
            print(f"\n[1/3] Classifying customer feedback...")
            df_classified = classifier.classify_feedback(df_cleaned, show_progress=True)

            print(f"\n[2/3] Validating classified categories...")
            validate_classified_data(df_classified)
            print(f"      Validation passed!")

            print(f"\n[3/3] Saving classified dataset to: output/classified_feedback.csv")
            df_classified.to_csv(classified_output_path, index=False)

        # -------------------------------------------------------------
        # STAGE 3: BUSINESS PRIORITY SCORING ENGINE (Step 4)
        # -------------------------------------------------------------
        print("\n" + "-" * 72)
        print(" [STAGE 3/3] BUSINESS PRIORITY SCORING ENGINE")
        print("-" * 72)

        print(f"\n[1/3] Validating classification inputs for priority computation...")
        errors = validate_priority_inputs(df_classified, error_log_path=error_log_path)
        if errors:
            print(f"      [Notice] {len(errors)} anomalies logged to: output/priority_errors.log")
        else:
            print(f"      Validation check: 0 errors detected.")

        print(f"\n[2/3] Computing PriorityScore (0-100), PriorityLevel & PriorityReason...")
        df_prioritized = add_priority_columns(df_classified, error_log_path=error_log_path)

        print(f"\n[3/3] Saving prioritized dataset to: output/prioritized_feedback.csv")
        df_prioritized.to_csv(prioritized_output_path, index=False)

        # -------------------------------------------------------------
        # PRIORITY SUMMARY & METRICS DISPLAY
        # -------------------------------------------------------------
        total_records = len(df_prioritized)
        avg_score = df_prioritized["PriorityScore"].mean()

        print("\n" + "=" * 72)
        print("                        PRIORITY SCORING SUMMARY                      ")
        print("=" * 72)
        print(f"\n  • Total Records Processed:   {total_records}")
        print(f"  • Average Priority Score:    {avg_score:.1f} / 100")

        # Priority Level Distribution
        print("\n  >> Priority Level Distribution:")
        level_order = ["Critical Priority", "High Priority", "Medium Priority", "Low Priority"]
        level_icons = {
            "Critical Priority": "[!!!]",
            "High Priority": "[!!] ",
            "Medium Priority": "[!]  ",
            "Low Priority": "[ok] ",
        }

        for lvl in level_order:
            cnt = (df_prioritized["PriorityLevel"] == lvl).sum()
            pct = (cnt / total_records) * 100
            icon = level_icons.get(lvl, "•")
            bar = "#" * int(pct / 3)
            print(f"      {icon} {lvl:<18}: {cnt:>3} ({pct:>5.1f}%)  {bar}")

        # Top Priority Topics in High & Critical
        print("\n  >> Top Topics in High & Critical Priority:")
        high_crit_df = df_prioritized[df_prioritized["PriorityLevel"].isin(["Critical Priority", "High Priority"])]
        topic_counts = high_crit_df["Topic"].value_counts()
        for rank, (topic, cnt) in enumerate(topic_counts.head(5).items(), 1):
            pct = (cnt / len(high_crit_df)) * 100
            print(f"      {rank}. {topic:<18}: {cnt:>3} issues ({pct:>5.1f}%)")

        # -------------------------------------------------------------
        # DISPLAY TOP 10 HIGHEST-PRIORITY FEEDBACK RECORDS
        # -------------------------------------------------------------
        print("\n" + "=" * 72)
        print("             TOP 10 HIGHEST-PRIORITY ACTIONABLE ISSUES                ")
        print("=" * 72)

        # Map Urgency to numeric rank for multi-level sorting
        urgency_rank = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        df_sorted = df_prioritized.copy()
        df_sorted["_urg_rank"] = df_sorted["Urgency"].map(urgency_rank)
        df_sorted = df_sorted.sort_values(
            by=["PriorityScore", "_urg_rank", "Date"],
            ascending=[False, False, False],
        ).drop(columns=["_urg_rank"])

        top_10 = df_sorted.head(10)

        for rank, (_, row) in enumerate(top_10.iterrows(), 1):
            icon = level_icons.get(row['PriorityLevel'], '•')
            print(f"\n{rank:>2}. [{row['FeedbackID']}] Score: {row['PriorityScore']:>3} | {icon} {row['PriorityLevel']} | Tier: {row['CustomerType']} | Topic: {row['Topic']} | Rating: *{row['Rating']}")
            print(f"    Text:   \"{row['Text']}\"")
            print(f"    Reason: {row['PriorityReason']}")

        print("\n" + "=" * 72)
        print(" Output saved successfully: output/prioritized_feedback.csv")
        print("=" * 72 + "\n")

    except FileNotFoundError as e:
        print(f"\n[ERROR] File Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n[ERROR] Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Pipeline Error: {e}")
        sys.exit(1)


def main():
    """Parse CLI arguments and launch pipeline."""
    parser = argparse.ArgumentParser(description="Customer Feedback Intelligence Pipeline")
    parser.add_argument("--full", action="store_true", help="Force full reprocessing & reclassification")
    parser.add_argument("--priority-only", action="store_true", help="Run only Priority Scoring on classified CSV")
    args = parser.parse_args()

    run_pipeline(force_reclassify=args.full, priority_only=args.priority_only)


if __name__ == "__main__":
    main()
