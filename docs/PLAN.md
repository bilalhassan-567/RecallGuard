# RecallGuard — Build Plan

Track: **The Taskmaster** (All Things Agentic Hackathon, Devpost) — also eligible for Best
Architectural Design, Best Multimodal UX, and Individual/Hobbyist (cross-track bonus
prizes, stated explicitly in the submission text).

Stack: **Gemini (Vertex AI) + Google ADK + Cloud Run + Firestore + Pub/Sub + Cloud
Scheduler.**

## Verified live rules (checked directly against the official Devpost page + Official
Rules, 2026-08-22 — re-confirmed against the full page text the same day)

The internal build plan this was derived from didn't carry exact dates or the full
per-track judging language. This section is authoritative; earlier estimates in this file
or elsewhere are superseded by it.

- **Contest Period:** Aug 3, 2026, 9:00 AM PT → Aug 31, 2026, 5:00 PM PT.
- **Submission deadline: August 31, 2026, 5:00 PM PT** = **September 1, 2026, 5:00 AM
  GMT+5 / PKT.** Strict cutoff, no edits to the submission after (draft edits to the
  Devpost *portfolio* page are fine post-deadline, the submission itself is frozen).
- **Judging Period: Sep 1, 2026 (9:00 AM PT) → Oct 1, 2026 (11:45 PM PT).** Winners
  announced on or around **Oct 8, 2026, 10:00 AM PT**.
- **Google Cloud credit ($150) request form has its own deadline:
  August 28, 2026, 12:00 PM PT — "or while supplies last."** This is a real near-term
  action item, separate from the build schedule — request it early, don't wait.
  (`https://forms.gle/riGhgDSHkHeMx8Ca6`, one code per entrant, ~72 business hours to
  process — so requesting even a day late risks not having it in hand until deep into
  the build window.)
- **Submission period: August 3–31, 2026.** The project must be newly created within this
  window (pre-existing code must be disclosed — not a concern, this repo started fresh).
- **Category (pick exactly one, mandatory field):** Taskmaster / Collaborative Partner /
  Fortified Enterprise Fleet. We're selecting **Taskmaster**. Best Architectural Design,
  Best Multimodal UX, and Individual/Hobbyist are cross-track bonus prizes judged
  separately, not alternate category picks — mention eligibility for them in the text
  description, don't try to "select" them.
