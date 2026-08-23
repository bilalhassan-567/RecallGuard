"""Action Agent (ADK agent #3 in docs/AGENTS.md) — turns a confirmed high-confidence
match into a pull-checklist, notification drafts, and a compliance record.

SECURITY / SAFETY DESIGN (read before touching this file):

1. **No LLM call happens in this module, at all.** By the time a match reaches here, the
   Matching Agent has already done the one reasoning step that needs an LLM. Everything
   below is deterministic templating over structured data we already control. This isn't
   a performance shortcut — it's a security decision: a compliance document that a health
   inspector or a supplier reads should not be able to be steered by adversarial text
   hidden inside a recall notice (prompt injection has nowhere to land if there's no
   prompt). The plan's "treat recall content as data, never instructions" rule is
   enforced structurally here, not just by policy.
2. **This module never sends anything over the network.** No smtplib, no HTTP POST to
   any notification/email API — check the imports below, there aren't any that could.
   Every "notification" produced is a draft file, explicitly labeled DRAFT / NOT SENT.
   This matches the MVP's deliberate scope cut in docs/PLAN.md: autonomous external
   actions are out of scope for the hackathon build, on purpose, not as an oversight.
3. **Structural refusal, not just caller discipline.** `run_action_agent` re-checks
   `match["status"] == "auto_actioned"` itself and raises if it isn't — so a bug upstream
   (e.g. a UI that calls this on a `pending_review` match by mistake) fails loudly here
   instead of silently drafting an action on an unconfirmed match.
4. **All external/untrusted text is escaped before it reaches the PDF renderer**
   (`_escape` below) — reportlab's Paragraph flowable interprets a subset of markup tags,
   so unescaped recall/invoice text could break rendering or, worse, inject formatting.
   Never pass raw external text into a Paragraph without going through `_escape` first.
5. **Filenames are derived only from IDs we sanitize ourselves** (`_safe_filename`) —
   never built directly from free-text recall/invoice content, even though recall IDs
   originate from an external source (FSIS/openFDA) and are technically untrusted too.
"""
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as _escape

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # agents/ (storage.py)
import storage

import pdf_export  # sibling in agents/action/ — flat-import style, matches ingestion/invoices/matching

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "local_data" / "artifacts"

# Keyword -> storage hint. Deliberately simple keyword matching, not another LLM call —
# this is a minor convenience field on the checklist, not something worth spending a
# reasoning step (or an injection surface) on.
STORAGE_HINTS = [
    (("chip", "snack", "cracker", "cereal", "flour", "tortilla"), "dry storage / shelf"),
    (("cheese", "milk", "yogurt", "cream", "dairy"), "refrigerated - dairy section"),
    (("beef", "pork", "chicken", "meat", "bacon", "sausage"), "refrigerated/frozen - meat case"),
    (("lettuce", "spinach", "produce", "vegetable", "fruit"), "produce cooler"),
]


def generate_pull_checklist(match: dict, recall: dict) -> dict:
    line = match["invoiceLineRef"]
    return {
        "item": line.get("rawText", ""),
        "supplier": line.get("supplier", ""),
        "quantity": line.get("quantity", ""),
        "storageHint": _storage_hint(line.get("rawText", "") + " " + recall.get("productDescription", "")),
        "lotCode": recall.get("lotCodes") or ["not provided by source — check physical packaging"],
        "recallSource": recall.get("source", ""),
        "recallId": recall.get("sourceRecordId", ""),
    }


def generate_notification_drafts(match: dict, recall: dict, business: dict) -> dict:
    """Returns supplier + health-department drafts. DRAFT ONLY — see module docstring."""
    line = match["invoiceLineRef"]
    common_header = (
        f"[DRAFT — NOT SENT — generated {_now_iso()} by RecallGuard, requires human review "
        f"and manual sending]\n"
    )
    supplier_draft = (
        f"{common_header}\n"
        f"To: {line.get('supplier', 'Supplier')}\n"
        f"From: {business.get('name', 'Business')}\n"
        f"Subject: Recalled product received — {recall.get('productDescription', '')[:60]}\n\n"
        f"We received a shipment that appears to match an active recall:\n"
        f"  Product (as received): {line.get('rawText', '')}\n"
        f"  Matched recall: {recall.get('productDescription', '')}\n"
        f"  Recall source: {recall.get('source', '')} #{recall.get('sourceRecordId', '')}\n"
        f"  Hazard: {recall.get('hazardType', '')}\n"
        f"  Classification: {recall.get('classification', '')}\n\n"
        f"Please advise on return/disposal instructions for this shipment."
    )
    health_dept_draft = (
        f"{common_header}\n"
        f"To: Local Health Department\n"
        f"From: {business.get('name', 'Business')} ({business.get('address', '')})\n"
        f"Subject: Recalled product notice — {recall.get('productDescription', '')[:60]}\n\n"
        f"This is a notification that our establishment received product matching an "
        f"active {recall.get('classification', '')} recall:\n"
        f"  Product: {recall.get('productDescription', '')}\n"
        f"  Hazard: {recall.get('hazardType', '')}\n"
        f"  Source: {recall.get('source', '')} #{recall.get('sourceRecordId', '')}\n"
        f"  Detected via invoice from: {line.get('supplier', '')}, received {line.get('dateReceived', '')}\n"
        f"  Match confidence: {match.get('confidenceScore', '')}% — {match.get('reasoning', '')}\n"
    )
    return {"supplierDraft": supplier_draft, "healthDeptDraft": health_dept_draft}


