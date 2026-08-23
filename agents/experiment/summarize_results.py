"""Scores agents/experiment/benchmark_results.jsonl against invoice_ground_truth.json
and prints the metrics docs/EXPERIMENT.md asks for: precision, recall, false-positive
rate, false-negative rate, mean time-to-detection, and the auto-actioned vs.
correctly-escalated split.

Definitions (see docs/AGENTS.md for the underlying thresholds — >=80 auto_actioned,
40-79 pending_review, <40 rejected):
- Detected: the recall's own true-positive line scored auto_actioned OR pending_review.
- Missed (false negative): the true-positive line scored rejected, or didn't appear in
  the results at all (below the 15-point logging floor in run_benchmark.py).
- Dangerous false positive: any OTHER line (a distractor, or another recall's unrelated
  true-positive line) scored auto_actioned for this recall — this is the case that
  matters for "zero high-confidence false positives" (docs/EXPERIMENT.md's success bar),
  since auto_actioned is what triggers a real drafted notification.
- Soft false positive: any other line scored pending_review — routed to a human, not
  auto-acted on, so tracked separately rather than folded into the same "false positive"
  count as the dangerous case above.

Run from agents/: python -m experiment.summarize_results
"""
import json
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_PATH = EXPERIMENT_DIR / "benchmark_results.jsonl"
GROUND_TRUTH_PATH = EXPERIMENT_DIR / "invoice_ground_truth.json"
RECALLS_PATH = EXPERIMENT_DIR / "ground_truth_recalls.json"


def compute_metrics(results: list[dict], ground_truth: dict) -> dict:
    tp_by_recall = {tp["recall_number"]: tp["line_text"] for tp in ground_truth["true_positives"]}

    detected = correctly_auto = correctly_escalated = missed = 0
    dangerous_fp = soft_fp = 0
    times = []

    for result in results:
        expected_line = tp_by_recall.get(result["recallId"])
        times.append(result["timeToDetectionSeconds"])

        tp_status = None
        for m in result["matches"]:
            if m["lineText"] == expected_line:
                tp_status = m["status"]
            elif m["status"] == "auto_actioned":
                dangerous_fp += 1
            elif m["status"] == "pending_review":
                soft_fp += 1

        if tp_status == "auto_actioned":
            detected += 1
            correctly_auto += 1
        elif tp_status == "pending_review":
            detected += 1
            correctly_escalated += 1
        else:
            missed += 1

    n = len(results)
    precision = correctly_auto / (correctly_auto + dangerous_fp) if (correctly_auto + dangerous_fp) else None
    recall_rate = detected / n if n else None
    mean_time = sum(times) / len(times) if times else None

    return {
        "n": n,
        "detected": detected,
        "correctlyAutoActioned": correctly_auto,
        "correctlyEscalated": correctly_escalated,
        "missed": missed,
        "dangerousFalsePositives": dangerous_fp,
        "softFalsePositives": soft_fp,
        "precision": precision,
        "recall": recall_rate,
        "meanTimeToDetectionSeconds": mean_time,
    }


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    if not RESULTS_PATH.exists():
        print(f"{RESULTS_PATH} doesn't exist yet — run experiment.run_benchmark first.")
        return

    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    total_recalls = len(json.loads(RECALLS_PATH.read_text(encoding="utf-8")))
    results = _load_jsonl(RESULTS_PATH)
    m = compute_metrics(results, ground_truth)

    print(f"Scored {m['n']}/{total_recalls} recalls (run experiment.run_benchmark again to complete the rest if <{total_recalls}).\n")
    print(f"Detected (auto-actioned or escalated): {m['detected']}/{m['n']}")
    print(f"  - Correctly auto-actioned:  {m['correctlyAutoActioned']}")
    print(f"  - Correctly escalated for review: {m['correctlyEscalated']}")
    print(f"Missed (false negatives):    {m['missed']}/{m['n']}")
    print(f"Dangerous false positives (wrongly auto-actioned): {m['dangerousFalsePositives']}")
    print(f"Soft false positives (wrongly escalated, not auto-acted): {m['softFalsePositives']}")
    print()
    print(f"Precision (on auto-actioned decisions): {m['precision']:.1%}" if m["precision"] is not None else "Precision: n/a (no auto-actioned decisions yet)")
    print(f"Recall (found at all, auto or reviewed): {m['recall']:.1%}" if m["recall"] is not None else "Recall: n/a")
    print(f"Mean time-to-detection: {m['meanTimeToDetectionSeconds']:.2f}s" if m["meanTimeToDetectionSeconds"] is not None else "Mean time-to-detection: n/a")


if __name__ == "__main__":
    main()
