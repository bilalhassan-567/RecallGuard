"""Scores baseline_results.jsonl (from run_human_baseline.py) against the same ground
truth summarize_results.py uses, so the two are directly comparable — same precision/
recall/time-to-detection definitions, human side.

Run from agents/: python -m experiment.summarize_baseline
"""
import json
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parent
RESULTS_PATH = EXPERIMENT_DIR / "baseline_results.jsonl"
GROUND_TRUTH_PATH = EXPERIMENT_DIR / "invoice_ground_truth.json"
RECALLS_PATH = EXPERIMENT_DIR / "ground_truth_recalls.json"


def compute_baseline_metrics(results: list[dict], ground_truth: dict) -> dict:
    tp_by_recall = {tp["recall_number"]: tp["line_text"] for tp in ground_truth["true_positives"]}

    detected = missed = false_positives = 0
    times = []

    for result in results:
        expected_line = tp_by_recall.get(result["recallId"])
        times.append(result["timeToDetectionSeconds"])
        picked = result["pickedLines"]

        if expected_line in picked:
            detected += 1
        else:
            missed += 1
        false_positives += sum(1 for line in picked if line != expected_line)

    n = len(results)
    precision = detected / (detected + false_positives) if (detected + false_positives) else None
    recall_rate = detected / n if n else None
    mean_time = sum(times) / len(times) if times else None

    return {
        "n": n,
        "detected": detected,
        "missed": missed,
        "falsePositives": false_positives,
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
        print(f"{RESULTS_PATH} doesn't exist yet — run experiment.run_human_baseline first.")
        return

    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    total_recalls = len(json.loads(RECALLS_PATH.read_text(encoding="utf-8")))
    results = _load_jsonl(RESULTS_PATH)
    m = compute_baseline_metrics(results, ground_truth)

    print(f"Scored {m['n']}/{total_recalls} recalls.\n")
    print(f"Detected: {m['detected']}/{m['n']}")
    print(f"Missed (false negatives): {m['missed']}/{m['n']}")
    print(f"False positives: {m['falsePositives']}")
    print()
    print(f"Precision: {m['precision']:.1%}" if m["precision"] is not None else "Precision: n/a")
    print(f"Recall: {m['recall']:.1%}" if m["recall"] is not None else "Recall: n/a")
    print(f"Mean time-to-detection: {m['meanTimeToDetectionSeconds']:.1f}s" if m["meanTimeToDetectionSeconds"] is not None else "Mean time-to-detection: n/a")
    print("\nCompare directly against: python -m experiment.summarize_results")


if __name__ == "__main__":
    main()
