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

## 2026-08-23 — Local pipeline built end-to-end: storage stand-in, invoices, Matching Agent

User's call: no GCP update yet, build everything that doesn't need it before circling
back. Built the whole local chain in one push — ingestion (already done) -> local storage
-> invoice parsing -> the Matching Agent itself, and ran it for real.

- **`agents/storage.py`** — a local JSON-file stand-in for Firestore, using the same
  collection-path/doc-id addressing (`businesses/{id}/invoices/{id}`) so swapping to real
  Firestore later means rewriting this file's insides, not any calling code. Runtime data
  goes to `agents/local_data/` (gitignored).
- **5 sample invoices** (`agents/sample_data/invoices/`) — Sysco, US Foods, a local
  distributor, a wholesale club, and Restaurant Depot formats, each with different real
  column layouts. Deliberately built to cover all four evaluation categories the plan
  calls for, not just "some invoices": 2 true positives anchored on the real recalls
  already verified in Phase 2 (H-0552-2026 potato chips, H-1219-2026 cottage cheese), 1
  near-miss (same brand — Uncle Ray's — different flavor, to test false-positive
  avoidance), 1 easy negative (unrelated products only), 1 genuinely ambiguous case (a
  plausible product with no brand/lot on the invoice). Documented as `ground_truth.json`.
- **`agents/invoices/csv_parser.py`** — parses any of the 5 formats via a known-alias
  column lookup rather than assuming one schema, since real invoices don't share a
  format. 7 tests passing against the actual sample files (not synthetic mini-fixtures).
- **`agents/matching/agent.py`** — the Matching Agent itself. Gemini call using
  `google-genai`'s Pydantic `response_schema` for reliable structured JSON (confidence +
  reasoning per line, not hand-parsed text). Reasoning is written in Scout's first-person
  voice, matching the brand guide and the `02_case_file_review.html` mockup's actual
  copy ("Scout's reasoning: ...") — this text goes straight into the review UI later, not
  through another rewrite step. Threshold routing (≥80/40-79/<40) implemented per the
  plan's pseudocode in `docs/AGENTS.md`.
