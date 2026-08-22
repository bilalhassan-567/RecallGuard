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
| 2 — Recall ingestion (FSIS + openFDA) | Not started |
| 3 — Event backbone (Pub/Sub + Scheduler) | Not started |
| 4 — Invoice ingestion (CSV + multimodal image) | Not started |
| 5 — Matching Agent (Gemini reasoning + confidence routing) | Not started |
| 6 — Action Agent + artifacts (checklist/notification/compliance PDF) | Not started |
| 7 — Dashboard / UI (Scout corkboard) | Not started |
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

- [ ] FSIS API client + confirmed auth/key requirements
- [ ] openFDA client — quoting (`classification:"Class+I"`), `.exact` aggregation, date-window pagination (avoid pre-2012-06-20 404 trap)
- [ ] Both sources normalized into `recalls/{recallId}` schema
- [ ] Unit tests against a handful of known historical recalls

## Phase 3 — Event backbone

- [ ] Pub/Sub topic `recall.detected` + subscription wiring
- [ ] Cloud Scheduler → Recall Monitor agent → publish, working end-to-end on seeded data

## Phase 4 — Invoice ingestion

- [ ] CSV upload → parsed `rawLineItems`
- [ ] 5–10 realistic sample invoice sets built (different suppliers/formats/abbreviations)
- [ ] **Photographed/scanned invoice via Gemini multimodal — required scope, not stretch** (Best Multimodal UX target)

## Phase 5 — Matching Agent

- [ ] Gemini prompt: confidence (0–100) + one-sentence reasoning, structured JSON output
- [ ] Confidence-threshold routing (≥80 auto-actioned, 40–79 pending review, <40 discarded+logged)
- [ ] N=30 ground-truth labeled set built early (feeds Phase 8)

## Phase 6 — Action Agent + artifacts

- [ ] Pull-checklist generation
- [ ] Notification draft (supplier + health dept template — draft only, never sent)
- [ ] Compliance record (serious, plain, paw-print-free) + PDF export
- [ ] `compliance_log` written

## Phase 7 — Dashboard / UI ("Scout" corkboard)

- [ ] Corkboard case board reading `recalls/{}` + `matches/{}`
- [ ] Case-file review screen (confidence dial + Scout's reasoning + confirm/reject)
- [ ] Recall-Free Streak counter (reads `metrics/{businessId}_daily`)
- [ ] Recall Radar map (approximate state centroids)
- [ ] Paw-stamp "CAUGHT IT" on confirmed matches
- [ ] Compliance record kept visually distinct from the fun UI (judge-facing intentionality)

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
- [ ] **Timeline strategy** — see the calendar reality check above; needs an answer before
      Day 1 starts, since it changes how aggressively to cut scope. Starting from a
      zero GCP setup (just confirmed above) makes this more pressing, not less.
- [ ] **FSIS API key/auth** — not yet confirmed (flagged as a Day-1 risk in the plan
      itself: "confirm key requirements on Day 1, not Day 8"). Needs checking against
      `https://www.fsis.usda.gov/science-data/developer-resources` before Phase 2 can start
      for real; openFDA-only is the fallback if this drags.
- [ ] **Sample invoice sets (5–10, varied suppliers/formats) + one real photographed
      invoice** — not yet collected. Explicitly flagged in the plan as "takes longer to
      assemble well than people expect and gates Days 4–6" — worth starting in parallel
      with Phase 1, not waiting for Phase 4.
- [ ] **Frontend framework for the dashboard** — not locked. Plan says "keep it simple," but
      no concrete choice yet (plain HTML/JS on Cloud Run vs. a framework).
- [ ] **PDF/doc generation library** for the compliance record — not chosen yet.
- [ ] **Team size** — building solo? (Individual/Hobbyist prize targeting assumes so; the
      live rules allow teams of any size with no cap, so worth confirming explicitly.)