- **Mandatory tech (all three required):** Gemini 3.5+ via Gemini API or Vertex AI ✅
  (official cost-saving tips explicitly recommend **Flash first, Pro only for complex
  final reasoning** — relevant to us since the Matching Agent calls Gemini once per
  invoice line, so Flash-by-default is the right cost posture, escalate to Pro only if
  match quality demands it) · one of Google ADK / GenAI SDK / Antigravity SDK / GenKit —
  we use **ADK** ✅ · one of Cloud Run / Cloud SQL / Firestore / GKE / Pub/Sub — we use
  **Cloud Run + Firestore + Pub/Sub** ✅ (Cloud Scheduler is extra, not itself one of the
  required five, but doesn't hurt).
- **Judging (Stage Two, 1–5 scale per criterion, averaged):**
  - **Innovation & Operational Utility — 40%.** Track-specific sub-question for
    Taskmaster: *"Does the agent successfully intercept and complete a multi-step
    background workflow without human intervention? Did the team successfully utilize
    the 'Bring Your Own Friction' (BYOF) mandate to solve a unique, personal problem?"*
    **BYOF is new information, not in the internal plan** — Taskmaster is explicitly
    scored partly on whether this solves a real friction *the builder personally has*,
    not a generic B2B pitch.
    **Decided 2026-08-22:** no personal food-service/compliance background exists here —
    do not fabricate one (a false claim risks the "false information" disqualification
    clause and reads as hollow to judges regardless). Instead, frame it honestly around
    a **real, demonstrated operational gap**: small restaurants and independent grocers
    have no realistic way to check every invoice line against every recall bulletin by
    hand — that's a genuinely messy, real chore that exists in the world (backed by the
    $74.7B/year foodborne-illness cost stat), not an invented anecdote. Then put the
    weight of the Innovation score on the *other* half of the same criterion, which is
    fully within engineering control: **"does the agent successfully intercept and
    complete a multi-step background workflow without human intervention."** That's a
    demo-able, provable claim — the honest and higher-EV bet versus a backstory that
    doesn't hold up under a follow-up question. See the `Inspiration` guidance in
    `docs/submission/devpost-description.md`.
  - **Architectural Discipline & Tech Stack — 30%.** The rules' text for this criterion
    is written per-track under alternate track names still in the page copy — the
    Taskmaster-mapped language ("Continuous Action Engine") asks: *"a clean, modularized,
    ease-of-maintenance system... how does the system handle state management? Are the
    tools properly isolated and scoped for security?"* — matches our three-agent
    decoupling + Firestore state design directly.
  - **Demo & Production Readiness — 30%.** *"Unedited, live execution... via terminal
    logs, database updates, or UI changes"* + a clean architecture diagram + reproducible
    setup + visible proof of Google Cloud deployment in the video.
  - **Stage Three bonus, up to +0.6** on a 1–6 final scale: +0.2 public blog/podcast/video
    (must state it was made for this hackathon) · +0.2 social post (X/LinkedIn/Instagram/
    Facebook, must include #AllThingsAgenticHackathon) · +0.2 per additional Google AI
    model integrated (Gemma/Veo/Lyria), capped at +0.6 total.
- **Team:** solo entrants explicitly allowed, no team-size cap.
- **Hosting:** "highly encouraged," not mandatory. **But if we do provide a hosted URL,
  the rules bind us to keep it available free of charge for testing until the Judging
  Period ends (Oct 1, 2026)** — not just through the submission deadline. If no hosted
  URL is provided, judges evaluate from video + text + repo only, no live obligation.
  Cloud Run's scale-to-zero means "available but idle" through Oct 1 should cost close to
  nothing either way, so hosting is low-risk to offer.
  **Decided 2026-08-22: host it, and host the dashboard frontend on Cloud Run too, not
  Vercel.** Vercel was considered (it's free and fast for a static/Next.js frontend), but
  two hard requirements point against splitting the deploy: (1) the "Demo & Production
  Readiness" criterion explicitly wants *visible proof of Google Cloud deployment in the
  video* — a Vercel-hosted frontend dilutes that story even though the backend agents
  would still satisfy the mandatory-tech requirement on their own; (2) a second platform
  means a second set of env vars, CORS/auth config, and a second thing that can break,
  which is real risk on a 9-day clock. Cloud Run's free tier + scale-to-zero already
  costs effectively nothing at this scale, so there's no cost upside to splitting either.
  One platform, one dashboard, one story for the camera.
- **Eligibility:** legal age of majority in country of residence; a short list of excluded
  countries/territories (Italy, Quebec, Crimea, Cuba, Iran, Syria, North Korea, Sudan,
  Belarus, Russia) — self-verify this isn't a blocker before submitting.

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
- **2026-08-22 (same day)** — Added the "Verified live rules" section above after
  fetching the actual Devpost rules page. Corrected the judging-weight framing (it's a
  three-way 40/30/30 split, not a two-way 40/60) and pinned down the real deadline
  (Aug 31, 2026, 5pm PT) and category-selection mechanics, none of which were locked in
  the internal plan. **This changes the day-by-day schedule's feasibility** — see
  `docs/PHASES.md` for the calendar reality check.
- **2026-08-22 (re-verified against the full official rules text, pasted directly from
  Devpost)** — Confirmed the deadline math (Sep 1, 5am GMT+5 = Aug 31, 5pm PT — same
  moment). Added facts not previously captured: the **$150 GCP credit request form
  deadline is Aug 28, 12pm PT** (a real near-term action item); the **Judging Period runs
  through Oct 1, 2026**, and a hosted URL (if offered) must stay available through then,
  not just past the submission deadline; the official cost tips recommend **Gemini Flash
  by default, Pro only for complex reasoning**; and Taskmaster's Innovation criterion
  explicitly names a **"Bring Your Own Friction" (BYOF)** expectation — the project
  should read as solving a real, personally-felt friction, not a generic B2B pitch. None
  of this changes the architecture or scope, but it does change the submission narrative
  and the near-term action list — see `docs/PHASES.md`.
