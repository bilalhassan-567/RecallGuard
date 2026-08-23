"""Runs the N=30 experiment (docs/EXPERIMENT.md): each frozen ground-truth recall against
the shared invoice corpus, scored against invoice_ground_truth.json.

Checkpointed against the free-tier daily quota (20 requests/day for gemini-3.5-flash —
see docs/RISK_REGISTER.md, hit this for real on 2026-08-23): each completed recall is
appended to benchmark_results.jsonl immediately, and already-completed recalls are
skipped on the next run — so if quota runs out mid-run, just run this again tomorrow and
it resumes instead of re-spending calls on work that's already done.

Run from agents/: python -m experiment.run_benchmark [--limit N]
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252 otherwise

EXPERIMENT_DIR = Path(__file__).resolve().parent
AGENTS_DIR = EXPERIMENT_DIR.parent
sys.path.insert(0, str(AGENTS_DIR / "ingestion"))
sys.path.insert(0, str(AGENTS_DIR / "invoices"))
sys.path.insert(0, str(AGENTS_DIR / "matching"))

import csv_parser  # noqa: E402
import matching_agent  # noqa: E402

RECALLS_PATH = EXPERIMENT_DIR / "ground_truth_recalls.json"
INVOICE_GROUND_TRUTH_PATH = EXPERIMENT_DIR / "invoice_ground_truth.json"
INVOICE_DIR = EXPERIMENT_DIR / "invoices"
RESULTS_PATH = EXPERIMENT_DIR / "benchmark_results.jsonl"


def load_line_items() -> list[dict]:
    lines = []
    for csv_path in sorted(INVOICE_DIR.glob("*.csv")):
        lines.extend(csv_parser.parse_csv(csv_path, supplier=csv_path.stem))
    return lines


def already_done() -> set[str]:
    if not RESULTS_PATH.exists():
        return set()
    done = set()
    with open(RESULTS_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                done.add(json.loads(line)["recallId"])
    return done


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="max recalls to process this run (quota pacing)")
    args = parser.parse_args()

    recalls = json.loads(RECALLS_PATH.read_text(encoding="utf-8"))
    all_lines = load_line_items()
    done = already_done()
    remaining = [r for r in recalls if r["sourceRecordId"] not in done]

    print(f"{len(done)}/{len(recalls)} recalls already scored. {len(remaining)} remaining.")
    if args.limit:
        remaining = remaining[: args.limit]
        print(f"Processing up to {len(remaining)} this run (--limit {args.limit}).")

    for recall in remaining:
        start = time.monotonic()
        try:
            matches = matching_agent.match_recall_against_lines(recall, all_lines)
        except Exception as err:  # noqa: BLE001 — a quota error mid-run must not corrupt the checkpoint file
            print(f"STOPPING at {recall['sourceRecordId']}: {err}")
            print("Already-completed recalls are saved. Re-run this script later to resume.")
            return
        elapsed = time.monotonic() - start

        result = {
            "recallId": recall["sourceRecordId"],
            "classification": recall["classification"],
            "productDescription": recall["productDescription"],
            "timeToDetectionSeconds": round(elapsed, 2),
            "matches": [
                {
                    "lineText": m["invoiceLineRef"]["rawText"],
                    "confidenceScore": m["confidenceScore"],
                    "status": m["status"],
                }
                for m in matches
                if m["confidenceScore"] >= 15  # keep the file readable; near-zero scores add no signal
            ],
        }
        with open(RESULTS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        print(f"  {recall['sourceRecordId']} ({recall['classification']}) — {elapsed:.1f}s, {len(result['matches'])} scored matches")

    print(f"\nDone this run. {len(already_done())}/{len(recalls)} total scored.")
    print("Run experiment.summarize_results once all 30 are done.")


if __name__ == "__main__":
    main()
