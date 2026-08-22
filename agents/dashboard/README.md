# dashboard/ — quick start

The "Scout" corkboard dashboard — reads real data from the local storage stand-in
(`agents/storage.py`), same Firestore-shaped collection addressing that swaps to real
Firestore later without a UI rewrite.

## Get real data in first

The dashboard just renders whatever's in `agents/local_data/` — it doesn't generate
anything itself. Populate it one of two ways:

- **`python run_matching_demo.py`** (from `agents/`) — the real pipeline, live Gemini
  calls, real recalls, real invoices. Preferred, but costs API quota (free tier is
  20 requests/day per model — see `docs/RISK_REGISTER.md`).
- **`python seed_dashboard_data.py`** (from `agents/`) — no Gemini calls. Fetches live
  recall data from openFDA (unlimited) and reuses real match/reasoning text already
  captured from earlier live runs this session (see the script's own docstring — not
  fabricated, just replayed). Use this when quota is tight and you just need something
  real on screen.

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
  Agent and produces a real compliance PDF in `agents/local_data/artifacts/`, exactly
  like an auto-actioned match would. Verified end-to-end with a headless-browser test
  (see `docs/PROGRESS.md`, 2026-08-23).
- The page polls `/api/state` every 5s — near-real-time, matching `docs/ARCHITECTURE.md`.

## What's not built yet

Recall Radar map, streak counter, and the animated pin-and-string visual between a
recall and its matching evidence card (the original mockup hand-positions these for
exactly 2 pairs — doing that generically for a variable-length list needs real layout
logic, deferred; see `docs/PLAN.md`'s Day 8 note about keeping the UI simple for a
Taskmaster submission over cosmetic polish).
