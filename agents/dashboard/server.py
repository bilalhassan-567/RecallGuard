"""RecallGuard dashboard — reads real data from the local storage stand-in
(agents/storage.py) and serves the "Scout" corkboard UI. No GCP needed: this is the same
FastAPI/Firestore-shaped design that swaps to real Cloud Run + Firestore later without a
UI rewrite, just a different storage.py backend.

Run from agents/: uvicorn dashboard.server:app --reload --port 8000
Then open http://127.0.0.1:8000/
"""
import io
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # agents/ (orchestrator.py, storage.py)
sys.path.insert(0, str(Path(__file__).resolve().parent))  # this dir (us_state_positions.py) —
# needed because uvicorn loads this file as the `dashboard` package's `server` submodule,
# so its own directory isn't on sys.path the way a standalone script's would be.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "invoices"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "action"))
import action_agent  # noqa: E402
import csv_parser  # noqa: E402
import image_parser  # noqa: E402
import invoice_store  # noqa: E402
import orchestrator  # noqa: E402
import storage  # noqa: E402
import us_state_positions  # noqa: E402

app = FastAPI(title="RecallGuard Dashboard")

STATIC_DIR = Path(__file__).resolve().parent / "static"
DEFAULT_BUSINESS_ID = "demo-biz-1"  # single-business demo; a real deploy is per-session-auth


@app.get("/", response_class=HTMLResponse)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/state")
def get_state(business_id: str = DEFAULT_BUSINESS_ID) -> dict:
    business = storage.get("businesses", business_id) or {"id": business_id, "name": "Unknown business"}
    matches = storage.list_collection(f"businesses/{business_id}/matches")

    cases = []
    for match in matches:
        recall = storage.get("recalls", match.get("recallId"))
        if recall is None:
            continue
        cases.append({"match": match, "recall": recall})

    review_items = storage.list_collection(f"businesses/{business_id}/review_queue")
    review_queue = []
    for item in review_items:
        if item.get("reviewerDecision") is not None:
            continue  # already decided, not pending anymore
        match = storage.get(f"businesses/{business_id}/matches", item["matchId"])
        if match is None:
            continue
        recall = storage.get("recalls", match.get("recallId"))
        review_queue.append({"reviewItem": item, "match": match, "recall": recall})

    all_metrics = storage.list_collection("metrics")
    business_metrics = [m for m in all_metrics if m["_id"].startswith(f"{business_id}_")]

    return {
        "business": business,
        "cases": cases,
        "reviewQueue": review_queue,
        "metrics": _aggregate_metrics(business_metrics),
        "radar": _radar_pings(cases),
        "streakDays": _streak_days(business, matches),
    }


@app.post("/api/review/{match_id}/confirm")
def confirm_review(match_id: str, business_id: str = DEFAULT_BUSINESS_ID) -> dict:
    return _resolve(business_id, match_id, "confirmed")


@app.post("/api/review/{match_id}/reject")
def reject_review(match_id: str, business_id: str = DEFAULT_BUSINESS_ID) -> dict:
    return _resolve(business_id, match_id, "rejected")


SUPPORTED_IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")


@app.get("/api/invoices")
def list_invoices(business_id: str = DEFAULT_BUSINESS_ID, q: str = "", status: str = "") -> list[dict]:
    invoices = invoice_store.list_invoices(business_id)
    if q:
        q_lower = q.lower()
        invoices = [
            inv for inv in invoices
            if q_lower in inv["sourceFileName"].lower() or q_lower in inv["supplier"].lower()
        ]
    if status:
        invoices = [inv for inv in invoices if _invoice_status(inv) == status]
    return invoices


@app.get("/api/invoices/{invoice_id}")
def get_invoice(invoice_id: str, business_id: str = DEFAULT_BUSINESS_ID) -> dict:
    detail = invoice_store.get_invoice_detail(business_id, invoice_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"no invoice {invoice_id}")
    return detail


@app.post("/api/invoices/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    business_id: str = Form(DEFAULT_BUSINESS_ID),
    supplier: str | None = Form(None),
) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix == ".csv":
        source_type = "csv"
    elif suffix in SUPPORTED_IMAGE_SUFFIXES:
        source_type = "image"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"unsupported file type {suffix!r} — use .csv or a photo ({', '.join(SUPPORTED_IMAGE_SUFFIXES)})",
        )

    contents = await file.read()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        # Exactly one parser call per upload request — the only Gemini cost in this
        # endpoint is this single parse_image call, never retried or called twice.
        lines = csv_parser.parse_csv(tmp_path, supplier=supplier) if source_type == "csv" \
            else image_parser.parse_image(tmp_path, supplier=supplier)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    try:
        return invoice_store.create_invoice(
            business_id, file.filename or "unnamed", source_type, lines, supplier=supplier
        )
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))


