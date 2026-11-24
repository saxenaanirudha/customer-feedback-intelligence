"""Negative, Failure, and Concurrency test suite."""

import concurrent.futures
from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src import classifier, preprocessing, priority


class TestNegativeAndFailureScenarios:
    """Simulates malformed data, edge cases, and failure modes."""

    def test_failure_on_extremely_long_feedback_text(self):
        """Verify classifier and priority engine handle 50,000 character inputs without crashing."""
        huge_text = "This application is too slow! " * 2000
        cls = classifier.FeedbackClassifier(api_key=None)
        res = cls.classify_single_heuristic(huge_text, rating=1)

        assert res["Sentiment"] == "Negative"
        assert res["Topic"] == "Performance"
        assert res["Urgency"] in ["High", "Critical"]

    def test_failure_on_unicode_and_emoji_characters(self):
        """Verify pipeline handles multi-byte unicode, emojis, and right-to-left text."""
        unicode_text = "🔥 Super slow crash 🚀! приложение зависает 💥! חוויה גרועה מאוד"
        df = pd.DataFrame([{
            "FeedbackID": "UNI_01",
            "Text": unicode_text,
            "Rating": 1,
            "Date": "2026-03-01",
            "CustomerType": "Enterprise",
        }])

        cleaned = preprocessing.clean_data(df)
        assert len(cleaned) == 1

        cls = classifier.FeedbackClassifier(api_key=None)
        classified = cls.classify_feedback(cleaned, show_progress=False)
        assert len(classified) == 1

        prioritized = priority.add_priority_columns(classified)
        assert len(prioritized) == 1
        assert prioritized.iloc[0]["PriorityScore"] >= 80

    def test_corrupted_csv_output_file_handling(self, temp_dir: Path):
        """Verify behavior when intermediate CSV output file is corrupted."""
        corrupted_file = temp_dir / "corrupted.csv"
        corrupted_file.write_text("FeedbackID,Text\nF1,OnlyTwoCols\n", encoding="utf-8")

        with pytest.raises(ValueError, match="Missing required columns"):
            df = pd.read_csv(corrupted_file)
            preprocessing.validate_data(df)

    def test_concurrent_heuristic_classification_thread_safety(self, sample_cleaned_data: pd.DataFrame):
        """Verify that concurrent threads can classify records simultaneously without state corruption."""
        cls = classifier.FeedbackClassifier(api_key=None)

        def worker(row_text: str, row_rating: int):
            return cls.classify_single_heuristic(row_text, row_rating)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(worker, f"Issue #{i} with slow board load crash", 1)
                for i in range(20)
            ]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == 20
        assert all(r["Topic"] == "Performance" for r in results)
        assert all(r["Sentiment"] == "Negative" for r in results)

    def test_concurrent_csv_writing_race_condition_simulation(self, temp_dir: Path):
        """Simulate race conditions when multiple workers write to the same output CSV."""
        shared_output = temp_dir / "shared_output.csv"

        def write_worker(worker_id: int):
            df = pd.DataFrame([{"Worker": worker_id, "Data": f"Run_{worker_id}"}])
            df.to_csv(shared_output, index=False)
            return True

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(write_worker, i) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(results)
        # Shared file exists, but last writer won without file-level locking
        assert shared_output.exists()
