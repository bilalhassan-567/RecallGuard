"""Ties ingestion -> matching -> action into one reusable pipeline run, and — unlike
run_matching_demo.py, which only prints — persists everything to the local storage
stand-in so the dashboard has real data to read: every recall, every match (including
rejected ones, for the false-negative audit the plan calls for), the review queue, and a
daily metrics rollup.

This is what a real trigger (Cloud Scheduler -> Pub/Sub, eventually) would call per
recall. For now it's called directly, in-process, since Phase 3 (the event backbone) is
blocked on GCP — see docs/PHASES.md.
"""
import sys
import time
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent
for sub in ("matching", "action"):
    sys.path.insert(0, str(AGENTS_DIR / sub))

import action_agent  # noqa: E402
import matching_agent  # noqa: E402
import storage  # noqa: E402


def process_recall(recall: dict, line_items: list[dict], business: dict) -> dict:
    """Runs the Matching Agent against one recall, persists every outcome, and runs the
    Action Agent for anything auto-actioned. Returns a summary for the caller to print/log."""
    business_id = business["id"]
    matches = matching_agent.match_recall_against_lines(recall, line_items)

    storage.save("recalls", recall["sourceRecordId"], recall)

    summary = {"recallId": recall["sourceRecordId"], "autoActioned": 0, "pendingReview": 0, "rejected": 0}
    detection_started_at = time.monotonic()

    for match in matches:
        match_id = str(uuid.uuid4())
        storage.save(f"businesses/{business_id}/matches", match_id, match)

        if match["status"] == "pending_review":
            summary["pendingReview"] += 1
            storage.save(
                f"businesses/{business_id}/review_queue",
                match_id,
                {
                    "matchId": match_id,
                    "reasonForFlag": match["reasoning"],
                    "reviewerDecision": None,
                    "decidedAt": None,
                },
            )
        elif match["status"] == "auto_actioned":
            summary["autoActioned"] += 1
            match["actionResult"] = action_agent.run_action_agent(match, recall, business, match_id=match_id)
        else:
            summary["rejected"] += 1

    _update_daily_metrics(business_id, summary, time.monotonic() - detection_started_at)
    return {"summary": summary, "matches": matches}


def _update_daily_metrics(business_id: str, summary: dict, detection_seconds: float) -> None:
    metrics_id = f"{business_id}_{date.today().isoformat()}"
    existing = storage.get("metrics", metrics_id) or {
        "recallsChecked": 0,
        "matchesFound": 0,
        "avgTimeToDetectionSeconds": 0.0,
        "falsePositiveCount": 0,
        "lastUpdated": None,
    }
    matches_found = summary["autoActioned"] + summary["pendingReview"]
    total_checked = existing["recallsChecked"] + 1
    # running average, not a full recompute — fine at this scale, matches the plan's
    # note that metrics/{businessId}_daily is a rollup, recompute-safe if ever wrong.
    existing["avgTimeToDetectionSeconds"] = (
        existing["avgTimeToDetectionSeconds"] * existing["recallsChecked"] + detection_seconds
    ) / total_checked
    existing["recallsChecked"] = total_checked
    existing["matchesFound"] += matches_found
    existing["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    storage.save("metrics", metrics_id, existing)


def resolve_review_item(business_id: str, match_id: str, decision: str) -> dict:
    """decision: 'confirmed' or 'rejected'. Called from the dashboard's Confirm/False
    Alarm buttons. Confirming a review-queue item runs the Action Agent on it — a human
    just did the confidence check the model couldn't, so it's safe to act now."""
    if decision not in ("confirmed", "rejected"):
        raise ValueError(f"decision must be 'confirmed' or 'rejected', got {decision!r}")

    review_item = storage.get(f"businesses/{business_id}/review_queue", match_id)
    if review_item is None:
        raise ValueError(f"no review_queue item {match_id} for business {business_id}")

    review_item["reviewerDecision"] = decision
    review_item["decidedAt"] = datetime.now(timezone.utc).isoformat()
    storage.save(f"businesses/{business_id}/review_queue", match_id, review_item)

    match = storage.get(f"businesses/{business_id}/matches", match_id)
    if match is None:
        raise ValueError(f"no match record {match_id} for business {business_id}")

    if decision == "confirmed":
        recall = storage.get("recalls", match["recallId"])
        business = {"id": business_id}
        match["status"] = "auto_actioned"  # human confirmed it — safe to act now
        storage.save(f"businesses/{business_id}/matches", match_id, match)
        action_agent.run_action_agent(match, recall, business, match_id=match_id)
    else:
        match["status"] = "rejected"
        storage.save(f"businesses/{business_id}/matches", match_id, match)

    return review_item
