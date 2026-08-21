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
