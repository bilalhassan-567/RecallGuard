# Billing Guard — hard spending cap setup

A Budget Alert by itself only sends an email; it cannot stop a charge. This sets up a
real hard stop: a Cloud Function that detaches the billing account from the project the
moment reported spend reaches the budget amount, which immediately kills further
billable usage.

Deployed 2026-08-26 as a precondition for doing any real Cloud Run/Firestore/Pub/Sub
work, since the billing account is backed by a card that belongs to someone else and
must never be charged. See `docs/PROGRESS.md` (2026-08-26 entries) for the full context.

## One-time setup

```bash
# 0. Auth (once per machine)
gcloud auth login

# 1. Pick the project this guards (must match the one billing is attached to)
export PROJECT_ID="<project-id>"
export BILLING_ACCOUNT_ID="<billing-account-id>"   # from `gcloud billing accounts list`
gcloud config set project "$PROJECT_ID"

# 2. Enable required APIs
gcloud services enable \
  cloudbilling.googleapis.com \
  cloudfunctions.googleapis.com \
  pubsub.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  --project="$PROJECT_ID"

# 3. Pub/Sub topic the budget will publish to
gcloud pubsub topics create billing-budget-alerts --project="$PROJECT_ID"

# 4. Deploy the function (source: infra/billing_guard/)
gcloud functions deploy disableBillingOnBudgetExceeded \
  --gen2 \
  --runtime=python312 \
  --region=us-central1 \
  --source=infra/billing_guard \
  --entry-point=disable_billing_on_budget_exceeded \
  --trigger-topic=billing-budget-alerts \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID" \
  --project="$PROJECT_ID"

# 5. Grant the function's own service account permission to detach billing.
#    Get the runtime service account first:
gcloud functions describe disableBillingOnBudgetExceeded \
  --gen2 --region=us-central1 --project="$PROJECT_ID" \
  --format="value(serviceConfig.serviceAccountEmail)"

#    Then grant it Billing Account Administrator ON THE BILLING ACCOUNT (not the
#    project — the API call to detach billing needs this at the account level):
gcloud billing accounts add-iam-policy-binding "$BILLING_ACCOUNT_ID" \
  --member="serviceAccount:<the-email-from-above>" \
  --role="roles/billing.admin"

# 6. Point the existing $1 budget at this Pub/Sub topic
gcloud billing budgets list --billing-account="$BILLING_ACCOUNT_ID"
#    ^ find the budget's ID (the "$1 Monthly Budget Alert" already created), then:
gcloud billing budgets update <BUDGET_ID> \
  --billing-account="$BILLING_ACCOUNT_ID" \
  --notifications-rule-pubsub-topic="projects/$PROJECT_ID/topics/billing-budget-alerts"
```

## Verifying it actually works

Don't trust a deploy that reports success — prove it:

```bash
# Manually publish a fake "over budget" notification and confirm billing actually
# gets detached (safe to do any time; it's exactly the real trigger payload).
# NOTE: pass plain JSON text here, NOT pre-base64-encoded — `gcloud pubsub
# publish` base64-encodes the message body itself as part of Pub/Sub's wire
# format, and the function only strips that one layer (matching what Eventarc
# actually delivers). Pre-encoding here double-encodes and the function will
# fail to parse it as JSON.
gcloud pubsub topics publish billing-budget-alerts \
  --project="$PROJECT_ID" \
  --message='{"budgetDisplayName": "test", "costAmount": 999, "budgetAmount": 1}'

# Check the function actually ran and disabled billing:
gcloud functions logs read disableBillingOnBudgetExceeded --gen2 --region=us-central1 --project="$PROJECT_ID" --limit=20

gcloud billing projects describe "$PROJECT_ID"
# billingEnabled should now be `false`. Re-link it before doing real work:
gcloud billing projects link "$PROJECT_ID" --billing-account="$BILLING_ACCOUNT_ID"
```

If the log doesn't show `BILLING DISABLED` and `billingEnabled` doesn't flip to
`false`, **do not treat this as protecting anything** — re-check IAM (step 5 is the
most common failure point) before proceeding to any billable work.

## Deployed state (verified live, 2026-08-26)

- Project: `project-04109a57-e726-450d-8b1` (relabeled "RecallGuard"; was an orphaned
  auto-created "My First Project" — confirmed empty of any resources before reuse)
- Billing account: `019A33-AD7C8E-1B325D`
- Function: `disableBillingOnBudgetExceeded`, region `us-central1`, gen2, ACTIVE
- Runtime service account: `306204883908-compute@developer.gserviceaccount.com`,
  granted `roles/billing.admin` on the billing account and `roles/run.invoker` on its
  own underlying Cloud Run service
- Pub/Sub topic: `billing-budget-alerts`, subscribed by the real "$1 Monthly Budget
  Alert" (`billingAccounts/019A33-AD7C8E-1B325D/budgets/1ff1fd5f-9fdd-474e-8d12-ce0bd970cef1`)
- **Live-tested end to end**: a real over-budget Pub/Sub message actually flipped
  `billingEnabled` to `false` on the project; billing was then re-linked to resume work.

## Gotchas hit getting here (so the next deploy doesn't re-discover them)

1. **Gen2 Cloud Functions on a new project needs manual IAM grants** the docs don't
   mention up front: `roles/cloudbuild.builds.builder` for both the default compute SA
   and the Cloud Build service agent (build fails silently otherwise — "missing
   permission on the build service account"), and `roles/run.invoker` for the trigger's
   service account on the function's own underlying Cloud Run service (Eventarc trigger
   fails with "not authenticated" otherwise, even though the function deployed fine).
2. **Do not pre-base64-encode a manual test message.** `gcloud pubsub topics publish
   --message=<text>` base64-encodes the body itself as part of Pub/Sub's wire format —
   passing already-encoded content double-encodes it, and the function's single decode
   (which correctly mirrors what Eventarc actually delivers) will silently unwrap to
   your own base64 string instead of JSON, failing to parse.
3. **On Windows, don't pass a JSON string with embedded double quotes as a `gcloud`
   argument at all** — `gcloud.cmd` is a batch file, and Windows routes batch-file
   argument passing through `cmd.exe`'s quoting rules, which mangle embedded `"`
   unpredictably. The reliable way to test manually from PowerShell: skip the CLI
   entirely and POST straight to the Pub/Sub REST API
   (`https://pubsub.googleapis.com/v1/projects/<id>/topics/<topic>:publish`) via
   `Invoke-RestMethod` with a bearer token from `gcloud auth print-access-token` — no
   argument quoting involved at all.
