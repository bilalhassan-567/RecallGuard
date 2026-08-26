"""Groups parsed invoice lines (csv_parser.py / image_parser.py output) into a real
invoice entity — businesses/{id}/invoices/{invoiceId} — instead of flat orphan line
documents with no shared ID, no upload timestamp, and no way to trace a match back to
its source invoice.

The reconciliation mechanism is entirely in flatten_invoice_lines(): every line it
returns carries its own invoiceId. Since matching_agent.match_recall_against_lines
copies whatever dict it's handed straight into match["invoiceLineRef"], that invoiceId
(and lineId) rides along into every match automatically — matching_agent.py and
orchestrator.py need no changes at all.

Reconciliation counts (flagged/auto-actioned/clean) are computed here from real match
records each time, never stored on the invoice document itself — matches are the
source of truth, same reasoning docs/DATA_MODEL.md already gives for
metrics/{businessId}_daily being a recompute-safe rollup rather than a cached value
that can drift out of sync.
"""
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # agents/ (storage.py)
import storage  # noqa: E402


def create_invoice(
    business_id: str,
    source_file_name: str,
    source_type: str,
    raw_lines: list[dict],
    supplier: str | None = None,
) -> dict:
    if source_type not in ("csv", "image"):
        raise ValueError(f"source_type must be 'csv' or 'image', got {source_type!r}")
    if not raw_lines:
        raise ValueError("no line items to store — the parser returned zero lines")

    invoice_id = str(uuid.uuid4())
    resolved_supplier = supplier or raw_lines[0].get("supplier") or source_file_name
    lines_with_ids = [{**line, "lineId": str(uuid.uuid4())} for line in raw_lines]

    invoice = {
        "sourceFileName": source_file_name,
        "sourceType": source_type,
        "supplier": resolved_supplier,
        "uploadedAt": datetime.now(timezone.utc).isoformat(),
        "rawLineItems": lines_with_ids,
    }
    storage.save(f"businesses/{business_id}/invoices", invoice_id, invoice)
    return {**invoice, "_id": invoice_id}


def flatten_invoice_lines(business_id: str) -> list[dict]:
    lines = []
    for invoice in storage.list_collection(f"businesses/{business_id}/invoices"):
        for line in invoice.get("rawLineItems", []):
            lines.append({**line, "invoiceId": invoice["_id"]})
    return lines


def list_invoices(business_id: str) -> list[dict]:
    invoices = storage.list_collection(f"businesses/{business_id}/invoices")
    matches = storage.list_collection(f"businesses/{business_id}/matches")

    counts_by_invoice: dict[str, dict[str, int]] = {}
    for match in matches:
        ref = match.get("invoiceLineRef") or {}
        invoice_id = ref.get("invoiceId")
        if not invoice_id:
            continue  # a pre-migration match with no traceable source invoice
        bucket = counts_by_invoice.setdefault(invoice_id, {"flagged": 0, "autoActioned": 0, "clean": 0})
        status = match.get("status")
        if status == "pending_review":
            bucket["flagged"] += 1
        elif status == "auto_actioned":
            bucket["autoActioned"] += 1
        else:
            bucket["clean"] += 1

    summaries = []
    for invoice in invoices:
        counts = counts_by_invoice.get(invoice["_id"], {"flagged": 0, "autoActioned": 0, "clean": 0})
        summaries.append(
            {
                "_id": invoice["_id"],
                "sourceFileName": invoice.get("sourceFileName", ""),
                "sourceType": invoice.get("sourceType", ""),
                "supplier": invoice.get("supplier", ""),
                "uploadedAt": invoice.get("uploadedAt", ""),
                "lineCount": len(invoice.get("rawLineItems", [])),
                "flaggedCount": counts["flagged"],
                "autoActionedCount": counts["autoActioned"],
                "cleanCount": counts["clean"],
            }
        )
    summaries.sort(key=lambda s: s["uploadedAt"], reverse=True)
    return summaries


def get_invoice_detail(business_id: str, invoice_id: str) -> dict | None:
    invoice = storage.get(f"businesses/{business_id}/invoices", invoice_id)
    if invoice is None:
        return None
    matches = storage.list_collection(f"businesses/{business_id}/matches")

    matches_by_line: dict[str, list[dict]] = {}
    for match in matches:
        ref = match.get("invoiceLineRef") or {}
        if ref.get("invoiceId") != invoice_id:
            continue
        line_id = ref.get("lineId")
        matches_by_line.setdefault(line_id, []).append(
            {
                "recallId": match.get("recallId"),
                "confidenceScore": match.get("confidenceScore"),
                "reasoning": match.get("reasoning"),
                "status": match.get("status"),
                "createdAt": match.get("createdAt"),
            }
        )

    lines = []
    for line in invoice.get("rawLineItems", []):
        history = sorted(
            matches_by_line.get(line.get("lineId"), []),
            key=lambda m: m.get("createdAt") or "",
            reverse=True,
        )
        lines.append({**line, "matchHistory": history})

    return {
        "_id": invoice_id,
        "sourceFileName": invoice.get("sourceFileName", ""),
        "sourceType": invoice.get("sourceType", ""),
        "supplier": invoice.get("supplier", ""),
        "uploadedAt": invoice.get("uploadedAt", ""),
        "lines": lines,
    }


def delete_invoice(business_id: str, invoice_id: str) -> bool:
    if storage.get(f"businesses/{business_id}/invoices", invoice_id) is None:
        return False
    storage.delete(f"businesses/{business_id}/invoices", invoice_id)
    return True
