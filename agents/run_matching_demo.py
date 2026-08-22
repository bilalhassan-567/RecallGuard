"""End-to-end local demo: fetch two real recalls -> parse all 5 sample invoices -> run
the Matching Agent -> print routing decisions and Scout's reasoning for each line,
checked informally against agents/sample_data/invoices/ground_truth.json.

This is the first full pipeline run (ingestion -> normalize -> parse -> match), all
local, no GCP needed. Run from agents/: python run_matching_demo.py

Note on structure: each subpackage (ingestion/, invoices/, matching/) uses flat sibling
imports internally (e.g. `import normalize`, not `from . import normalize`), matching how
they're run standalone (`cd ingestion && python test_ingestion.py`). This script adds
each subdirectory to sys.path to make that work from one place — a real package
restructure (proper relative imports) is reasonable future cleanup, not urgent given the
deadline.
"""
import json
import sys
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent
for sub in ("ingestion", "invoices", "matching"):
    sys.path.insert(0, str(AGENTS_DIR / sub))

import agent as matching_agent  # matching/agent.py
import csv_parser
import normalize
import openfda_client

KNOWN_RECALLS = ["H-0552-2026", "H-1219-2026"]
INVOICE_DIR = AGENTS_DIR / "sample_data" / "invoices"


def main() -> None:
    recalls = []
    for recall_number in KNOWN_RECALLS:
        raw = openfda_client.fetch_by_recall_number(recall_number)
        if raw is None:
            print(f"WARNING: {recall_number} not found live, skipping")
            continue
        recalls.append(normalize.normalize_openfda(raw))

    all_lines = []
    for csv_path in sorted(INVOICE_DIR.glob("*.csv")):
        all_lines.extend(csv_parser.parse_csv(csv_path, supplier=csv_path.stem))
    print(f"Loaded {len(all_lines)} invoice line items from {INVOICE_DIR.name}/\n")

    for recall in recalls:
        print("=" * 70)
        print(f"RECALL {recall['sourceRecordId']}: {recall['productDescription'][:70]}")
        print(f"Classification: {recall['classification']} | Hazard: {recall['hazardType'][:80]}")
        print("=" * 70)
        matches = matching_agent.match_recall_against_lines(recall, all_lines)
        # Only show lines Scout considered worth a real score, sorted highest first.
        matches.sort(key=lambda m: m["confidenceScore"], reverse=True)
        for m in matches:
            if m["confidenceScore"] < 15:  # skip the obviously-irrelevant bulk for readability
                continue
            line = m["invoiceLineRef"]
            print(f"\n  [{m['status'].upper()}] {m['confidenceScore']}% - {line['rawText']!r}")
            print(f"    supplier: {line['supplier']}")
            print(f"    Scout: {m['reasoning']}")
        print()


if __name__ == "__main__":
    main()
    print("\nCompare against agents/sample_data/invoices/ground_truth.json expectations.")
