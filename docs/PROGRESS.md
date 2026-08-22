# RecallGuard — Progress Log

Running record of what's actually built and verified, in plain terms. Newest entry at the
bottom. See `docs/PHASES.md` for the at-a-glance status board, and `docs/PLAN.md` for the
full build plan — this file is just "what happened, in order."

---

## 2026-08-22 — Documentation phase started

- Reviewed the full master build plan and the three UI/brand mockups (dashboard, case-file
  review, brand style guide) — all kept in `docs/master-workout/` (private, gitignored).
- Set up the repo: `git init`, `.gitignore` (excludes the master-workout folder, `CLAUDE.md`,
  secrets, venv/IDE noise), and `CLAUDE.md` with the working rules for this project —
  most notably: no AI co-author attribution anywhere, and a hard split between
  `docs/master-workout/` (private) and `docs/` (public, tracked).
- Built out the public `docs/` structure: phase board, this progress log, the plan,
  architecture, data model, agent logic, experiment design, risk register, and
  submission-asset drafts (Devpost description, demo script, checklist).
- No application code written yet — Phase 1 (Foundations / GCP setup) is next.

## 2026-08-22 — Full plan re-check against live Devpost rules

- Re-read the master build plan and all three UI mockups end to end, cross-checked against
  the public `docs/` set for gaps.
- Fetched the live Devpost rules (the internal plan didn't carry an exact deadline).
  Confirmed: deadline **Aug 31, 2026, 5pm PT**, submission period Aug 3–31, judging is a
  three-way 40/30/30 split (Innovation & Operational Utility / Architectural Discipline &
  Tech Stack / Demo & Production Readiness), category selection is exactly one of
  Taskmaster/Collaborative Partner/Fortified Enterprise Fleet, mandatory tech (Gemini
  3.5+, an ADK-family framework, a listed Cloud service) all already matches the locked
  stack. Updated `docs/PLAN.md`, `docs/PHASES.md`, and
  `docs/submission/submission-checklist.md` with the verified facts.
- **Key finding:** today (Aug 22) to the deadline is only 9 full calendar days, but the
  plan's schedule is written as 10 working days with Days 9–10 (real experiment + demo
  video + submission) both landing on Aug 31 itself if mapped 1:1. Flagged as the top
  open risk in `docs/PHASES.md` — needs a timeline decision before Phase 1 starts.
- Logged the remaining open blockers (GCP project status, FSIS API key confirmation,
  sample invoice sourcing, frontend framework choice, PDF library choice, team size) in
  `docs/PHASES.md` → Blockers / open questions.

## 2026-08-22 — Re-verified against the full official rules text

User pasted the complete Devpost page + Official Rules directly (more reliable than the
earlier fetched summary). Cross-checked and confirmed the deadline math (Aug 31 5pm PT =
Sep 1 5am GMT+5 — same instant, no discrepancy). Found several facts not previously
captured and added them to `docs/PLAN.md`, `docs/PHASES.md`, `docs/submission/
submission-checklist.md`, and `docs/RISK_REGISTER.md`:
- **$150 GCP credit request form deadline: Aug 28, 2026, 12pm PT** ("or while supplies
  last") — a real near-term action item, separate from the build schedule.
- **Judging Period runs through Oct 1, 2026** — a hosted URL (if offered) must stay
  available for testing until then, not just past the submission deadline.
- Official cost-saving guidance recommends **Gemini Flash by default**, escalating to Pro
  only for complex reasoning — directly relevant since the Matching Agent calls Gemini
  per invoice line.
- Taskmaster's Innovation criterion (40% weight) explicitly names a **"Bring Your Own
  Friction" (BYOF)** expectation — the project should read as solving a real, personal
  friction. Flagged as an open framing decision, not yet resolved.
No architecture or scope changes — this was a documentation-accuracy pass, plus new
near-term action items surfaced.

## 2026-08-22 — Three open decisions resolved

- **BYOF framing:** no personal food-service background exists — decided not to fabricate
  one. The submission narrative frames the problem honestly (a real gap small food
  businesses have, backed by the $74.7B/year foodborne-illness stat) and leans on the
  autonomous multi-step workflow half of the Innovation criterion instead. Added an
  `Inspiration` section with this guidance to `docs/submission/devpost-description.md`.
- **Hosting:** will host a live demo. Decided against splitting the deploy onto Vercel —
  the dashboard frontend goes on Cloud Run alongside the agents, so there's one platform,
  one Google Cloud story for the video, and no second integration surface to debug under
  time pressure. Cloud Run's scale-to-zero makes this ~free either way.
- **GCP status confirmed: starting from zero.** No project, no billing, no local `gcloud`
  CLI (checked — not on PATH). The $150 hackathon credit hasn't been requested yet; that's
  now the single most time-sensitive action item (form deadline Aug 28, 12pm PT, and it's
  a step only the user can do — tied to their own Google identity). Flagged as the very
  first action, ahead of any other Phase 1 work.
- **$150 credit form submitted.**

## 2026-08-22 — GCP free-trial billing blocked (SadaPay declined, support ticket filed)

- Free-trial billing setup failed with `OR_BACR2_31` on the user's SadaPay virtual
  Mastercard. Tried the physical SadaPay Mastercard too — same error. Researched the
  cause: fintech/prepaid card BINs (SadaPay, NayaPay) are broadly blocked by cloud
  providers' fraud checks for metered/postpaid billing, compounded by Pakistani banks'
  mandatory OTP-based 3D Secure, which Google Cloud's verification flow rejects. Both
  cards failing identically points to an issuer-level block, not a per-card issue.
- Filed a Google Cloud "Account Suspension / payment method error" support inquiry
  (helped draft the form fields: purpose, business/website = N/A individual entrant,
  additional info requesting manual ID-based verification as an alternative to card
  verification, referencing the already-submitted $150 credit request for legitimacy).
- First support reply (agent "Rea") was a generic canned response pointing to the list of
  supported card networks — didn't address the manual-verification request. Sent a
  follow-up pointing out SadaPay's card **is** on that supported-network list (Mastercard
  debit), so the block is issuer-specific, and re-asked for manual verification.
