"""Cloud Function entry points for Phase 3, the event backbone:

    Cloud Scheduler --HTTP--> poll_recalls --publish--> Pub/Sub `recall-detected`
        --push--> on_recall_detected --> orchestrator.process_recall (unchanged)

Deployed from this same `agents/` source tree the Dockerfile already uses (same
requirements.txt, same modules), with two separate `gcloud functions deploy` calls
against two different --entry-point values — see infra/EVENT_BACKBONE_SETUP.md.

Deliberately reuses orchestrator.process_recall as-is rather than re-implementing
matching/routing here — that function's own docstring already says this is what a
real trigger would call per recall (written before Phase 3 was unblocked).

Cost note: poll_recalls never calls Gemini — it only fetches openFDA (free, no quota)
and dedups against Firestore's `recalls` collection. The one Gemini call per genuinely
new recall happens downstream, inside orchestrator.process_recall -> matching_agent,
exactly the same one-call-per-recall cost as running the pipeline locally.
"""
import base64
import json
import os
import sys
from pathlib import Path

import functions_framework
from google.cloud import pubsub_v1

AGENTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AGENTS_DIR / "ingestion"))

import normalize  # noqa: E402
import openfda_client  # noqa: E402
import orchestrator  # noqa: E402
import storage  # noqa: E402

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
TOPIC_ID = os.environ.get("RECALL_TOPIC", "recall-detected")
DEMO_BUSINESS_ID = os.environ.get("DEMO_BUSINESS_ID", "demo-biz-1")

_publisher = None


def _publisher_client():
    global _publisher
    if _publisher is None:
        _publisher = pubsub_v1.PublisherClient()
    return _publisher


@functions_framework.http
def poll_recalls(request):
    """HTTP entry point, triggered by Cloud Scheduler. Fetches recent openFDA recalls,
    skips anything already processed (dedup via the `recalls` Firestore collection,
    which orchestrator.process_recall writes to for every recall it handles), and
    publishes only genuinely new ones for the matcher to pick up."""
    days = int(request.args.get("days", 7)) if request else 7
    from_date = _date_days_ago(days)
    raw_recalls = openfda_client.fetch_since(from_date)

    new_count = 0
    for raw in raw_recalls:
        recall = normalize.normalize_openfda(raw)
        recall_id = recall["sourceRecordId"]
        if not recall_id:
            # A handful of openFDA records are missing recall_number entirely — real
            # data messiness, not a bug. Log and skip rather than crash the whole poll
            # or publish an unaddressable recall downstream.
            print(f"WARNING: skipping a record with no recall_number, event_id={raw.get('event_id', 'unknown')}")
            continue
        if storage.get("recalls", recall_id) is not None:
            continue
        topic_path = _publisher_client().topic_path(PROJECT_ID, TOPIC_ID)
        _publisher_client().publish(topic_path, json.dumps(recall).encode("utf-8"))
        new_count += 1

    return {"checked": len(raw_recalls), "newRecalls": new_count}, 200


@functions_framework.cloud_event
def on_recall_detected(cloud_event):
    """Pub/Sub entry point — one genuinely new recall per invocation. Reads this
    business's invoice line items from Firestore (seeded by seed_invoices.py) and runs
    the exact same tested pipeline used locally, unchanged."""
    pubsub_message = cloud_event.data["message"]
    raw = base64.b64decode(pubsub_message["data"]).decode("utf-8")
    recall = json.loads(raw)

    business = storage.get("businesses", DEMO_BUSINESS_ID) or {"id": DEMO_BUSINESS_ID}
    line_items = storage.list_collection(f"businesses/{DEMO_BUSINESS_ID}/invoices")
    if not line_items:
        return
    orchestrator.process_recall(recall, line_items, business)


def _date_days_ago(days: int) -> str:
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
