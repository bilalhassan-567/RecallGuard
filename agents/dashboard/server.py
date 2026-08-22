"""RecallGuard dashboard — reads real data from the local storage stand-in
(agents/storage.py) and serves the "Scout" corkboard UI. No GCP needed: this is the same
FastAPI/Firestore-shaped design that swaps to real Cloud Run + Firestore later without a
UI rewrite, just a different storage.py backend.

Run from agents/: uvicorn dashboard.server:app --reload --port 8000
Then open http://127.0.0.1:8000/
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # agents/ (orchestrator.py, storage.py)
sys.path.insert(0, str(Path(__file__).resolve().parent))  # this dir (us_state_positions.py) —
# needed because uvicorn loads this file as the `dashboard` package's `server` submodule,
# so its own directory isn't on sys.path the way a standalone script's would be.
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