- **Update:** second reply confirms it's been escalated to Google's internal team for
  investigation — real progress, not another canned response. New estimate: 1–3 business
  days. That lands ~Aug 25–26, eating a meaningful chunk of the 9-day window — reinforces
  not waiting idle on this (see below).
- **Decision: don't let this block all progress.** Set up the Gemini API path via Google
  AI Studio (no billing account required) so agent/prompt development can proceed
  regardless of how the billing ticket resolves — see the next entry.

## 2026-08-22 — Phase 1 kickoff: local ADK + Gemini scaffolding (agents/)

Built out `agents/` so Phase 1 agent work can start today without GCP billing:
- `agents/requirements.txt` (`google-adk`, `google-genai`, `python-dotenv`) — installed
  into the local `.venv` cleanly (`google-adk` 2.7.1, `google-genai` 2.19.0), both import
  without errors.
- `agents/config.py` — shared `.env` loader (`GOOGLE_API_KEY`, `GEMINI_MODEL`, defaulting
  to `gemini-3.5-flash` per the hackathon's mandatory-tech + cost-guidance).
- `agents/test_gemini.py` — one-command smoke test to confirm an API key works before
  building anything on top of it.
- `agents/hello_agent/` — minimal ADK agent (`root_agent`), runnable via `adk run
  hello_agent` or `adk web` once a key is in `agents/.env`.
- Verified: `.gitignore` correctly excludes any real `agents/.env` while still tracking
  `agents/.env.example` (checked both directions with `git check-ignore` / `git add`).
- **Deliberately built on the Gemini Developer API (AI Studio key), not Vertex AI** —
  same `google-genai` SDK underneath, so flipping to Vertex AI later (once GCP billing
  clears) is a one-line env change (`GOOGLE_GENAI_USE_VERTEXAI=TRUE`), not a rewrite.
- **Confirmed working (2026-08-22):** user generated an AI Studio key, `python
  test_gemini.py` returned a clean response from `gemini-3.5-flash` with real prompt/
  response token counts. Model ID confirmed correct on the first try. Gemini path is
  fully unblocked regardless of the GCP billing ticket's outcome.
- **Also confirmed (2026-08-22):** `adk run hello_agent` works through the real ADK CLI,
  not just the raw SDK — agent loaded, responded correctly to a live prompt. (The agent's
  reply claimed "Gemini 2.5 Flash" — that's the model unreliably self-reporting its own
  name in prose, not authoritative; the real config is `test_gemini.py`'s printed model
  ID, confirmed by a successful API call.) **Phase 1 local scaffolding is done** — only
  "deployed to Cloud Run" remains, pending the GCP billing ticket.

## 2026-08-22 — Phase 2: recall ingestion clients built and (partly) verified

Researched the two open questions from the plan's risk list — FSIS auth requirements and
the openFDA query gotchas — by finding real, working reference implementations on GitHub
(`justanesta/food_safety_recalls`, `leelesemann-sys/food-recalls-database`) rather than
relying on docs alone, since the FSIS docs page itself was unreachable (Akamai-blocked,
see below).

**FSIS:** confirmed no API key is required — the reference repos call it anonymously with
just a `User-Agent` header. This resolves the original "confirm auth requirements" risk.
**But a new, more interesting problem surfaced:** every request from this dev sandbox got
403'd by Akamai bot-management, regardless of User-Agent (tried a browser UA and
`curl/7.88`, both failed identically) — while the *exact same test* against openFDA
succeeded cleanly. Pulled a real sample FSIS record from one repo's committed dataset
(`raw_data/usda_food_safety_recalls.json`) via a byte-range request to get exact field
names without needing the live API to work. Built `agents/ingestion/fsis_client.py`
matching the working reference pattern (90s timeout, retry with backoff, `curl/7.88`
User-Agent) — correct code, but **unverified from a real network yet**. Open question:
is this sandbox-specific, or would Cloud Run's IPs (also a "datacenter" ASN) hit the same
wall in production? Logged in `docs/RISK_REGISTER.md` and `docs/PHASES.md` as the next
thing to test — starting with the user's own machine.

