# RecallGuard — GCP Environment Setup

Scope, per `docs/PHASES.md`: GCP is only needed for going live — **Cloud Run** (public
hosting), real **Firestore** (replacing the local JSON stand-in in `agents/storage.py`),
real **Pub/Sub** (Phase 3 — currently `agents/orchestrator.py` calls the agents directly
in-process), and **Cloud Scheduler** (real recurring polling, currently run manually).
Gemini/ADK already works today via the AI Studio key and doesn't need any of this.

**Status as of 2026-08-23 (see `docs/PROGRESS.md`): GCP billing verification is blocked.**
Free-trial billing setup fails with `OR_BACR2_31` on both SadaPay cards — a known issue
where fintech/prepaid card BINs get blocked by Google's fraud checks. A support ticket is
filed and escalated (ETA 1–3 business days from Aug 22). **This blocks anything that
needs a billing-enabled project: Cloud Run deploy, real Firestore, real Pub/Sub, Cloud
Scheduler.** It does not block project creation, IAM, or local emulators — all of Part A
below works right now.

This doc is split accordingly:

- **Part A — do today**, no billing required.
- **Part B — do the moment the billing ticket clears.**
- **Part C — gotchas specific to this project.**

All commands are `gcloud` CLI, safe to run from PowerShell, cmd, or Git Bash on Windows —
they don't need WSL.

---

## Part A — Do today (no billing needed)

### A1. Install the gcloud CLI

**Done (2026-08-23)** — installed via `winget install --id Google.CloudSDK`, version
581.0.0, verified working in both PowerShell and Git Bash. If it's ever missing on a
fresh machine: download the installer from
https://cloud.google.com/sdk/docs/install (Windows tab), run it, then open a **new**
terminal (PATH only updates in new shells) and confirm with `gcloud version`.

### A2. Authenticate and pick an account

```
gcloud auth login
```

This opens a browser window — sign in with the Google account used for the $150
hackathon credit and the billing support ticket, so everything lines up under one
identity.

### A3. Create the GCP project