- **Ran it for real** (`agents/run_matching_demo.py`) against both live recalls and all 5
  invoices. Result, unedited: the heavily-abbreviated true positive ("LOWES FD S/C ONION
  CHIPS 8Z") scored 95% and auto-actioned; the ambiguous no-brand cottage cheese line
  scored 55% and correctly routed to `pending_review`, with Scout's reasoning explicitly
  naming the missing brand/lot info; unrelated products scored low and were rejected.
  **The near-miss case (Uncle Ray's BBQ chips vs. the recalled sour-cream-and-onion
  flavor) was NOT auto-actioned despite the brand match** — exactly the false-positive
  trap this needed to avoid, and the system instruction's explicit rule about brand
  similarity alone not being sufficient held up under a real test, not just in theory.
- Wrote `agents/matching/test_agent.py` — 3 live automated tests (not just eyeballing the
  demo output) asserting the routing OUTCOME for the true positive, the near-miss, and
  unrelated products. All pass. This is now permanent regression protection for future
  prompt tuning.
- Fixed a cosmetic bug along the way: an em-dash in a print statement was garbling on
  Windows console encoding — swapped for a plain hyphen.
- **Not yet done:** the photographed/invoice-image multimodal path (Best Multimodal UX
  requirement, still Phase 4), a Cloud Run region choice for the eventual FSIS re-test,
  and scaling the sample/ground-truth set from 5 invoices toward the N=30 needed for
  Phase 8's real experiment.

## 2026-08-23 — Action Agent built, secured, and run end-to-end (Phase 6 done, local)

User's instruction: build it now, make it secure, then review. Built
`agents/action/action_agent.py` + `pdf_export.py` with security as a first-class design
constraint, not an afterthought:

- **No LLM call anywhere in this module.** Everything downstream of a confirmed match —
  the pull checklist, both notification drafts, the compliance record — is deterministic
  templating over structured data the Matching Agent already produced. This is a security
  decision, not a shortcut: a compliance document has nowhere for prompt injection to
  land if there's no prompt. The one LLM call in the whole pipeline stays isolated to the
  Matching Agent, where reasoning is actually needed.
- **Structural refusal, not just caller discipline.** `run_action_agent` re-checks
  `match["status"] == "auto_actioned"` itself and raises `ValueError` on anything else —
  so a bug upstream that calls this on a `pending_review` match fails loudly here instead
  of silently drafting on an unconfirmed match.
- **No send capability exists in the code, verifiably.** Wrote a test that parses the
  module's actual AST and asserts none of its imports are network/send-capable
  (`smtplib`, `requests`, `socket`, etc.) — not just a comment promising this, a test that
  would fail if someone added one later. Every notification is a draft file labeled
  `DRAFT — NOT SENT`.
- **Filenames sanitized, external text escaped.** `_safe_filename` strips everything but
  alphanumerics/dash/underscore before it ever touches a file path (tested against a
  path-traversal string). All recall/invoice/reasoning text is escaped via
  `xml.sax.saxutils.escape` before reaching reportlab's `Paragraph`, which otherwise
  interprets a subset of markup tags in its input.
- **PDF chosen deliberately: `reportlab`** — pure Python, no external system binary
  dependency (ruled out `weasyprint`, which needs Pango/cairo installed separately) —
  fewer moving parts to break under time pressure, smaller supply-chain surface.
- **9 tests, all passing** — the refusal behavior, checklist/draft content, the AST
  import check, filename sanitization, and a full end-to-end run asserting a real PDF
  gets written and the compliance log is correct.
- **Ran the whole pipeline live** (extended `run_matching_demo.py`): both real
  true-positive matches (chips, cottage cheese) flowed all the way through to actual
  compliance PDFs. **Read one of the generated PDFs back and visually verified it** —
  clean, plain, tabular, zero Scout branding, exactly matching the brand guide's rule
  that this is the one artifact a health inspector reads and needs to look serious.
- **Found and fixed a real bug:** `matching/agent.py` and the new `action/agent.py` had
  the same filename. The flat sibling-import pattern used throughout this codebase (each
  subpackage assumes it's the only thing on `sys.path`) silently breaks the moment two
  same-named files are both importable at once — `import agent` the second time just
  returns the first module from `sys.modules`, not an error, so it fails silently rather
  than loudly. Renamed both to `matching_agent.py`/`action_agent.py` and updated every
  reference (including in the git-tracked matching files, via `git mv` to preserve
  history). Worth remembering if more subpackages get added later.
- Also fixed two cosmetic em-dash/Windows-console-encoding mojibake issues in print
  statements — harmless but would look unpolished in a demo recording.

## 2026-08-23 — Multimodal invoice path built (Phase 4 fully done, local)

User's instruction: keep building the rest. Picked the multimodal image path next since
it's fully local (same Gemini key, no GCP) and it's the required-scope Best Multimodal UX
target, not just a nice-to-have.

- **`agents/invoices/image_parser.py`** — sends a photographed/scanned invoice image
  straight to Gemini's multimodal input, using the same structured-output pattern as the
  Matching Agent (Pydantic `response_schema`). Returns the identical rawLineItems shape
  `csv_parser.py` does, so nothing downstream needs to know or care which path an invoice
  came from. Same security posture as the Matching Agent too: the system instruction
  treats image content strictly as data to transcribe, never as instructions — an image
  containing adversarial embedded text shouldn't change extraction behavior, only get
  transcribed verbatim as ordinary (clearly attributed) line-item text.
- **No real photographed invoice on hand**, so built `generate_test_invoice_image.py` — a
  one-off Pillow script that renders a plausible printed receipt and applies rotation +
  blur + noise to simulate an actual phone photo, rather than testing against a
  suspiciously clean render. Explicitly NOT a substitute for a real photo before the
  actual demo recording — noted as a new blocker in `docs/PHASES.md`.
- **Tested live against the synthetic image — worked well on the first try.** Gemini
  correctly extracted all 5 line items AND pulled the supplier name ("GARCIA WHOLESALE
  FOODS") and the date straight out of the image text, neither of which were in a
  structured field — genuine multimodal reading, not just OCR-then-template. 3 tests
  passing (`test_image_parser.py`).
- **Wired into the full pipeline** (`run_matching_demo.py` now loads the photo alongside
  the 5 CSVs) and ran it end to end: the photographed invoice's recalled-product line
  matched at 95% and flowed through the Action Agent to a real compliance PDF, exactly
  like the CSV cases — proving the Matching/Action Agents genuinely don't care which
  ingestion path a line item came from.
- **Root-caused the mojibake issue properly this time** instead of patching individual
  characters: Windows' console defaults to cp1252, which mangles any non-ASCII character
  an LLM response contains. Added `sys.stdout.reconfigure(encoding="utf-8")` once at the
  top of `run_matching_demo.py` — confirmed it fixed a real instance (Gemini had added an
  accent to "Latínos" that was displaying as `Lat�nos` before the fix).
- Added `Pillow` to `agents/requirements.txt` (test-image generation only, not part of
  the runtime pipeline).

## 2026-08-23 — Hit the Gemini free-tier daily quota mid-session

Running the full pipeline again (to seed real dashboard data) failed with
`RESOURCE_EXHAUSTED` — the AI Studio free tier caps at **20 requests/day per model**,
and today's cumulative testing across every phase used it up. Logged in
`docs/RISK_REGISTER.md` — this threatens Phase 8's N=30 experiment specifically, which
needs far more than 20 calls in one run; will need to either spread it across days on
free tier or move to Vertex AI (paid) once GCP billing clears. Decided not to keep
retrying — paced remaining work around it instead of burning more quota chasing a fresh
run today.

## 2026-08-23 — Dashboard built: real backend, real frontend, visually verified (Phase 7 core done)

User's instruction: keep building the rest. Built the "Scout" corkboard dashboard —
`agents/dashboard/`, FastAPI backend + vanilla JS frontend adapted from the actual
brand-guide mockup CSS (not a generic template), reading live from `agents/storage.py`.

- **Found and fixed a real design gap first**: `storage.list_collection()` returned
  parsed JSON with no way to know which document a record came from — the dashboard
  needs this to correlate review-queue items with their matches and to call the
  confirm/reject endpoints. Fixed by having `list_collection` inject an `_id` field
  (the document's filename stem) into every returned record.
- **`agents/orchestrator.py`** — new, ties ingestion → matching → persistence → action
  into one reusable pipeline call (`process_recall`), used by both
  `run_matching_demo.py` (refactored to use it instead of duplicating logic) and the
  dashboard's confirm/reject actions (`resolve_review_item` — confirming a review-queue
  item promotes it to `auto_actioned` and genuinely runs the Action Agent, since a human
  just did the confidence check the model couldn't).
- **Found and fixed a real correctness bug via this refactor**: when the same recall
  matched two different invoice lines for one business (which happened for real — the
  CSV and photo invoices both had a Selectos Latinos line), the Action Agent derived its
  PDF filename/compliance-log key from recall+business only, so the second match's PDF
  silently overwrote the first's. Fixed by having callers pass their own unique
  `match_id` through to `run_action_agent`; added a regression test
  (`test_two_matches_same_recall_dont_collide_when_match_id_given`).
- **`agents/dashboard/server.py`** — `/api/state` (business + cases + review queue +
  metrics, joined from storage), `/api/review/{id}/confirm|reject`. 4 tests passing via
  FastAPI's `TestClient` (no live server needed): empty state, matches+queue joins, the
  full confirm→Action-Agent→compliance-log path, 404 on an unknown match.
- **`agents/dashboard/static/index.html`** — adapted directly from the real
  `01_dashboard.html`/`02_case_file_review.html` mockups' actual CSS tokens/fonts, not
  reinvented: the case board, the "Needs Your Nose" review queue, and the case-file
  modal with the confidence dial and Scout's stored reasoning. Confirm/reject wired to
  the real API, 5s polling for near-real-time refresh per `docs/ARCHITECTURE.md`.
- **Seeded real data without new Gemini calls** (`seed_dashboard_data.py`) — recalls
  fetched live from openFDA (no quota limit there), match/reasoning content reused
  verbatim from real Gemini outputs already captured earlier this session (not
  fabricated — explicitly documented as a stopgap in the script's own docstring).
- **Visually verified with an actual headless browser**, not just by reading the code.
  Neither `chromium-cli` nor Node.js/npx were available in this environment, so installed
  Python's `playwright` + Chromium as a fallback. Screenshotted the case board (4 cases,
  correct stamps/tags), opened the review modal via a real click (confidence dial,
  Scout's actual stored reasoning), and — the real test — clicked **Confirm Match** and
  verified the review count went 1→0, a new compliance PDF and log entry appeared on
  disk, and the browser console had zero JS errors.
- **Found and fixed a real CSS bug from the screenshot**: a redundant "CAUGHT" text label
  next to the confidence percentage visually overlapped the paw-stamp graphic on
  auto-actioned cards. Removed it — the stamp alone already says that.
- **Deliberately not built**: Recall Radar map, streak counter, and the animated
  pin-and-string connector between a specific recall and its matching evidence card (the
  original mockup hand-positions that for exactly 2 cards; doing it generically for a
  variable-length list needs real layout logic). All three are explicitly named as the
  first things to cut under time pressure in `docs/PLAN.md`'s own priority list — correct
  to defer them ahead of harder remaining work, not an oversight.
