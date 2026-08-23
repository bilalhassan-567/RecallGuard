"""The human half of the N=30 experiment (docs/EXPERIMENT.md) — an unaided manual check,
timed, scored against the same ground truth and same metrics as the agent run
(summarize_results.py), so the two are directly comparable.

This does NOT run itself — no baseline numbers exist until a person actually sits down
and does this. Deliberately built as a real timed tool rather than left as "go do this
by hand with a stopwatch," since a repeatable tool is what makes the comparison fair
(same recall order, same invoice list shown, same scoring code as the agent side).

Run from agents/: python -m experiment.run_human_baseline [--limit N]
Ctrl-C at any point ALSO saves progress so far — you don't have to do all 30 in one
sitting, or even decide up front how many you'll do; --limit is just for planning a
specific short session (e.g. "10 cases, ~5-10 min, then I'll stop").
"""
import argparse
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="stop after N cases this session (e.g. --limit 10 for a ~5-10 min sitting)")
    args = parser.parse_args()

    recalls = json.loads(RECALLS_PATH.read_text(encoding="utf-8"))
    all_lines = load_line_items()
    done = already_done()
    remaining = [r for r in recalls if r["sourceRecordId"] not in done]
    session = remaining[: args.limit] if args.limit else remaining

    print(f"{len(done)}/{len(recalls)} already done. {len(remaining)} remaining overall.")
    if args.limit:
        print(f"This session: {len(session)} cases (--limit {args.limit}).")
    print(f"You'll see {len(all_lines)} invoice line items for EVERY recall — same list the")
    print("agent checks against. For each recall, type the line number(s) that plausibly")
    print("match (comma-separated), or just press Enter if none look like a match.\n")
    input("Press Enter when ready to start the clock on the first case...")

    session_times = []
    for idx, recall in enumerate(session, start=1):
        print("\n" + "=" * 70)
        eta = f" — ~{(sum(session_times) / len(session_times)) * (len(session) - idx + 1) / 60:.1f} min left" if session_times else ""
        print(f"Case {idx}/{len(session)}{eta}")
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
        session_times.append(elapsed)

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

    total_done = len(already_done())
    if total_done >= len(recalls):
        print(f"\nAll {len(recalls)} done. Run experiment.summarize_baseline to score it.")
    else:
        print(f"\nSession done: {total_done}/{len(recalls)} total so far. Run this again anytime to continue.")


if __name__ == "__main__":
    main()
