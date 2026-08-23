# RecallGuard

An autonomous agent that watches FDA and USDA food recall feeds, fuzzy-matches them
against a business's own invoices with Gemini, and drafts a pull-checklist, a
notification, and a timestamped compliance record — flagging anything ambiguous for
human review instead of guessing.

Built for the **All Things Agentic Hackathon** (Devpost). Track: **The Taskmaster**.
Also eligible for Best Architectural Design, Best Multimodal UX, and
Individual/Hobbyist.

**Scout** is the product's detective persona — a corkboard-styled dashboard and voice
layered over the same backend below (color/type tokens: Anton display type, a red
pinned-evidence-card motif, a paw-stamp "CAUGHT IT" on confirmed matches).

## Status

**The full agent pipeline runs today, entirely locally** — recall ingestion, fuzzy
matching (Gemini), a photographed-invoice multimodal path, drafted compliance
artifacts, and a live dashboard, all backed by real tests and a real evaluation
harness. Only the **Cloud deployment** (Cloud Run / real Firestore / Pub/Sub /
Scheduler) is pending — blocked on a GCP billing verification issue, in progress. See
[`docs/PHASES.md`](docs/PHASES.md) for the exact, current state of every phase, and
[`docs/GCP_SETUP.md`](docs/GCP_SETUP.md) for the deployment runbook (ready to run the
moment billing clears).

## What's actually working

- **Recall ingestion** — live from openFDA (FSIS is built but currently geo-blocked in
  dev; see `docs/RISK_REGISTER.md`).
- **Fuzzy matching** — Gemini reasons about messy, abbreviated real invoice text
  against a recall, returning a confidence score and a stated reason, not a black-box
  yes/no. Verified to correctly avoid false positives on same-brand/wrong-flavor
  near-misses, and to correctly escalate genuinely ambiguous cases to a human instead
  of guessing.
- **Multimodal invoices** — a photographed/scanned invoice (not just clean CSV) is read
  directly by Gemini's vision input and flows through the identical pipeline.
- **Action Agent** — drafts a pull-checklist, supplier + health-department notification
  drafts (labeled `DRAFT — NOT SENT`, no send-capable code exists in the module — see
  `agents/action/action_agent.py`), and a real compliance-record PDF. Resumable if PDF
  generation fails partway through.
- **Dashboard** — a live corkboard UI (FastAPI + real data, not a mockup): the case
  board, a Recall Radar, a clean streak counter, and a case-file review screen with a
  working confirm/reject loop that genuinely runs the Action Agent.
- **A real N=30 evaluation** — see [`docs/EXPERIMENT.md`](docs/EXPERIMENT.md), in
  progress with honestly-labeled partial results, plus a second automated (non-LLM)
  comparison baseline.
- **61+ automated tests**, all passing, across every module above.

## Architecture

Three agents mapped 1:1 to three real jobs — **sense → decide → act**: a Recall
Monitor that normalizes FSIS/openFDA data, a Matching Agent that fuzzy-matches recalls
against invoices with Gemini, and an Action Agent that drafts the compliance
artifacts. Full diagram and failure-path notes: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Stack

Gemini (via the Gemini Developer API today; a one-line env flip to Vertex AI once GCP
billing clears) · Google ADK · Cloud Run · Firestore · Pub/Sub · Cloud Scheduler ·
FastAPI (dashboard) · reportlab (compliance PDFs).

## Run it locally

Needs Python 3.12+ and a free Gemini API key (no billing account, no GCP project) from
[aistudio.google.com](https://aistudio.google.com) — click "Get API key."

```bash
cd agents
pip install -r requirements.txt
cp .env.example .env        # paste your key into GOOGLE_API_KEY=
python test_gemini.py       # confirms the key works
```

**Run the full pipeline** (ingestion → matching → action → real compliance PDF, against
live recall data):

```bash
python run_matching_demo.py
```

**Run the dashboard** (reads whatever the pipeline above just produced):

```bash
uvicorn dashboard.server:app --reload --port 8010
# open http://127.0.0.1:8010/
```

**Run the test suite** (offline tests, no API key needed for most of them):

```bash
cd ingestion && python -m unittest discover -p "test_*.py" && cd ..
cd invoices && python -m unittest discover -p "test_*.py" && cd ..
cd action && python -m unittest discover -p "test_*.py" && cd ..
cd dashboard && python -m unittest discover -p "test_*.py" && cd ..
cd experiment && python -m unittest discover -p "test_*.py" && cd ..
```

**Run the N=30 evaluation** (paced against the free-tier Gemini quota, 20 req/day —
resumable):

```bash
# from agents/
python experiment/run_benchmark.py --limit 10     # repeat until 30/30
python experiment/summarize_results.py
python experiment/naive_baseline.py                # a second, non-LLM comparison point
```

## Deploy to Google Cloud

Not live yet — see [`docs/GCP_SETUP.md`](docs/GCP_SETUP.md) for the full runbook,
split into what's runnable today (project creation, local Firestore/Pub/Sub
emulators, testing the Docker container) and what needs GCP billing enabled first
(the actual Cloud Run deploy, real Firestore, real Pub/Sub, Cloud Scheduler).

## Scope

See [`docs/PLAN.md`](docs/PLAN.md) for the locked MVP scope — including what's
deliberately *not* built, and why (no real outbound sends, no chat interface, no
mobile app, no 50-state legal certification claim).

## Docs

| | |
|---|---|
| [docs/PHASES.md](docs/PHASES.md) | What's done, in progress, not started — the single source of truth for project status |
| [docs/PROGRESS.md](docs/PROGRESS.md) | Dated build log — every decision and why |
| [docs/PLAN.md](docs/PLAN.md) | Full build plan + verified hackathon rules |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System diagram + failure paths |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Firestore schema |
| [docs/AGENTS.md](docs/AGENTS.md) | Agent pseudocode |
| [docs/EXPERIMENT.md](docs/EXPERIMENT.md) | N=30 evaluation design + live results |
| [docs/RISK_REGISTER.md](docs/RISK_REGISTER.md) | Known risks + mitigations |
| [docs/GCP_SETUP.md](docs/GCP_SETUP.md) | Cloud deployment runbook |
| [docs/submission/](docs/submission/) | Devpost text, demo script, submission checklist |
| [agents/README.md](agents/README.md), [agents/dashboard/README.md](agents/dashboard/README.md), [agents/experiment/README.md](agents/experiment/README.md) | Per-component quick-starts |
