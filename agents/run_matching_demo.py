"""End-to-end local demo: fetch two real recalls -> parse all 5 sample invoices -> run
the Matching Agent -> run the Action Agent on anything auto-actioned (real checklist,
notification drafts, and a compliance PDF) -> print everything, checked informally
against agents/sample_data/invoices/ground_truth.json.

This is the full pipeline (ingestion -> normalize -> parse -> match -> act), all local,
no GCP needed. Run from agents/: python run_matching_demo.py

Note on structure: each subpackage (ingestion/, invoices/, matching/, action/) uses flat
sibling imports internally (e.g. `import normalize`, not `from . import normalize`),
matching how they're run standalone (`cd ingestion && python test_ingestion.py`). This
script adds each subdirectory to sys.path to make that work from one place. matching_agent
and action_agent are named to avoid a real collision that existed earlier when both
subpackages had a same-named agent.py — see docs/PROGRESS.md, 2026-08-23.
"""
import sys
from pathlib import Path

# Windows' console defaults to cp1252, which mangles any non-ASCII character an LLM
# response might contain (accents, em-dashes, etc.) into "?" — this is the real, root
# fix, rather than chasing individual characters out of print statements.
sys.stdout.reconfigure(encoding="utf-8")

AGENTS_DIR = Path(__file__).resolve().parent
for sub in ("ingestion", "invoices", "matching", "action"):
    sys.path.insert(0, str(AGENTS_DIR / sub))

import action_agent  # noqa: E402  (path setup must run first)
import csv_parser  # noqa: E402
import image_parser  # noqa: E402
import matching_agent  # noqa: E402
import normalize  # noqa: E402
import openfda_client  # noqa: E402

KNOWN_RECALLS = ["H-0552-2026", "H-1219-2026"]
INVOICE_DIR = AGENTS_DIR / "sample_data" / "invoices"
DEMO_BUSINESS = {"id": "demo-biz-1", "name": "Maple & Vine Kitchen", "address": "12 Main St, Springfield"}


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

    photo_path = INVOICE_DIR / "photo_006_true_positive.jpg"
    if photo_path.exists():
        # The multimodal case — a photographed invoice, not a clean export. Best
        # Multimodal UX target (docs/PLAN.md): this isn't a CSV, it's a real image read
        # by Gemini's vision input, going through the exact same downstream pipeline.
        photo_lines = image_parser.parse_image(str(photo_path))
        print(f"Extracted {len(photo_lines)} lines from a PHOTOGRAPHED invoice (not a clean CSV)")
        all_lines.extend(photo_lines)

    print(f"Loaded {len(all_lines)} invoice line items total from {INVOICE_DIR.name}/\n")

    for recall in recalls:
        print("=" * 70)
        print(f"RECALL {recall['sourceRecordId']}: {recall['productDescription'][:70]}")
        print(f"Classification: {recall['classification']} | Hazard: {recall['hazardType'][:80]}")
        print("=" * 70)
        matches = matching_agent.match_recall_against_lines(recall, all_lines)
        matches.sort(key=lambda m: m["confidenceScore"], reverse=True)
        for m in matches:
            if m["confidenceScore"] < 15:  # skip the obviously-irrelevant bulk for readability
                continue
            line = m["invoiceLineRef"]
            print(f"\n  [{m['status'].upper()}] {m['confidenceScore']}% - {line['rawText']!r}")
            print(f"    supplier: {line['supplier']}")
            print(f"    Scout: {m['reasoning']}")

            if m["status"] == "auto_actioned":
                result = action_agent.run_action_agent(m, recall, DEMO_BUSINESS)
                print(f"    -> Action Agent ran: PDF at {result['compliancePdfPath']}")
                print(f"    -> Storage hint: {result['checklist']['storageHint']}")
        print()


if __name__ == "__main__":
    main()
    print("\nCompare against agents/sample_data/invoices/ground_truth.json expectations.")
    print("Generated PDFs are in agents/local_data/artifacts/ (gitignored, not committed).")
