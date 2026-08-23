"""The human half of the N=30 experiment (docs/EXPERIMENT.md) — an unaided manual check,
timed, scored against the same ground truth and same metrics as the agent run
(summarize_results.py), so the two are directly comparable.

This does NOT run itself — no baseline numbers exist until a person actually sits down
and does this. Deliberately built as a real timed tool rather than left as "go do this
by hand with a stopwatch," since a repeatable tool is what makes the comparison fair
(same recall order, same invoice list shown, same scoring code as the agent side).

Run from agents/: python -m experiment.run_human_baseline
Ctrl-C at any point saves progress so far to baseline_results.jsonl (append-only, same
resume behavior as run_benchmark.py) — you don't have to do all 30 in one sitting.
"""
import json
import sys
import time
from pathlib import Path

EXPERIMENT_DIR = Path(__file__).resolve().parent
AGENTS_DIR = EXPERIMENT_DIR.parent
sys.path.insert(0, str(AGENTS_DIR / "invoices"))
sys.stdout.reconfigure(encoding="utf-8")

import csv_parser  # noqa: E402

RECALLS_PATH = EXPERIMENT_DIR / "ground_truth_recalls.json"
INVOICE_GROUND_TRUTH_PATH = EXPERIMENT_DIR / "invoice_ground_truth.json"
INVOICE_DIR = EXPERIMENT_DIR / "invoices"
RESULTS_PATH = EXPERIMENT_DIR / "baseline_results.jsonl"


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
    recalls = json.loads(RECALLS_PATH.read_text(encoding="utf-8"))
    all_lines = load_line_items()
    done = already_done()
    remaining = [r for r in recalls if r["sourceRecordId"] not in done]

    print(f"{len(done)}/{len(recalls)} already done. {len(remaining)} remaining.")
    print(f"You'll see {len(all_lines)} invoice line items for EVERY recall — same list the")
    print("agent checks against. For each recall, type the line number(s) that plausibly")
    print("match (comma-separated), or just press Enter if none look like a match.\n")
    input("Press Enter when ready to start the clock on the first case...")

    for recall in remaining:
        print("\n" + "=" * 70)
        print(f"RECALL: {recall['productDescription']}")
        print(f"Classification: {recall['classification']} | Hazard: {recall['hazardType']}")
        print("=" * 70)
        for i, line in enumerate(all_lines):
            print(f"  [{i}] {line['rawText']}  (supplier: {line['supplier']})")

        start = time.monotonic()
        try:
            raw_answer = input("\nMatching line number(s), comma-separated, or Enter for none: ").strip()
        except KeyboardInterrupt:
            print(f"\n\nStopped. {len(already_done())}/{len(recalls)} saved to {RESULTS_PATH.name}.")
            return
        elapsed = time.monotonic() - start

        picked_indices = [int(x.strip()) for x in raw_answer.split(",") if x.strip().isdigit()]
        picked_lines = [all_lines[i]["rawText"] for i in picked_indices if 0 <= i < len(all_lines)]

        result = {
            "recallId": recall["sourceRecordId"],
            "timeToDetectionSeconds": round(elapsed, 1),
            "pickedLines": picked_lines,
        }
        with open(RESULTS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        print(f"Recorded ({elapsed:.1f}s).")

    print(f"\nAll {len(recalls)} done. Run experiment.summarize_baseline to score it.")


if __name__ == "__main__":
    main()
