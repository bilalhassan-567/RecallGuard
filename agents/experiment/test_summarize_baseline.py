"""Run: python -m unittest test_summarize_baseline -v"""
import unittest

from summarize_baseline import compute_baseline_metrics

GROUND_TRUTH = {
    "true_positives": [
        {"line_text": "TP LINE A", "recall_number": "R-A"},
        {"line_text": "TP LINE B", "recall_number": "R-B"},
    ]
}


def _result(recall_id, picked, time_s=30.0):
    return {"recallId": recall_id, "timeToDetectionSeconds": time_s, "pickedLines": picked}


class TestComputeBaselineMetrics(unittest.TestCase):
    def test_correct_pick(self):
        m = compute_baseline_metrics([_result("R-A", ["TP LINE A"])], GROUND_TRUTH)
        self.assertEqual(m["detected"], 1)
        self.assertEqual(m["missed"], 0)
        self.assertEqual(m["precision"], 1.0)

    def test_no_pick_is_missed(self):
        m = compute_baseline_metrics([_result("R-A", [])], GROUND_TRUTH)
        self.assertEqual(m["missed"], 1)
        self.assertEqual(m["detected"], 0)

    def test_wrong_pick_only_is_missed_and_false_positive(self):
        m = compute_baseline_metrics([_result("R-A", ["SOME OTHER LINE"])], GROUND_TRUTH)
        self.assertEqual(m["missed"], 1)
        self.assertEqual(m["falsePositives"], 1)

    def test_correct_plus_extra_pick_counts_both(self):
        m = compute_baseline_metrics([_result("R-A", ["TP LINE A", "SOME OTHER LINE"])], GROUND_TRUTH)
        self.assertEqual(m["detected"], 1)
        self.assertEqual(m["falsePositives"], 1)
        self.assertEqual(m["precision"], 0.5)

    def test_empty_results(self):
        m = compute_baseline_metrics([], GROUND_TRUTH)
        self.assertEqual(m["n"], 0)
        self.assertIsNone(m["recall"])
        self.assertIsNone(m["precision"])


if __name__ == "__main__":
    unittest.main()
