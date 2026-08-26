"""Regression test for a real bug caught 2026-08-27 (see docs/PROGRESS.md): the invoice
line list shown to a human doing the baseline used to be built by concatenating the CSVs
in file order, which happened to put each recall's true-positive line at a position that
tracked the recall's own processing order almost perfectly (correlation ~1.0) — a
human working through cases in order could learn "the answer creeps up by ~1 each time"
without reading anything. Fixed with a fixed-seed shuffle in load_line_items(); this test
makes sure that fix can't silently regress.

Run: python -m unittest test_run_human_baseline -v
"""
import json
import unittest
from pathlib import Path

from run_human_baseline import load_line_items

EXPERIMENT_DIR = Path(__file__).resolve().parent


class TestLoadLineItemsOrdering(unittest.TestCase):
    def test_deterministic_across_calls(self):
        first = [line["rawText"] for line in load_line_items()]
        second = [line["rawText"] for line in load_line_items()]
        self.assertEqual(first, second)

    def test_no_strong_correlation_with_recall_processing_order(self):
        recalls = json.loads((EXPERIMENT_DIR / "ground_truth_recalls.json").read_text(encoding="utf-8"))
        ground_truth = json.loads((EXPERIMENT_DIR / "invoice_ground_truth.json").read_text(encoding="utf-8"))
        tp_by_recall = {tp["recall_number"]: tp["line_text"] for tp in ground_truth["true_positives"]}

        shown_order = [line["rawText"] for line in load_line_items()]
        position_by_text = {text: i for i, text in enumerate(shown_order)}

        pairs = []
        for recall_index, recall in enumerate(recalls):
            line_text = tp_by_recall.get(recall["sourceRecordId"])
            if line_text is None:
                continue
            pairs.append((recall_index, position_by_text[line_text]))

        recall_indices = [p[0] for p in pairs]
        positions = [p[1] for p in pairs]
        correlation = _pearson(recall_indices, positions)

        # The pre-fix bug measured ~1.0 (perfectly sequential). A real shuffle should
        # land nowhere near that — 0.5 is a generous margin, not a tight bound.
        self.assertLess(
            abs(correlation), 0.5,
            f"correlation={correlation:.3f} — the shown line order tracks recall "
            "processing order too closely, reintroducing the guessable pattern",
        )


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    return cov / (var_x * var_y) ** 0.5


if __name__ == "__main__":
    unittest.main()
