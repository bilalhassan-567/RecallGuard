# RecallGuard

An autonomous agent that watches FDA and USDA food recall feeds, matches them against a
business's own invoices, and drafts a pull-checklist, a notification, and a timestamped
compliance record — flagging anything ambiguous for human review instead of guessing.

Built for **All Things Agentic Hackathon** (Devpost), track: **The Taskmaster.**

**Status: documentation / pre-build.** The full plan, architecture, and phase-by-phase
status live in [`docs/`](docs/) — start with [`docs/PHASES.md`](docs/PHASES.md) for what's
done and what's next. Spin-up instructions land here once there's something to spin up.

## Stack

Gemini (Vertex AI) · Google ADK · Cloud Run · Firestore · Pub/Sub · Cloud Scheduler.

## Why three agents

RecallGuard runs three agents mapped 1:1 to three real jobs — **sense → decide → act**:
a Recall Monitor that normalizes FSIS/openFDA data, a Matching Agent that fuzzy-matches
recalls against invoices with Gemini (returning a confidence score and stated reasoning,
not a black-box yes/no), and an Action Agent that drafts the compliance artifacts. Full
architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Scope

See [`docs/PLAN.md`](docs/PLAN.md) for the locked MVP scope — including what's deliberately
*not* being built, and why.

## Docs

| | |
|---|---|
| [docs/PHASES.md](docs/PHASES.md) | What's done, in progress, not started |
| [docs/PROGRESS.md](docs/PROGRESS.md) | Dated build log |
| [docs/PLAN.md](docs/PLAN.md) | Full build plan |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System diagram + failure paths |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Firestore schema |
| [docs/AGENTS.md](docs/AGENTS.md) | Agent pseudocode |
| [docs/EXPERIMENT.md](docs/EXPERIMENT.md) | Evaluation design + results |
| [docs/submission/](docs/submission/) | Devpost text, demo script, submission checklist |
