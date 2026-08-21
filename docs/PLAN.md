# RecallGuard — Build Plan

Track: **The Taskmaster** (All Things Agentic Hackathon, Devpost) — also eligible for Best
Architectural Design, Best Multimodal UX, and Individual/Hobbyist (cross-track bonus
prizes, stated explicitly in the submission text).

Stack: **Gemini (Vertex AI) + Google ADK + Cloud Run + Firestore + Pub/Sub + Cloud
Scheduler.**

For the full reasoning behind every decision below — including the prize-targeting
strategy and API research that shaped it — see the internal build plan (not tracked in
this repo). This file is the living, public version: what we're building and why, kept in
sync as the project moves. Status/checkboxes for day-to-day execution live in
`docs/PHASES.md`; this file is the "what and why," not the tracker.

---

## One-paragraph spec

RecallGuard ingests FDA (openFDA) and USDA FSIS food recall data, fuzzy-matches each recall
against a business's own uploaded invoices/POS records using Gemini, and autonomously
produces a pull-checklist, a draft notification, and a timestamped compliance record —
flagging anything ambiguous for human review instead of guessing.

## Two API realities that shape the build

1. **openFDA is not a live-status feed.** FDA's own docs say the enforcement API
   shouldn't be used to track a recall's lifecycle, and `status` (Ongoing/Terminated) isn't
   reliably updated. **We treat `report_date` as the trigger signal** ("newly published as
   of X"), never claim "live recall status."
2. **openFDA updates weekly; FSIS's Recall API is near-real-time.** FSIS is the primary
   "fast" trigger source; openFDA is the broader historical/matching corpus.
3. **openFDA query gotchas:** always quote exact-match values
   (`classification:"Class+I"`), append `.exact` when aggregating a text field, and don't
   request `report_date` ranges before 2012-06-20 (404s on all three enforcement endpoints).

Base endpoints:
- `https://api.fda.gov/food/enforcement.json`
- FSIS Recall API — see `https://www.fsis.usda.gov/science-data/developer-resources` for
  current base URL/key requirements; confirm auth requirements on Day 1.

## Locked MVP scope

**Building:**
- Recall ingestion (openFDA + FSIS) → normalized event
- Invoice/POS upload — CSV required; photographed/scanned invoice via Gemini multimodal is
  **required scope**, not a stretch goal (it's the Best Multimodal UX proof)
- Fuzzy matching agent (Gemini reasoning with stated confidence + rationale, not
  embeddings-only)
- Confidence-based routing: high confidence → auto-draft action; low confidence → human
  review queue
- Action agent: pull-checklist, notification draft, compliance record (structured doc/PDF)
- Firestore dashboard: recalls checked, matches found, time-to-detection, accuracy history
- Deployed on Cloud Run, wired through Pub/Sub, Vertex AI call logs visible in console

**Explicitly NOT building** (deliberate scope cut, stated in the README so it reads as a
decision, not an oversight):
- Auto-sending real emails/notifications to real third parties (draft-only)
- Full legal compliance certification across all 50 states / all regulatory bodies
- Mobile app
- General chat interface over the data (scope creep back to chatbot)
- A live-at-judging-time requirement — the hackathon rules don't require this, just
  provably built and deployed

## Architecture

See `docs/ARCHITECTURE.md` for the diagram. Three agents, mapped 1:1 to three real jobs —
**sense → decide → act**:

| Agent | Job |
|---|---|
| Recall Monitor | Polls FSIS + openFDA, normalizes into `recalls/{recallId}`, publishes to Pub/Sub |
| Matching Agent | Gemini fuzzy-matches recall vs. invoice line items, returns confidence + reasoning |
| Action Agent | Drafts checklist, notification, and compliance record for high-confidence matches |

**Google Cloud service justification** (also goes in the submission's "technologies used"
field):
- **Cloud Run** — hosts monitor, matching, action, and dashboard services; scales to zero
  between polls
- **Pub/Sub** — decouples detection from matching (async, retryable, fan-out per business)
- **Firestore** — persistent per-business state across sessions; NoSQL fits variable
  invoice schemas
- **Vertex AI (Gemini)** — the reasoning engine for fuzzy matching + drafting
- **Cloud Scheduler** — triggers the monitor poll (the one deterministic piece; agentic
  value is downstream, in matching/decision/action)

Full Firestore schema: `docs/DATA_MODEL.md`. Full agent pseudocode: `docs/AGENTS.md`.

## The "Scout" layer

Product name stays **RecallGuard** — that's what appears on the compliance record (serious,
credible). The agent's voice and UI carry a persona: **Scout**, a food-safety detective.
This is copy + a UI skin over the same backend, not new architecture.

- **Design direction:** a detective corkboard case-file, not a generic SaaS dashboard.
- **Signature element:** a recall = a pinned "wanted poster"; a matching invoice line = a
  pinned "evidence" card; a red string connects them; a confirmed match gets a paw-stamp
  reading "CAUGHT IT."
- **Voice rule that matters for credibility:** Scout is confident, never smug, never
  overclaims — a low-confidence match says "Scout's unsure — take a look." The compliance
  record artifact itself stays plain, serious, and paw-print-free.

Full color/type/component tokens and reference mockups are internal design assets; the
summary of the design system will be published here once the UI is built.

## What "excellent" looks like (the two prizes idea alone can't win)

### Best Architectural Design
Must be visible in the demo or repo, not just true in the code:
- Pub/Sub decoupling shown on camera, explained
- Firestore state persisting across a session boundary shown, not claimed
- A real failure triggered on camera (kill the recall API, or feed a malformed invoice),
  showing graceful degradation
- Credentials shown to be non-hardcoded (Secret Manager / env config glance)
- Architecture diagram shows data direction AND failure paths
- README spin-up instructions actually verified by someone who didn't build the project

### Best Multimodal UX
- At least one photographed/scanned invoice demoed, not only a clean CSV
- The case-file review UI shown in motion (confidence dial, live reasoning render,
  string-and-pin animation)
- Compliance record kept visually distinct from the fun UI (design intentionality, not one
  skin over everything)
- No generic component-library look — the corkboard/case-file treatment is the point

If time runs short near the end, cut in this order (last cut first): (1) badges/streak
cosmetics, (2) Recall Radar polish, (3) recall-source coverage beyond the two APIs — never
cut the live failure-demo moment or the photographed-invoice path.

## Quantitative experiment

Full design in `docs/EXPERIMENT.md`. Summary: 30 real historical recalls, a curated invoice
set (true positives / near-miss true negatives / easy true negatives), a timed human
baseline vs. the agent, reporting precision/recall/false-positive/false-negative/mean
time-to-detection exactly as measured. Success bar: agent accuracy ≥ human baseline, ≥10×
reduction in mean time-to-detection, zero high-confidence false positives.

## Failure modes to demonstrate

| Failure | Handling |
|---|---|
| Recall API unreachable | Retry with backoff; log gap in Firestore; never silently skip |
| Invoice missing key fields (no lot code) | Flag "insufficient data," route to review, don't guess |
| Gemini low-confidence output | Routed to human review queue, never auto-actioned |
| Partial workflow completion (match found, PDF fails) | Per-step state in Firestore — resumes from the failed step |
| Prompt injection via recall notice text | Recall content treated as untrusted data, never as instructions |

## Security notes

- Firestore security rules scoped per `businessId`; no cross-business reads
- No credentials committed — Secret Manager / environment injection
- Action Agent's "send" capability disabled in the MVP (draft-only)
- All fetched recall content treated as data, not instructions

## Demo script (4 minutes)

Full timestamped script: `docs/submission/demo-video-script.md`.

## Submission checklist

Full checklist: `docs/submission/submission-checklist.md`.

---

## Revisions

*(Log scope or approach changes here with a dated entry, rather than silently rewriting
sections above.)*

- **2026-08-22** — Initial public plan written, derived from the locked internal build
  plan. No revisions yet — this is the starting spec.