Project creation is free and doesn't need billing linked. Pick a globally-unique project
ID (project *names* can collide across users; project *IDs* can't):

```
gcloud projects create recallguard-<yoursuffix> --name="RecallGuard"
gcloud config set project recallguard-<yoursuffix>
```

Swap `<yoursuffix>` for something short and unique (initials + a few digits is fine).
Keep a note of the exact project ID — every command below assumes `gcloud config set
project` already points at it, so you won't need to repeat `--project` each time.

### A4. Service account for the backend

The Cloud Run services will eventually authenticate to Firestore/Pub/Sub as a service
account, not as you. Creating it now costs nothing and saves a step later:

```
gcloud iam service-accounts create recallguard-backend \
  --display-name="RecallGuard backend (Cloud Run -> Firestore/Pub/Sub)"
```

Role grants for this account happen in Part B, after the APIs it needs are enabled.

### A5. Local Firestore + Pub/Sub emulators — unblocks Phase 3 today

This is the one piece of real progress available *before* billing clears: the official
emulators run entirely on your machine, need no billing account, and speak the same wire
protocol as the real services — so `agents/storage.py`'s eventual Firestore-backed
rewrite, and the Pub/Sub wiring in Phase 3, can be built and tested now instead of
waiting on the support ticket.

```
gcloud components install cloud-firestore-emulator pubsub-emulator beta
```

Start them (two separate terminals, or background them):

```
gcloud emulators firestore start --host-port=localhost:8081
gcloud emulators pubsub start --host-port=localhost:8085
```

Point client code at the emulator instead of real GCP by setting env vars before running
your Python process (add these to `agents/.env` once you start the Firestore/Pub/Sub
rewrite — they're not needed yet for the current local-JSON `storage.py`):

```
FIRESTORE_EMULATOR_HOST=localhost:8081
PUBSUB_EMULATOR_HOST=localhost:8085
GOOGLE_CLOUD_PROJECT=recallguard-<yoursuffix>
```

The `google-cloud-firestore` and `google-cloud-pubsub` Python clients both auto-detect
these env vars and skip auth entirely when talking to an emulator. Add those two packages
to `agents/requirements.txt` when you actually start that rewrite — no need to install
them before then.

### A6. Test the dashboard container locally (no GCP account needed at all)

`Dockerfile` and `.dockerignore` (repo root) are ready — this validates the exact image
Cloud Run will run, before Cloud Run itself is reachable. **Needs Docker Desktop
installed first — not yet on this machine as of 2026-08-23; optional, since `gcloud run
deploy --source .` in Part B builds remotely via Cloud Build and doesn't need local
Docker at all. Install Docker only if you want to test the container locally before
that.**

```
docker build -t recallguard-dashboard .
docker run --rm -p 8080:8080 --env-file agents/.env recallguard-dashboard
```

Open http://localhost:8080/. If this works, `gcloud run deploy --source .` in Part B is
close to a formality.

### A7. Check the billing ticket

No `gcloud` command surfaces support-ticket status — check
https://console.cloud.google.com/support/cases in the browser, under the Google account
you filed it from. Worth checking daily rather than waiting for an email, since the first
reply was a generic canned response before the follow-up got it escalated.

---

## Part B — Once the billing ticket clears

Run `gcloud billing accounts list` first — if it returns an account, billing is
unblocked and you can proceed. Link it to the project:

```
gcloud billing projects link recallguard-<yoursuffix> --billing-account=<BILLING_ACCOUNT_ID>
```

### B1. Enable the required APIs

```
gcloud services enable ^
  run.googleapis.com ^
  firestore.googleapis.com ^
  pubsub.googleapis.com ^
  cloudscheduler.googleapis.com ^
  cloudbuild.googleapis.com ^
  artifactregistry.googleapis.com ^
  aiplatform.googleapis.com
```

(`^` is the Windows cmd line-continuation character; use `` ` `` in PowerShell, or `\` in
Git Bash/WSL. `aiplatform.googleapis.com` is for Vertex AI — only needed once/if you flip
`GOOGLE_GENAI_USE_VERTEXAI=TRUE`; skip it if staying on the AI Studio key.)

### B2. Create the Firestore database

One Firestore database per project, native mode (not Datastore mode — native mode is
what the security-rules syntax in `firestore.rules` assumes). Pick a region close to
your users; `us-central1` is a safe default and matches the FSIS-reachability note in
Part C:

```
gcloud firestore databases create --location=us-central1 --type=firestore-native
```

Deploy the rules and indexes already written for you (`firestore.rules`,
`firestore.indexes.json`, repo root) via the Firebase CLI (works fine against a plain GCP
project, no Firebase project needed):

```
npm install -g firebase-tools
firebase login
firebase deploy --only firestore:rules,firestore:indexes --project recallguard-<yoursuffix>
```

`firestore.rules` scopes every read/write to the caller's `businessId`, matching the
requirement in `docs/DATA_MODEL.md`. Read the comments at the top of the file — until
real end-user auth exists, the Cloud Run backend should talk to Firestore via the service
account from A4 (which these rules don't restrict), not have the browser hit Firestore
directly.

### B3. Grant the service account access

```
gcloud projects add-iam-policy-binding recallguard-<yoursuffix> ^
  --member="serviceAccount:recallguard-backend@recallguard-<yoursuffix>.iam.gserviceaccount.com" ^
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding recallguard-<yoursuffix> ^
  --member="serviceAccount:recallguard-backend@recallguard-<yoursuffix>.iam.gserviceaccount.com" ^
  --role="roles/pubsub.editor"
```

### B4. Pub/Sub — the `recall.detected` topic

Matches `docs/ARCHITECTURE.md`'s event backbone:

```
gcloud pubsub topics create recall.detected
gcloud pubsub subscriptions create recall-detected-matching-sub --topic=recall.detected
```

A push subscription (versus this default pull one) becomes the right choice once the
Matching Agent is its own Cloud Run service with an HTTP endpoint — revisit then.

### B5. Deploy the dashboard to Cloud Run

```
gcloud run deploy recallguard-dashboard --source . --region us-central1 ^
  --allow-unauthenticated ^
  --service-account recallguard-backend@recallguard-<yoursuffix>.iam.gserviceaccount.com ^
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=FALSE,GEMINI_MODEL=gemini-3.5-flash
```

Don't put `GOOGLE_API_KEY` in `--set-env-vars` (that lands in plaintext in the Cloud Run
revision config, visible to anyone with viewer access) — Phase 1's checklist already
calls for Secret Manager instead:

```
gcloud secrets create google-api-key --data-file=- <<< "YOUR_KEY_HERE"
gcloud run deploy recallguard-dashboard --source . --region us-central1 ^
  --allow-unauthenticated ^
  --service-account recallguard-backend@recallguard-<yoursuffix>.iam.gserviceaccount.com ^
  --set-secrets GOOGLE_API_KEY=google-api-key:latest ^
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=FALSE,GEMINI_MODEL=gemini-3.5-flash
```

(On Windows, `<<<` heredoc syntax needs Git Bash/WSL — in PowerShell, write the key to a
temp file first and use `--data-file=path\to\file`, then delete the file.)

Cloud Run scales to zero by default (no `--min-instances` flag needed) — matches
`docs/ARCHITECTURE.md`'s note that this keeps cost near-free between polls.

### B6. Cloud Scheduler — the real recurring poll

This assumes the Recall Monitor agent has an HTTP entrypoint deployed to Cloud Run (it
doesn't yet — `orchestrator.py`'s docstring says the trigger chain "for now... called
directly, in-process" since Phase 3 is blocked on GCP). Once that service exists:

```
gcloud scheduler jobs create http recall-monitor-poll ^
  --schedule="*/30 * * * *" ^
  --uri="https://<monitor-service-url>/poll" ^
  --http-method=POST ^
  --oidc-service-account-email=recallguard-backend@recallguard-<yoursuffix>.iam.gserviceaccount.com ^
  --location=us-central1
```

`--oidc-service-account-email` is what lets Scheduler call an authenticated (not
`--allow-unauthenticated`) Cloud Run service — the Monitor agent doesn't need to be
public the way the dashboard does.

---

## Part C — Project-specific gotchas

- **Region: use `us-central1` (or another US region) throughout, deliberately.** The
  open item in `docs/PHASES.md`/`PROGRESS.md` about FSIS 403'ing from dev — "re-test FSIS
  once Cloud Run is deployed in a US region, a US-based Google Cloud egress IP might not
  hit the same block" — only gets tested if the Monitor service actually runs in a US
  region. Keep every resource (Firestore, Cloud Run, Scheduler) in the same region to
  avoid cross-region latency/cost.
- **Splitting the agents into separate Cloud Run services is a separate, later step,**
  not covered here. Right now `agents/orchestrator.py` calls the Matching and Action
  agents as in-process Python calls; `docs/ARCHITECTURE.md` calls for Monitor, Matching,
  and Action to each be their own Cloud Run service wired through Pub/Sub. This doc gets
  you the *infrastructure* (project, APIs, Firestore, the topic, Scheduler, one deployed
  Cloud Run service for the dashboard) — turning the three agent modules into separately
  deployable HTTP services is Phase 3 code work, not environment setup.
- **Don't burn the free-tier Gemini quota testing GCP plumbing.** `docs/PROGRESS.md`
  notes the day's free-tier quota got used up on testing across every phase — Firestore/
  Pub/Sub/Cloud Run setup and testing doesn't call Gemini at all, so it's safe to do
  freely, but keep that in mind once you're testing the full pipeline end-to-end on
  Cloud Run.
- **`agents/.env` never leaves your machine or the emulator setup** — it's gitignored
  already (verified in `docs/PROGRESS.md`). The Cloud Run deploy commands above use
  Secret Manager / `--set-env-vars` instead, on purpose — don't `COPY` a real `.env` into
  the Docker image (the `.dockerignore` already excludes it).