**openFDA:** built `agents/ingestion/openfda_client.py`, tested live, works end-to-end —
36 real records fetched and normalized for an August 2026 date window. Found and fixed a
real bug in the process: `requests`' automatic URL-encoding was turning the literal `+`
in openFDA's `report_date:[X+TO+Y]` Lucene-style range syntax into `%2B`, which the API
rejected with a 500. Fixed by building the query string manually instead of passing it
through `params=`. (The plan's documented quoting/`.exact` gotchas were already known;
this encoding issue was a new one, only visible by actually running the code.)

**Normalization:** built `agents/ingestion/normalize.py` mapping both sources into the
`recalls/{recallId}` shape from `docs/DATA_MODEL.md`, using real field names pulled from
actual sample data (not guessed) — `field_recall_number`/`field_title`/etc. for FSIS,
`recall_number`/`product_description`/etc. for openFDA. Fixed a messiness bug here too:
openFDA's `distribution_pattern` field often carries a boilerplate sentence prefix
("The recalled product was distributed to the following states: MD, VA") — now stripped
before splitting into a states list, verified against live data (`["MD", "VA"]` clean).

**Not yet done:** unit tests against known historical recalls (the current smoke test
just proves the code runs, not that it's correct against ground truth) — deferred to
align with the N=30 ground-truth work in `docs/EXPERIMENT.md`, Phase 8. Firestore
writes not wired up yet (blocked on GCP project/billing, same as Phase 1's deploy step).

## 2026-08-23 — FSIS confirmed blocked from a real network too, not just the sandbox

User ran `test_ingestion.py` from their own machine (real Pakistani residential network).
openFDA: same clean success as the sandbox test. **FSIS: same 403 as the sandbox** — this
rules out "sandbox-specific datacenter IP" as the explanation. New working theory: a
geographic block on non-US traffic at the Akamai layer in front of this US federal (.gov)
site, since both failing networks are non-US. Decision: stop investigating this in dev —
not fixable from here. Updated `docs/PLAN.md` (section 1), `docs/PHASES.md`, and
`docs/RISK_REGISTER.md`: **openFDA is the primary/sole trigger source for now**; FSIS
gets re-tested once Cloud Run is deployed in a US region (a US-based egress IP might not
hit the same block) but nothing in the build should assume FSIS is available until proven
otherwise. This is also a genuine, real instance of the failure-handling behavior the
plan already designs for (retry/log/continue on an unreachable source) — not just a
hypothetical for the demo.

## 2026-08-23 — Phase 2 unit tests written and passing (11/11)

Closed the last open Phase 2 checklist item. `agents/ingestion/test_normalize.py` — 8
offline tests, no network: a real captured FSIS record (Brazilian Taste, #036-2025) used
as ground truth for `normalize_fsis`, plus full edge-case coverage of `_split_states`
(empty, "Nationwide", plain CSV, the boilerplate-prefix bug fixed earlier, single state
with no comma). `agents/ingestion/test_openfda_live.py` — 3 live tests against
`api.fda.gov`, pinned to two specific real recalls by exact `recall_number` (Uncle Ray's
potato chips, Class II; Selectos Latinos cottage cheese, Class I) rather than a date
window, so they stay stable over time — values match what was manually verified live
earlier in the session. Added `openfda_client.fetch_by_recall_number()` to support this.
All 11 tests pass. **Phase 2 is done, openFDA-only** — FSIS stays deferred until a
US-region Cloud Run test (see the 2026-08-23 entry above).
