"""A second, automated comparison point — NOT a substitute for the human baseline
(docs/EXPERIMENT.md still needs a real person for that; see run_human_baseline.py). This
is a naive, non-LLM fuzzy-string matcher: no reasoning, no brand/flavor disambiguation,
just token-overlap similarity. Fully honest to run and report, since it's deterministic
and needs no human — it answers a different, complementary question: "does the Matching
Agent's reasoning actually add value over simple fuzzy matching, or would grep-with-extra-
steps get the same result?"

Deliberately simple (difflib, stdlib only) — the point isn't to build a good baseline,
it's to build an honest bad one and see by how much the real agent beats it.

Run from agents/: python -m experiment.naive_baseline
"""
import json
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252 otherwise

EXPERIMENT_DIR = Path(__file__).resolve().parent
RECALLS_PATH = EXPERIMENT_DIR / "ground_truth_recalls.json"
GROUND_TRUTH_PATH = EXPERIMENT_DIR / "invoice_ground_truth.json"
INVOICE_DIR = EXPERIMENT_DIR / "invoices"

MATCH_THRESHOLD = 0.5  # a SequenceMatcher ratio above this counts as "matched" — arbitrary,
# picked once before looking at results, not tuned afterward to flatter the number


def _normalize(text: str) -> str:
    return re.sub(r"[^A-Z0-9 ]", " ", text.upper())


def best_match(recall_text: str, lines: list[str]) -> tuple[str, float]:
    target = _normalize(recall_text)
    best_line, best_score = "", 0.0
    for line in lines:
        score = SequenceMatcher(None, target, _normalize(line)).ratio()
        if score > best_score:
            best_line, best_score = line, score
    return best_line, best_score


def load_line_items() -> list[str]:
    import csv

    lines = []
    for csv_path in sorted(INVOICE_DIR.glob("*.csv")):
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            desc_col = next((c for c in reader.fieldnames if "desc" in c.lower() or c.lower() in ("item",)), None)
            for row in reader:
                if desc_col:
                    lines.append(row[desc_col])
    return lines


def main() -> None:
    recalls = json.loads(RECALLS_PATH.read_text(encoding="utf-8"))
    ground_truth = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    tp_by_recall = {tp["recall_number"]: tp["line_text"] for tp in ground_truth["true_positives"]}
    lines = load_line_items()

    detected = false_positives = 0
    times = []

    for recall in recalls:
        start = time.monotonic()
        matched_line, score = best_match(recall["productDescription"], lines)
        elapsed = time.monotonic() - start
        times.append(elapsed)

        expected = tp_by_recall.get(recall["sourceRecordId"])
        is_match = score >= MATCH_THRESHOLD
        if is_match and matched_line == expected:
            detected += 1
        elif is_match and matched_line != expected:
            false_positives += 1
        # is_match == False and matched_line != expected -> correctly found nothing (not scored either way)
        # is_match == False and matched_line == expected -> a real miss, already counted as not detected

    n = len(recalls)
    precision = detected / (detected + false_positives) if (detected + false_positives) else None
    recall_rate = detected / n if n else None
    mean_time = sum(times) / len(times) if times else None

    print(f"Naive fuzzy-match baseline (difflib, threshold={MATCH_THRESHOLD}) — n={n}\n")
    print(f"Detected: {detected}/{n}")
    print(f"False positives: {false_positives}")
    print(f"Precision: {precision:.1%}" if precision is not None else "Precision: n/a")
    print(f"Recall: {recall_rate:.1%}" if recall_rate is not None else "Recall: n/a")
    print(f"Mean time per recall: {mean_time*1000:.2f}ms (no API call — this is pure string computation)")
    print("\nThis is NOT the human baseline docs/EXPERIMENT.md calls for — it's a second,")
    print("automated comparison point showing what simple string matching gets you without")
    print("LLM reasoning. Compare against: python -m experiment.summarize_results")


if __name__ == "__main__":
    main()
