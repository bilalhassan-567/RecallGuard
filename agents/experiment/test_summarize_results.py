"""Offline tests for the scoring logic — synthetic results, no network/Gemini needed.
Deliberately tests the definitions in summarize_results.py's own docstring, since those
distinctions (missed vs. rejected-but-present, dangerous vs. soft false positive) are
exactly the kind of thing that's easy to get subtly wrong.

Run: python -m unittest test_summarize_results -v
"""
import unittest

from summarize_results import compute_metrics

GROUND_TRUTH = {
    "true_positives": [
        {"line_text": "TP LINE A", "recall_number": "R-A"},
        {"line_text": "TP LINE B", "recall_number": "R-B"},
    ]
}


def _result(recall_id, matches, time_s=10.0):
    return {"recallId": recall_id, "timeToDetectionSeconds": time_s, "matches": matches}


class TestComputeMetrics(unittest.TestCase):
    def test_correctly_auto_actioned(self):
        results = [_result("R-A", [{"lineText": "TP LINE A", "confidenceScore": 95, "status": "auto_actioned"}])]
        m = compute_metrics(results, GROUND_TRUTH)
        self.assertEqual(m["detected"], 1)
        self.assertEqual(m["correctlyAutoActioned"], 1)
        self.assertEqual(m["missed"], 0)
        self.assertEqual(m["precision"], 1.0)

    def test_correctly_escalated_counts_as_detected_not_missed(self):
        results = [_result("R-A", [{"lineText": "TP LINE A", "confidenceScore": 55, "status": "pending_review"}])]
        m = compute_metrics(results, GROUND_TRUTH)
        self.assertEqual(m["detected"], 1)
        self.assertEqual(m["correctlyEscalated"], 1)
        self.assertEqual(m["correctlyAutoActioned"], 0)
        self.assertEqual(m["missed"], 0)

    def test_rejected_true_positive_counts_as_missed(self):
        results = [_result("R-A", [{"lineText": "TP LINE A", "confidenceScore": 20, "status": "rejected"}])]
        m = compute_metrics(results, GROUND_TRUTH)
        self.assertEqual(m["missed"], 1)
        self.assertEqual(m["detected"], 0)

    def test_absent_true_positive_counts_as_missed(self):
        results = [_result("R-A", [])]  # true-positive line never scored high enough to appear
        m = compute_metrics(results, GROUND_TRUTH)
        self.assertEqual(m["missed"], 1)

    def test_dangerous_false_positive(self):
        results = [_result("R-A", [
            {"lineText": "TP LINE A", "confidenceScore": 90, "status": "auto_actioned"},
            {"lineText": "SOME OTHER LINE", "confidenceScore": 85, "status": "auto_actioned"},
        ])]
        m = compute_metrics(results, GROUND_TRUTH)
        self.assertEqual(m["dangerousFalsePositives"], 1)
        # precision should be dragged down: 1 correct auto-action, 1 wrong one
        self.assertEqual(m["precision"], 0.5)

    def test_soft_false_positive_does_not_affect_precision(self):
        results = [_result("R-A", [
            {"lineText": "TP LINE A", "confidenceScore": 90, "status": "auto_actioned"},
            {"lineText": "SOME OTHER LINE", "confidenceScore": 50, "status": "pending_review"},
        ])]
        m = compute_metrics(results, GROUND_TRUTH)
        self.assertEqual(m["softFalsePositives"], 1)
        self.assertEqual(m["dangerousFalsePositives"], 0)
        self.assertEqual(m["precision"], 1.0)  # soft FPs don't count against auto-action precision

    def test_precision_none_when_no_auto_actions_at_all(self):
        results = [_result("R-A", [{"lineText": "TP LINE A", "confidenceScore": 50, "status": "pending_review"}])]
        m = compute_metrics(results, GROUND_TRUTH)
        self.assertIsNone(m["precision"])

    def test_empty_results(self):
        m = compute_metrics([], GROUND_TRUTH)
        self.assertEqual(m["n"], 0)
        self.assertIsNone(m["recall"])
        self.assertIsNone(m["meanTimeToDetectionSeconds"])

    def test_mean_time_to_detection(self):
        results = [_result("R-A", [], time_s=10.0), _result("R-B", [], time_s=20.0)]
        m = compute_metrics(results, GROUND_TRUTH)
        self.assertEqual(m["meanTimeToDetectionSeconds"], 15.0)


if __name__ == "__main__":
    unittest.main()