@app.delete("/api/invoices/{invoice_id}")
def delete_invoice(invoice_id: str, business_id: str = DEFAULT_BUSINESS_ID) -> dict:
    if not invoice_store.delete_invoice(business_id, invoice_id):
        raise HTTPException(status_code=404, detail=f"no invoice {invoice_id}")
    return {"deleted": True}


@app.get("/api/compliance/{match_id}/pdf")
def get_compliance_pdf(match_id: str, business_id: str = DEFAULT_BUSINESS_ID):
    record = storage.get(f"businesses/{business_id}/compliance_log", match_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"no compliance record for match {match_id}")

    storage_path = record.get("pdfStoragePath")
    if storage_path:
        # Cloud mode: the PDF outlived the container that generated it, in GCS.
        from google.cloud import storage as gcs_storage
        client = gcs_storage.Client()
        blob = client.bucket(action_agent.compliance_bucket_name()).blob(storage_path)
        pdf_bytes = blob.download_as_bytes()
        return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf")

    # Local dev mode: no GCS involved, the PDF is still sitting on local disk.
    local_path = action_agent.ARTIFACTS_DIR / f"{match_id}.pdf"
    if not local_path.exists():
        raise HTTPException(status_code=404, detail=f"compliance PDF not found for match {match_id}")
    return FileResponse(local_path, media_type="application/pdf")


@app.get("/api/compliance/{match_id}/drafts")
def get_notification_drafts(match_id: str, business_id: str = DEFAULT_BUSINESS_ID):
    """The PDF only ever contained the compliance record, never the notification
    drafts — those were persisted correctly (fixed 2026-08-27) but nothing ever
    exposed them for a person to actually read. This closes that gap."""
    record = storage.get(f"businesses/{business_id}/compliance_log", match_id)
    if record is None or not record.get("notificationDrafts"):
        raise HTTPException(status_code=404, detail=f"no notification drafts for match {match_id}")
    drafts = record["notificationDrafts"]
    text = (
        f"{'=' * 70}\nSUPPLIER DRAFT\n{'=' * 70}\n{drafts.get('supplierDraft', '')}\n\n"
        f"{'=' * 70}\nHEALTH DEPARTMENT DRAFT\n{'=' * 70}\n{drafts.get('healthDeptDraft', '')}\n"
    )
    return StreamingResponse(io.BytesIO(text.encode("utf-8")), media_type="text/plain")


def _invoice_status(inv: dict) -> str:
    if inv["flaggedCount"] > 0:
        return "flagged"
    if inv["autoActionedCount"] > 0:
        return "actioned"
    return "clean"


def _resolve(business_id: str, match_id: str, decision: str) -> dict:
    try:
        return orchestrator.resolve_review_item(business_id, match_id, decision)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


def _radar_pings(cases: list[dict]) -> list[dict]:
    pings = []
    for case in cases:
        if case["match"]["status"] == "rejected":
            continue  # not case-worthy, matches the corkboard's own filtering
        ping_type = "match" if case["match"]["status"] == "auto_actioned" else "considered"
        for pos in us_state_positions.positions_for_states(case["recall"].get("distributionStates", [])):
            pings.append({**pos, "type": ping_type})
    return pings


def _streak_days(business: dict, matches: list[dict]) -> int:
    """Days since the most recent auto-actioned match — 0 if one landed today. With no
    matches yet, days since the business was registered (clean since we started
    watching), or 0 if that's missing too rather than guessing."""
    auto_actioned_dates = [m["createdAt"] for m in matches if m.get("status") == "auto_actioned" and m.get("createdAt")]
    reference = max(auto_actioned_dates) if auto_actioned_dates else business.get("registeredAt")
    if not reference:
        return 0
    then = datetime.fromisoformat(reference)
    return max(0, (datetime.now(timezone.utc) - then).days)


def _aggregate_metrics(metrics_rows: list[dict]) -> dict:
    if not metrics_rows:
        return {"recallsChecked": 0, "matchesFound": 0, "avgTimeToDetectionSeconds": 0}
    return {
        "recallsChecked": sum(m.get("recallsChecked", 0) for m in metrics_rows),
        "matchesFound": sum(m.get("matchesFound", 0) for m in metrics_rows),
        "avgTimeToDetectionSeconds": round(
            sum(m.get("avgTimeToDetectionSeconds", 0) for m in metrics_rows) / len(metrics_rows), 2
        ),
    }
