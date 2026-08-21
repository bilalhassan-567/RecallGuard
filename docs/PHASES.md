# RecallGuard — Phase Board

The one file to check for "where are we." Flip statuses here as work lands — don't let it
drift from `docs/PROGRESS.md` (the detailed log) or from reality. Status values: **Not
started** · **In progress** · **Blocked** · **Done**.

**Last updated:** 2026-08-22 — project scaffolding + documentation phase.

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

*(none yet — log anything blocking progress here with a date, and clear it when resolved)*
