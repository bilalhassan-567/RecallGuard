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
