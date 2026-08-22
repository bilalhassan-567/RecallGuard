# RecallGuard — Phase Board

The one file to check for "where are we." Flip statuses here as work lands — don't let it
drift from `docs/PROGRESS.md` (the detailed log) or from reality. Status values: **Not
started** · **In progress** · **Blocked** · **Done**.

**Last updated:** 2026-08-22 — project scaffolding + documentation phase.

---

## Timeline reality check (verified 2026-08-22 against live Devpost rules)

**Deadline: August 31, 2026, 5:00 PM PT — hard cutoff.** Today is August 22. That leaves
**9 full calendar days** (Aug 23–31), and part of Aug 31 itself needs to be reserved for
actually clicking submit, not building — "submit early" per the plan, not at 4:55pm.

The internal build plan's day-by-day schedule (`docs/PLAN.md`) is written as **10 working
days**. Mapped onto the real calendar:

| Plan day | Calendar date | Content |
|---|---|---|
| Day 1 | Aug 23 | Foundations |
| Day 2 | Aug 24 | Recall ingestion |
| Day 3 | Aug 25 | Event backbone |
| Day 4 | Aug 26 | Invoice ingestion (incl. required multimodal image path) |
| Day 5–6 | Aug 27–28 | Matching Agent (highest-uncertainty component — the plan's own buffer day lives here) |
| Day 7 | Aug 29 | Action Agent + artifacts |
| Day 8 | Aug 30 | Dashboard / UI |
| Day 9 | Aug 31 (AM) | Run the real N=30 experiment + rehearse the failure-demo beat |
| Day 10 | Aug 31 (PM) | Demo video, docs polish, submission |

**This does not fit with any slack.** Days 9 and 10 — running a real experiment,
recording/editing a 4-minute video, and submitting — landing on the same calendar day as a
5pm hard deadline is a real risk, not a formality. Before Phase 1 starts, this needs one of:

1. More than one plan-day of work per calendar day on at least a few days (i.e. this isn't
   a "one sitting per day" build), or
2. The experiment (Day 9) pulled earlier — e.g. run a smaller/partial version once the
   Matching Agent works (~Aug 28), full N=30 once the pipeline is stable, rather than
   waiting until the last morning, or
3. An explicit internal deadline earlier than Aug 31 (e.g. "submit by Aug 30 evening,
   Aug 31 is buffer only") — the safer pattern, and what the reference build in
   `docs/master-workout/` (an earlier hackathon) actually did.

**Not yet answered — needed before committing to a day-by-day schedule:** how many hours/
day are realistically available, and starting when (today, or after Aug 22 documentation
work wraps)?

---

## At a glance

| Phase | Status |
|---|---|
| 0 — Documentation & repo scaffolding | In progress |
| 1 — Foundations (GCP, ADK hello-world, Firestore schema) | Not started |
| 2 — Recall ingestion (FSIS + openFDA) | Done (openFDA-only; FSIS deferred, see notes) |
| 3 — Event backbone (Pub/Sub + Scheduler) | Not started |
| 4 — Invoice ingestion (CSV + multimodal image) | Done (local) |
| 5 — Matching Agent (Gemini reasoning + confidence routing) | Core logic done, validated |
| 6 — Action Agent + artifacts (checklist/notification/compliance PDF) | Done (local) |
| 7 — Dashboard / UI (Scout corkboard) | Core done (local), polish items remain |
| 8 — Quantitative experiment (N=30 baseline vs agent) | Not started |
| 9 — Failure-injection rehearsal + Architectural Design checklist | Not started |
| 10 — Demo video, docs polish, submission | Not started |

---

## Phase 0 — Documentation & repo scaffolding

- [x] Read and internalized the master build plan + brand/UI mockups (`docs/master-workout/`)
- [x] Git repo initialized
- [x] `.gitignore` — excludes `docs/master-workout/`, `CLAUDE.md`, secrets, venv, IDE files
- [x] `CLAUDE.md` — internal rules file (gitignored): no-AI-co-author rule, docs split rule, working rhythm
- [x] `docs/` public structure created (this board, plan, architecture, data model, agent
      logic, experiment design, risk register, submission drafts)
- [ ] Root `README.md` — problem statement + status (spin-up steps land once there's something to spin up)
- [ ] First commit

## Phase 1 — Foundations

- [ ] GCP project created, billing linked
- [ ] APIs enabled: Vertex AI, Firestore, Pub/Sub, Cloud Run, Cloud Scheduler
- [ ] ADK scaffolding + hello-world agent deployed to Cloud Run
- [ ] Firestore schema created (see `docs/DATA_MODEL.md`)
- [ ] Firestore security rules drafted (scoped per `businessId`)
- [ ] Secrets handled via Secret Manager / env injection (no hardcoded credentials — verify this on camera later, section 5c)

## Phase 2 — Recall ingestion

- [x] **FSIS auth confirmed: no API key needed** (2026-08-22) — verified against real
      working reference implementations on GitHub, not just docs. Client built
      (`agents/ingestion/fsis_client.py`) but **untested from a real network** — the dev
      sandbox is blocked by Akamai bot-management (403, same for browser and `curl` UAs),
      while openFDA hit the same way works fine. Needs a run from a normal machine to
      confirm this is sandbox-specific, not a broader block. **See the 🔴 item in
      Blockers below — this could matter again once we're on Cloud Run.**
- [x] **openFDA client built and verified end-to-end** (`agents/ingestion/
      openfda_client.py`) — real request against live data, 36 records fetched and
      normalized correctly. Found and fixed a real bug along the way: `requests`'
      automatic URL-encoding turned openFDA's literal `+` (in `report_date:[X+TO+Y]`)
      into `%2B`, breaking the query (500 from the API) — fixed by building the query
      string manually instead of passing it through `params=`.
- [x] Both sources normalized into the `recalls/{recallId}` shape from `docs/DATA_MODEL.md`
      (`agents/ingestion/normalize.py`) — real field names pulled from an actual FSIS
      sample record and a live openFDA response, not guessed. Fixed a messiness bug in
      `distributionStates` parsing along the way (openFDA prefixes it with a boilerplate
      sentence; now stripped before splitting).
- [x] **Unit tests against known historical recalls** (2026-08-23) — 11 tests, all
      passing. `test_normalize.py`: 8 offline/fixture tests (a real captured FSIS record
      used as ground truth, plus full coverage of the `_split_states` edge cases —
      empty, "Nationwide", plain CSV, the boilerplate-prefix bug, single state). `test_
      openfda_live.py`: 3 live tests pinned against two specific real recalls by exact
      `recall_number` (not a date window, so they're stable over time) — verified against
      values manually confirmed earlier in the session, plus a not-found case. Added
      `openfda_client.fetch_by_recall_number()` to support pinned lookups.

## Phase 3 — Event backbone

- [ ] Pub/Sub topic `recall.detected` + subscription wiring
- [ ] Cloud Scheduler → Recall Monitor agent → publish, working end-to-end on seeded data

## Phase 4 — Invoice ingestion

- [x] **CSV upload → parsed `rawLineItems`** (2026-08-23) — `agents/invoices/csv_parser.py`,
      handles 5 genuinely different column layouts via a known-alias lookup rather than
      assuming one schema (real invoices don't share a format). 7 tests passing.
- [x] **5 realistic sample invoice sets built** (`agents/sample_data/invoices/`) — Sysco,
      US Foods, a local distributor, a wholesale club, and Restaurant Depot styles.
      Deliberately covers all four evaluation categories up front: 2 true positives
      (anchored on real recalls), 1 near-miss true negative (same brand, wrong flavor —
      tests false-positive avoidance), 1 easy true negative, 1 genuinely ambiguous case
      (no lot code — tests the "don't guess" behavior). Ground truth documented in
      `ground_truth.json`. Room to grow toward 10 later; this set already exercises every
      behavior the plan calls out.
- [x] **Photographed/scanned invoice via Gemini multimodal** (2026-08-23) — required
      scope, not stretch (Best Multimodal UX target). `agents/invoices/image_parser.py`,
      same output shape as `csv_parser.py` so the Matching Agent doesn't care which path
      an invoice came from. Same prompt-injection guard pattern as the Matching Agent
      (image content treated as data to transcribe, not instructions). Tested against a
      synthetic photographed-invoice image (`generate_test_invoice_image.py` — printed
      text, rotation, noise/blur, not a clean render) — extraction correctly pulled all 5
      line items, the supplier name, AND the date straight out of the image, and the
      recalled product line matched at 95% through the full pipeline (matching + action)
      exactly like the CSV cases. **3 tests passing.** Before the actual demo recording,
      swap the synthetic image for one genuine photographed invoice (see Blockers).

## Phase 5 — Matching Agent

- [x] **Gemini prompt + structured JSON output — built and validated live (2026-08-23).**
      `agents/matching/agent.py`. Uses `google-genai`'s Pydantic-based `response_schema`
      for reliable structured output (confidence 0-100 + reasoning per line), not
      hand-parsed text. Reasoning is written in Scout's first-person voice per the brand
      guide (matches the `02_case_file_review.html` mockup's actual copy style), since
      it's shown directly in the review UI, not post-processed. Recall/invoice text
      passed as data, never instructions (prompt-injection guard).
- [x] **Confidence-threshold routing** (≥80 auto_actioned, 40-79 pending_review, <40
      rejected-but-logged) — implemented and live-tested against real recalls + the
      sample invoice set. **All 3 automated tests pass** (`agents/matching/test_agent.py`,
      live Gemini calls): the true positive (heavily abbreviated) correctly
      auto-actioned at 95%; the near-miss (same brand, wrong flavor) correctly did NOT
      auto-action despite brand-name similarity — the exact false-positive trap this
      needed to avoid; unrelated products correctly rejected. The ambiguous no-lot-code
      case correctly routed to `pending_review` at 55%, with Scout's stated reasoning
      explicitly naming the missing brand/lot info as the reason — exactly the "don't
      guess" behavior the plan designs for.
- [ ] N=30 ground-truth labeled set built early (feeds Phase 8) — the 5-invoice set above
      is a real start but not yet at N=30 scale.

## Phase 6 — Action Agent + artifacts

- [x] **Pull-checklist generation** (2026-08-23) — `agents/action/action_agent.py`.
      Includes a keyword-based storage-location hint (dairy/meat/produce/dry storage)
      as a small deterministic convenience, not another LLM call.
- [x] **Notification drafts** (supplier + health dept) — every draft is explicitly
      labeled `DRAFT — NOT SENT`, and there is no send-capable code in the module at all
      (no smtplib/requests/socket — verified by an AST-parsing test, not just a promise).
      Matches the plan's deliberate MVP scope cut: draft-only, on purpose.
- [x] **Compliance record + PDF export** — `agents/action/pdf_export.py` (reportlab).
      Visually verified: plain, serious, tabular — no Scout branding, matching the brand
      guide's explicit rule that this is the one document a health inspector reads.
- [x] `compliance_log` written to the local Firestore stand-in
      (`businesses/{id}/compliance_log/{matchId}`).
- **Security design (see the docstring at the top of `action_agent.py`):** no LLM call
  happens anywhere in this module — everything is deterministic templating over data the
  Matching Agent already produced, which removes prompt-injection as a concern for this
  stage entirely (there's no prompt to inject into). `run_action_agent` structurally
  refuses to run on anything but a confirmed `auto_actioned` match — enforced in code, not
  just caller discipline — and all external text is escaped before reaching the PDF
  renderer. 9 tests passing, including a real path-traversal filename test and the AST
  import check.
- **Ran the full pipeline live** (`agents/run_matching_demo.py`, extended this session):
  ingestion → matching → action, end to end, on real recall data. Both true-positive
  matches produced real compliance PDFs, checklists, and drafts.
- **Found and fixed a real bug along the way:** `agents/matching/agent.py` and
  `agents/action/agent.py` shared the same filename, which silently broke the flat
  sibling-import pattern used everywhere else (`import agent` returned whichever module
  got imported first, not the intended one) the moment both subpackages were on
  `sys.path` at once. Renamed both to `matching_agent.py` / `action_agent.py`.

## Phase 7 — Dashboard / UI ("Scout" corkboard)

- [x] **Corkboard case board reading real data** (2026-08-23) — `agents/dashboard/`,
      FastAPI backend + vanilla JS frontend, adapted from the actual brand-guide mockup
      CSS/tokens (not a generic template). Reads live from `agents/storage.py`'s
      `matches`/`recalls`/`review_queue`/`metrics` — same Firestore-shaped addressing, so
      swapping to real Firestore later is a backend change, not a UI rewrite.
- [x] **Case-file review screen (confidence dial + Scout's reasoning + confirm/reject)**
      — a modal, not a separate page, matching `02_case_file_review.html`'s visual style.
      **Confirm/reject are real, not decorative**: confirming a pending-review match
      calls `orchestrator.resolve_review_item`, which genuinely runs the Action Agent and
      produces a real compliance PDF — verified end-to-end with a headless-browser test
      (screenshot before/after, review queue count 1→0, PDF + compliance_log entry
      confirmed on disk).
- [x] **Paw-stamp "CAUGHT IT" on confirmed matches** — implemented, visually verified.
- [ ] Recall-Free Streak counter — not built yet (metrics rollup exists, just not
      surfaced as a streak specifically).
- [ ] Recall Radar map (approximate state centroids) — not built.
- [x] Compliance record kept visually distinct from the fun UI — already true by
      construction (Phase 6's PDF has zero Scout branding, verified visually).
- **4 API tests passing** (`agents/dashboard/test_server.py`, FastAPI `TestClient`, no
  live server/network needed) — empty state, matches+review-queue joins, the full
  confirm→Action-Agent→compliance-log path, and a 404 on an unknown match.
- **Visually verified with a real headless browser** (Playwright, installed this session
  since neither `chromium-cli` nor Node.js were available here) — not just "the code
  looks right." Screenshotted the case board, the review modal, and the state after a
  real confirm click; checked the browser console for JS errors (none). See
  `docs/PROGRESS.md` for what the screenshots showed, including one real CSS bug found
  and fixed (a "CAUGHT" label overlapping the paw stamp).
- Deliberately deferred: Recall Radar and streak counter are cosmetic (explicitly named
  as the *first* things to cut under time pressure in `docs/PLAN.md`'s priority list) —
  correctly not spending time on them before the harder remaining phases.

## Phase 8 — Quantitative experiment

- [ ] 30 real historical recalls pulled (mixed Class I/II/III, mixed hazard types)
- [ ] Invoice sample set with true positives, near-miss true negatives, easy true negatives
- [ ] Baseline: manual human check timed + scored
- [ ] Agent condition run, same 30 cases, metrics recorded
- [ ] Precision / recall / false-positive rate / false-negative rate / mean time-to-detection reported as measured (no rounding up)

## Phase 9 — Failure handling + Architectural Design checklist

- [ ] Recall API unreachable → retry/backoff, logged gap, no silent skip
- [ ] Invoice missing key fields → routed to review, not guessed
- [ ] Low-confidence Gemini output → never auto-actioned
- [ ] Partial workflow failure (match found, PDF fails) → resumes from failed step, not from scratch
- [ ] Prompt-injection guard on recall text (treated as data, never instructions)
- [ ] Live failure-injection demo beat rehearsed until it's a clean ~15s repeatable moment
- [ ] Pub/Sub decoupling moment identified for the demo
- [ ] Firestore cross-session persistence moment identified for the demo

## Phase 10 — Demo, docs, submission

- [ ] 4-minute demo recorded (see `docs/submission/demo-video-script.md`)
- [ ] Architecture diagram finalized as a clean visual (`docs/ARCHITECTURE.md`)
- [ ] README spin-up instructions written AND tested by someone who didn't build it
- [ ] `docs/submission/devpost-description.md` filled in with real results
- [ ] `docs/submission/submission-checklist.md` fully checked
- [ ] Submitted (early, not at the deadline hour)

---

## Blockers / open questions

Logged 2026-08-22 during the full plan re-check, before Phase 1 starts:

- [x] **$150 Google Cloud credit form submitted** (2026-08-22). Processing takes up to
      72 business hours — don't block Phase 1 waiting on it; the standard Cloud free
      trial (separate from this hackathon credit) is enough to start a project today.
- [x] **BYOF framing** — decided 2026-08-22: no fabricated personal backstory (risks the
      false-information disqualification clause and doesn't hold up under scrutiny
      anyway). Frame honestly around the real operational gap instead, and let the
      autonomous-workflow half of the Innovation criterion carry the score. See
      `docs/PLAN.md` and `docs/submission/devpost-description.md` → Inspiration.
- [x] **Hosting decision** — decided 2026-08-22: host it, and host the dashboard frontend
      on **Cloud Run**, not Vercel — keeps one platform, one story for the "visible Google
      Cloud deployment" judging criterion, and avoids a second integration surface under
      a 9-day clock. Full reasoning in `docs/PLAN.md`.
- [ ] **🔴 GCP billing verification blocked (in progress, 2026-08-22).** Free-trial
      billing setup fails with `OR_BACR2_31` — both a SadaPay virtual and physical
      Mastercard declined with the identical error. Root cause: fintech/prepaid card
      BINs (SadaPay, NayaPay) are broadly blocked by Google's cloud-billing fraud checks,
      independent of which specific card. A Google Cloud Support ticket has been filed
      asking for manual identity verification instead of card verification; first reply
      was a generic canned response, a follow-up was sent pushing back on it (see
      `docs/PROGRESS.md` for the full exchange). **This blocks Cloud Run / Firestore /
      Pub/Sub specifically — it does not block Gemini API work (see below).**
- [x] **Gemini API access unblocked without waiting on GCP billing (2026-08-22).** Set up
      `agents/` locally: `google-adk` + `google-genai` installed and import-clean, a
      `test_gemini.py` smoke test, and an ADK hello-world agent (`agents/hello_agent/`).
      Uses a free Google AI Studio API key (`GOOGLE_API_KEY`, no billing account) instead
      of Vertex AI — same `google-genai` SDK either way, so switching to Vertex later is
      a one-line env change (`GOOGLE_GENAI_USE_VERTEXAI=TRUE`), not a rewrite.
      **Confirmed working live** — `python test_gemini.py` returned a clean response from
      `gemini-3.5-flash` with real token counts, and `adk run hello_agent` loaded and
      responded correctly through the actual ADK CLI. (The agent's own reply claimed
      "Gemini 2.5 Flash" — that's the model unreliably self-reporting in prose, not
      authoritative; the real config is confirmed by `test_gemini.py`'s printed model ID,
      which came from a successful API call using our own `gemini-3.5-flash` setting.)
      **Phase 1 local scaffolding is done.** Only "deployed to Cloud Run" remains, pending
      the GCP billing ticket.
- [ ] **A genuine photographed invoice, before the demo recording** — the multimodal path
      is code-complete and tested against a synthetic image, but the actual demo script
      (`docs/submission/demo-video-script.md`) needs a real phone photo of a real paper
      invoice, not a generated one, for the Best Multimodal UX moment to be honest. Low
      effort (photograph any invoice, even a made-up one printed on paper), just needs
      doing before Day 10.
- [ ] **Timeline strategy** — see the calendar reality check above; needs an answer before
      Day 1 starts, since it changes how aggressively to cut scope. Starting from a
      zero GCP setup (just confirmed above) makes this more pressing, not less.
- [x] **FSIS reachability — investigated, not fixable from dev (2026-08-22/23).** No API
      key needed (confirmed via real working reference code), but the endpoint 403'd from
      BOTH the dev sandbox AND the user's real Pakistani residential network — same
      error, same behavior, ruling out "sandbox-specific datacenter IP" as the cause.
      **Working theory: a geographic block on non-US traffic**, common for Akamai-fronted
      US federal (.gov) sites. **Decision: stop chasing this in dev.** Treat FSIS as
      unavailable for now; openFDA is the confirmed-working primary/sole trigger source.
      Re-test FSIS once Cloud Run is deployed **in a US region** — a US-based Google Cloud
      egress IP might not hit the same block, which residential/sandbox non-US IPs did.
      The plan's existing failure-handling design (retry/log/continue, never silently
      skip) already covers "a recall source is unreachable" without special-casing this —
      real-world validation of that design, not just a hypothetical for the demo.
- [ ] **Sample invoice sets (5–10, varied suppliers/formats) + one real photographed
      invoice** — not yet collected. Explicitly flagged in the plan as "takes longer to
      assemble well than people expect and gates Days 4–6" — worth starting in parallel
      with Phase 1, not waiting for Phase 4.
- [ ] **Frontend framework for the dashboard** — not locked. Plan says "keep it simple," but
      no concrete choice yet (plain HTML/JS on Cloud Run vs. a framework).
- [ ] **PDF/doc generation library** for the compliance record — not chosen yet.
- [ ] **Team size** — building solo? (Individual/Hobbyist prize targeting assumes so; the
      live rules allow teams of any size with no cap, so worth confirming explicitly.)
