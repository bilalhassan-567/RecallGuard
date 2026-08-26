"""One-off migration: groups the legacy flat invoice-line documents (written by the
now-obsolete seed_invoices.py, before the Invoices feature existed) into real invoice
entities, and backfills invoiceId onto existing matches that reference them.

Legacy detection: a doc under businesses/{id}/invoices lacking a "rawLineItems" key is
a pre-migration flat line (the new shape always has one) — this makes the script
idempotent and safely re-runnable; already-migrated invoices are simply skipped.

Dry-run by default (prints the plan, writes nothing). Pass --apply to actually write.

Run from agents/, pointed at real Firestore:
  USE_FIRESTORE=TRUE GOOGLE_CLOUD_PROJECT=<project-id> python migrate_legacy_invoices.py --business-id demo-biz-1 [--apply]

Ordering note (see docs/PROGRESS.md): run this before or in the same window as
redeploying the live recallMatcher Cloud Function, never after — that function reads
invoices via invoice_store.flatten_invoice_lines(), which returns zero lines for a
legacy doc with no rawLineItems key.
"""
import argparse
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent / "invoices"))
import storage  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--business-id", required=True)
    parser.add_argument("--apply", action="store_true", help="actually write; default is dry-run")
    args = parser.parse_args()

    all_docs = storage.list_collection(f"businesses/{args.business_id}/invoices")
    legacy_lines = [d for d in all_docs if "rawLineItems" not in d]

    if not legacy_lines:
        print("No legacy flat invoice-line documents found — nothing to migrate.")
        return

    groups: dict[str, list[dict]] = {}
    for line in legacy_lines:
        groups.setdefault(line.get("supplier", "unknown"), []).append(line)

    print(f"Found {len(legacy_lines)} legacy line(s) across {len(groups)} supplier group(s):")
    for supplier, lines in groups.items():
        print(f"  - {supplier}: {len(lines)} line(s)")

    if not args.apply:
        print("\nDry run only — pass --apply to actually migrate.")
        return

    all_matches = storage.list_collection(f"businesses/{args.business_id}/matches")

    for supplier, lines in groups.items():
        source_file_name = f"{supplier}.csv"
        new_invoice_id = str(uuid.uuid4())
        new_lines = []
        old_ids = []
        for old_line in lines:
            new_line = {
                "lineId": str(uuid.uuid4()),
                "rawText": old_line.get("rawText", ""),
                "supplier": old_line.get("supplier", supplier),
                "quantity": old_line.get("quantity", ""),
                "unit": old_line.get("unit", ""),
                "dateReceived": old_line.get("dateReceived", ""),
                "parsedProduct": old_line.get("parsedProduct"),
                "parsedLot": old_line.get("parsedLot"),
            }
            new_lines.append(new_line)
            old_ids.append(old_line["_id"])

        invoice_doc = {
            "sourceFileName": source_file_name,
            "sourceType": "csv",
            "supplier": supplier,
            # The real original upload time was never recorded by the legacy seed
            # script — using migration time here is an accepted, documented
            # limitation, not a fabricated value.
            "uploadedAt": datetime.now(timezone.utc).isoformat(),
            "migratedAt": datetime.now(timezone.utc).isoformat(),
            "migratedFromLegacyIds": old_ids,
            "rawLineItems": new_lines,
        }
        storage.save(f"businesses/{args.business_id}/invoices", new_invoice_id, invoice_doc)
        print(f"Created invoice {new_invoice_id} ({source_file_name}, {len(new_lines)} lines)")

        # Best-effort backfill: match existing match records to a migrated line by
        # supplier+rawText (exact, since the legacy seed always used one literal
        # supplier string per source file). Duplicate rawText within one supplier
        # could collide on lineId here — acceptable for a one-off backfill, since
        # nothing downstream needs lineId precision on pre-migration matches, only
        # the invoiceId deep-link.
        backfilled = 0
        for match in all_matches:
            ref = match.get("invoiceLineRef") or {}
            if ref.get("invoiceId"):
                continue  # already has one, not a pre-migration match
            if ref.get("supplier") != supplier:
                continue
            matching_new_line = next((nl for nl in new_lines if nl["rawText"] == ref.get("rawText")), None)
            if matching_new_line is None:
                continue
            match["invoiceLineRef"] = {**ref, "invoiceId": new_invoice_id, "lineId": matching_new_line["lineId"]}
            storage.save(f"businesses/{args.business_id}/matches", match["_id"], match)
            backfilled += 1
        print(f"  Backfilled invoiceId onto {backfilled} existing match(es)")

        for old_id in old_ids:
            storage.delete(f"businesses/{args.business_id}/invoices", old_id)
        print(f"  Deleted {len(old_ids)} legacy flat line doc(s)")

    print("\nMigration complete.")


if __name__ == "__main__":
    main()
