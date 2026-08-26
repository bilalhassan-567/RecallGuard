# dashboard/ — quick start

The "Scout" corkboard dashboard — FastAPI backend + a single-file vanilla-JS frontend.
Reads through `agents/storage.py`, which is backed by either a local JSON stand-in or
real Firestore (`USE_FIRESTORE=TRUE`) behind the identical call shape — same code
either way. **Live on Cloud Run today**, reading real Firestore:
https://recallguard-dashboard-306204883908.us-central1.run.app/

## Get real data in locally

The dashboard just renders whatever's in storage — it doesn't generate anything
itself. Populate it one of these ways:

- **Upload an invoice through the dashboard's own Invoices panel** — a CSV (free,
  instant) or a photographed invoice (one real Gemini vision call). This is the actual
  live feature now, not just a developer script.
- **`python run_matching_demo.py`** (from `agents/`) — the real pipeline, live Gemini
  calls, real recalls, real invoices. Costs API quota (free tier is 20 requests/day per
  model — see `docs/RISK_REGISTER.md`).
- **`python seed_dashboard_data.py`** (from `agents/`) — no Gemini calls. Fetches live
  recall data from openFDA (unlimited) and reuses real match/reasoning text already
  captured from earlier live runs (see the script's own docstring — not fabricated,
  just replayed). Use this when quota is tight and you just need something real on
  screen.

## Run it

```
cd agents
uvicorn dashboard.server:app --reload --port 8010
```

Open http://127.0.0.1:8010/. (Picked 8010, not 8000 — something else on this machine
already listens on 8000.)

## What's wired up for real

- The corkboard case board reads live from `businesses/{id}/matches` + `recalls/{id}`.
- "Needs Your Nose" reads live from the pending `review_queue`.
- Clicking **Review** opens the case-file modal (confidence dial, Scout's actual stored
  reasoning) — not a mockup, real data.
- **Confirm Match** / **False Alarm** call real API endpoints
  (`orchestrator.resolve_review_item`) — confirming a match genuinely runs the Action
  Agent and produces a real compliance PDF, exactly like an auto-actioned match would.
- The **Recall Radar** plots real distribution-state data from live recalls, and the
  **clean-streak counter** is computed from real match timestamps — neither is a
  placeholder.
- The **Invoices panel**: drag-and-drop upload (CSV or photo, dispatched server-side by
  file extension), a list with real per-invoice reconciliation status computed fresh
  from match records each time, a detail view with every line's full match history,
  search/filter, delete, and client-side CSV export. See `agents/invoices/invoice_store.py`
  for how a match gets traced back to its source invoice.
- The page polls `/api/state` and `/api/invoices` every 5s — near-real-time, matching
  `docs/ARCHITECTURE.md`. Search/filter inputs live outside the polled-and-rebuilt
  container specifically so a poll tick never wipes out mid-keystroke input.

## What's not built yet

The animated pin-and-string visual between a recall poster and its matching evidence
card (the original mockup hand-positions this for exactly 2 pairs — doing that
generically for a variable-length list needs real layout logic; cosmetic, lowest
priority per `docs/PLAN.md`'s Day 8 note about keeping the UI simple for a Taskmaster
submission over cosmetic polish).