def generate_compliance_record(match: dict, recall: dict, business: dict, checklist: dict) -> dict:
    return {
        "businessId": business.get("id", ""),
        "recallId": recall.get("sourceRecordId", ""),
        "recallSource": recall.get("source", ""),
        "detectedAt": _now_iso(),
        "matchConfidence": match.get("confidenceScore"),
        "matchReasoning": match.get("reasoning", ""),
        "invoiceLine": match["invoiceLineRef"].get("rawText", ""),
        "invoiceSupplier": match["invoiceLineRef"].get("supplier", ""),
        "actionsTaken": ["checklist_generated", "notification_drafted"],
        "checklist": checklist,
        "status": "draft_ready_for_human_review",
    }


def run_action_agent(match: dict, recall: dict, business: dict, match_id: str | None = None) -> dict:
    """The only entry point that should be called from outside this module. Refuses to
    run on anything but a confirmed auto_actioned match — see module docstring point 3.

    match_id should be the caller's own unique ID for this specific match (orchestrator.py
    generates one per match). Without it, this falls back to deriving one from
    recall+business alone — which silently collides (and overwrites a prior PDF/compliance
    record) whenever the same recall matches more than one invoice line for the same
    business. Found this the hard way on a real run where a recall matched both a CSV line
    and a photographed-invoice line for one business — always pass match_id when calling
    this from a real pipeline, not just in isolated tests."""
    if match.get("status") != "auto_actioned":
        raise ValueError(
            f"run_action_agent refuses to act on status={match.get('status')!r} — "
            "only 'auto_actioned' matches may reach the Action Agent. This is enforced "
            "here deliberately, not just by caller discipline."
        )

    if match_id is None:
        match_id = f"{recall.get('sourceRecordId', 'unknown')}_{business.get('id', 'unknown')}"
    safe_id = _safe_filename(match_id)
    business_id = business.get("id", "unknown")

    # Per-step state so a failure resumes from where it broke, not from scratch — see
    # docs/PLAN.md's failure-modes table: "match found, PDF generation fails -> workflow
    # resumes from the failed step." If PDF export throws (a real, plausible failure —
    # disk full, a bad character reaching the renderer despite the escaping) a retry
    # skips regenerating the checklist/drafts/record and just retries the PDF.
    progress = storage.get(f"businesses/{business_id}/action_progress", safe_id)
    if progress and progress.get("step") == "artifacts_ready":
        checklist = progress["checklist"]
        drafts = progress["drafts"]
        compliance_record = progress["complianceRecord"]
    else:
        checklist = generate_pull_checklist(match, recall)
        drafts = generate_notification_drafts(match, recall, business)
        compliance_record = generate_compliance_record(match, recall, business, checklist)
        storage.save(
            f"businesses/{business_id}/action_progress",
            safe_id,
            {"step": "artifacts_ready", "checklist": checklist, "drafts": drafts, "complianceRecord": compliance_record},
        )

    pdf_path = pdf_export.write_compliance_pdf(compliance_record, ARTIFACTS_DIR / f"{safe_id}.pdf")

    storage.save(f"businesses/{business_id}/compliance_log", safe_id, compliance_record)
    storage.save(f"businesses/{business_id}/action_progress", safe_id, {"step": "complete"})

    return {
        "checklist": checklist,
        "notificationDrafts": drafts,
        "complianceRecord": compliance_record,
        "compliancePdfPath": str(pdf_path),
    }


def _storage_hint(text: str) -> str:
    lowered = text.lower()
    for keywords, hint in STORAGE_HINTS:
        if any(k in lowered for k in keywords):
            return hint
    return "check all storage areas — product type unclear from description"


def _safe_filename(raw: str) -> str:
    """Strips anything that isn't alphanumeric/dash/underscore — defense in depth even
    though these IDs are already fairly well-formed, since recall IDs ultimately trace
    back to external sources (see module docstring point 5)."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "_", raw)
    return cleaned[:120] or "artifact"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
