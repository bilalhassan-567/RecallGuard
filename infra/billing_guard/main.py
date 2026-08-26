"""Hard spending cap for the RecallGuard GCP project.

A Cloud Billing budget alert (see ../BILLING_GUARD_SETUP.md) publishes to the
Pub/Sub topic this function is subscribed to every time spend crosses a
threshold. Most of those notifications are informational (50%/90%/100%/150%
of the budget) and are NOT reason to act on their own — Cloud Billing sends
the same message shape regardless of threshold, so this function makes its
own decision using the actual reported cost, not the alert firing itself.

The moment reported cost reaches or exceeds the budget amount, this detaches
the billing account from the project via the Cloud Billing API. That kills
billing-capable usage immediately (Cloud Run stops serving, further Firestore/
Pub/Sub usage is rejected, etc.) — a real stop, not just a notification email.

This is a backstop, not the primary safety mechanism: the project is designed
to stay inside GCP's permanent Always-Free tier (Cloud Run scale-to-zero,
Firestore/Pub/Sub/Scheduler under free quotas, Gemini via the free AI Studio
key rather than billed Vertex AI calls) so real spend is expected to be $0.
This function exists so a misconfiguration can't turn into an open-ended bill
on a card that isn't the project owner's.
"""

import base64
import json
import logging
import os

import functions_framework
from google.cloud import billing_v1

logging.basicConfig(level=logging.INFO)

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
PROJECT_NAME = f"projects/{PROJECT_ID}"


@functions_framework.cloud_event
def disable_billing_on_budget_exceeded(cloud_event):
    pubsub_message = cloud_event.data["message"]
    raw = base64.b64decode(pubsub_message["data"]).decode("utf-8")
    data = json.loads(raw)

    budget_name = data.get("budgetDisplayName", "unknown")
    cost_amount = data.get("costAmount", 0)
    budget_amount = data.get("budgetAmount", 0)

    logging.info(
        "Budget notification: budget=%s cost=%s of %s",
        budget_name, cost_amount, budget_amount,
    )

    if budget_amount <= 0:
        logging.warning("Budget amount missing/zero in notification — refusing to act blind.")
        return

    if cost_amount < budget_amount:
        logging.info("Under budget (%s < %s) — no action.", cost_amount, budget_amount)
        return

    client = billing_v1.CloudBillingClient()
    info = client.get_project_billing_info(name=PROJECT_NAME)

    if not info.billing_enabled:
        logging.info("Billing already disabled on %s — nothing to do.", PROJECT_ID)
        return

    client.update_project_billing_info(
        name=PROJECT_NAME,
        project_billing_info=billing_v1.ProjectBillingInfo(billing_account_name=""),
    )
    logging.warning(
        "BILLING DISABLED on %s — reported cost %s reached/exceeded budget %s (%s).",
        PROJECT_ID, cost_amount, budget_amount, budget_name,
    )
