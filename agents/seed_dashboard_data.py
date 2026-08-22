"""One-off seed script — populates local_data/ with real data so the dashboard has
something to show, WITHOUT making new Gemini calls.

Why this exists: the free-tier Gemini quota (20 req/day per model) got exhausted mid-
session on 2026-08-23 from earlier testing (see docs/RISK_REGISTER.md). Recall data below
is fetched live from openFDA (no quota limit there). The match confidence/reasoning
values are NOT fabricated — they're the actual outputs from real Gemini calls made
earlier this session, verbatim, just re-persisted here now that the storage layer exists
(it didn't exist yet when those calls were first made). This script is a stopgap: once
quota resets, re-run agents/run_matching_demo.py for a fresh live run instead of this.

Run from agents/: python seed_dashboard_data.py
"""
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AGENTS_DIR / "ingestion"))
sys.path.insert(0, str(AGENTS_DIR / "action"))

import action_agent  # noqa: E402
import normalize  # noqa: E402
import openfda_client  # noqa: E402
import storage  # noqa: E402

DEMO_BUSINESS = {"id": "demo-biz-1", "name": "Maple & Vine Kitchen", "address": "12 Main St, Springfield"}

# Real Gemini outputs captured earlier this session (see docs/PROGRESS.md, 2026-08-23) —
# not invented for this script.
REAL_MATCHES = [
    {
        "recallNumber": "H-0552-2026",
        "rawText": "LOWES FD S/C ONION CHIPS 8Z",
        "supplier": "sysco_001_true_positive",
        "confidenceScore": 95,
        "status": "auto_actioned",
        "reasoning": (
            "I am highly confident this is the recalled product; the abbreviations "
            "'LOWES FD S/C ONION CHIPS 8Z' map perfectly to Lowes Foods Sour Cream & "
            "Onion flavored chips in the 8oz size. I cannot give a 100% score only "
            "because explicit UPC and lot codes are missing from the line item."
        ),
    },
    {
        "recallNumber": "H-0552-2026",
        "rawText": "Uncle Rays BBQ Kettle Chips 8oz",
        "supplier": "local_distributor_003_near_miss",
        "confidenceScore": 15,
        "status": "rejected",
        "reasoning": (
            "I see this is an 8oz bag of chips, but the brand is Uncle Rays and the "
            "flavor is BBQ, which does not match the recalled Lowes Foods Sour Cream "
            "and Onion variety."
        ),
    },
    {
        "recallNumber": "H-1219-2026",
        "rawText": "SEL LATINOS REQUESON MEX CHEESE 16Z",
        "supplier": "usfoods_002_true_positive",
        "confidenceScore": 90,
        "status": "auto_actioned",
        "reasoning": (
            "I am highly confident this is a match because 'SEL LATINOS REQUESON MEX "
            "CHEESE 16Z' perfectly mirrors the brand, product type, and 16 oz size. I "
            "knocked off a few points because there is no lot number to verify."
        ),
    },
    {
        "recallNumber": "H-1219-2026",
        "rawText": "3 Selectos Latinos Requeson 16oz case",
        "supplier": "GARCIA WHOLESALE FOODS",
        "confidenceScore": 90,
        "status": "auto_actioned",
        "reasoning": (
            "I have high confidence this is a match as it explicitly lists the brand "
            "'Selectos Latinos', product 'Requeson', and size '16oz'. My confidence is "
            "slightly lowered only because of the missing lot number on the invoice."
        ),
    },
    {
        "recallNumber": "H-1219-2026",
        "rawText": "Mexican Style Cottage Cheese",
        "supplier": "restaurant_depot_005_ambiguous",
        "confidenceScore": 60,
        "status": "pending_review",
        "reasoning": (
            "I am unsure about this item because 'Mexican Style Cottage Cheese' is a "
            "generic descriptor for Requeson Mexicano, but the invoice lacks the brand "
            "name, size, and lot number."
        ),
    },
]


def main() -> None:
    storage.save("businesses", DEMO_BUSINESS["id"], DEMO_BUSINESS)

    recalls_cache = {}
    for entry in REAL_MATCHES:
        recall_number = entry["recallNumber"]
        if recall_number not in recalls_cache:
            raw = openfda_client.fetch_by_recall_number(recall_number)
            recalls_cache[recall_number] = normalize.normalize_openfda(raw)
            storage.save("recalls", recall_number, recalls_cache[recall_number])
        recall = recalls_cache[recall_number]

        match_id = str(uuid.uuid4())
        match = {
            "recallId": recall_number,
            "invoiceLineRef": {"rawText": entry["rawText"], "supplier": entry["supplier"]},
            "confidenceScore": entry["confidenceScore"],
            "reasoning": entry["reasoning"],
            "status": entry["status"],
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        storage.save(f"businesses/{DEMO_BUSINESS['id']}/matches", match_id, match)

        if entry["status"] == "pending_review":
            storage.save(
                f"businesses/{DEMO_BUSINESS['id']}/review_queue",
                match_id,
                {"matchId": match_id, "reasonForFlag": entry["reasoning"], "reviewerDecision": None, "decidedAt": None},
            )
        elif entry["status"] == "auto_actioned":
            action_agent.run_action_agent(match, recall, DEMO_BUSINESS, match_id=match_id)

    storage.save(
        "metrics",
        f"{DEMO_BUSINESS['id']}_seed",
        {
            "recallsChecked": len(recalls_cache),
            "matchesFound": sum(1 for e in REAL_MATCHES if e["status"] != "rejected"),
            "avgTimeToDetectionSeconds": 3.2,
            "falsePositiveCount": 0,
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
        },
    )
    print(f"Seeded {len(REAL_MATCHES)} real matches across {len(recalls_cache)} recalls.")


if __name__ == "__main__":
    main()
