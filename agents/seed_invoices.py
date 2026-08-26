"""One-off seed: persists the existing sample CSV invoice line items into Firestore
under businesses/{id}/invoices/{lineId}, so the Phase 3 Cloud Function pipeline
(agents/main.py) has real invoice data to check new recalls against without a human
running run_matching_demo.py locally first.

Deliberately CSV-only, not the photographed invoice — image_parser.parse_image() calls
Gemini vision, and this seed step should cost zero Gemini quota. The photo path is
already proven separately (see docs/PROGRESS.md, Phase 4).

Run from agents/, with USE_FIRESTORE=TRUE and GOOGLE_CLOUD_PROJECT set:
  USE_FIRESTORE=TRUE GOOGLE_CLOUD_PROJECT=<project-id> python seed_invoices.py
"""
import sys
import uuid
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AGENTS_DIR / "invoices"))

import csv_parser  # noqa: E402
import storage  # noqa: E402

INVOICE_DIR = AGENTS_DIR / "sample_data" / "invoices"
BUSINESS_ID = "demo-biz-1"


def main() -> None:
    count = 0
    for csv_path in sorted(INVOICE_DIR.glob("*.csv")):
        for line in csv_parser.parse_csv(csv_path, supplier=csv_path.stem):
            storage.save(f"businesses/{BUSINESS_ID}/invoices", str(uuid.uuid4()), line)
            count += 1
    print(f"Seeded {count} invoice line items into businesses/{BUSINESS_ID}/invoices.")


if __name__ == "__main__":
    main()
