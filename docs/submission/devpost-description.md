# RecallGuard — Devpost Submission Text (template)

Draft skeleton — fill in the bracketed sections once the build and the N=30 experiment are
done. Track: **The Taskmaster.** State eligibility for Best Architectural Design, Best
Multimodal UX, and Individual/Hobbyist explicitly — judges read this field, and categories
aren't mutually exclusive.

---

## Elevator pitch (one line)

RecallGuard watches FDA and USDA food recall feeds, matches them against a business's own
invoices with Gemini, and drafts the pull-checklist, notification, and compliance record —
flagging anything it isn't sure about instead of guessing.

## What it does

RecallGuard runs three agents against real recall data:

1. **A Recall Monitor** polls FSIS (near-real-time) and openFDA (weekly, historical),
   normalizing both into a single event schema.
2. **A Matching Agent** (Gemini) fuzzy-matches each new recall against a business's
   invoice/POS line items — CSV and, crucially, **photographed/scanned invoices** — and
   returns a confidence score with a stated reason, not a black-box yes/no.
3. **An Action Agent** drafts a pull-checklist, a notification (supplier + health
   department — draft only, never sent), and a timestamped compliance record for anything
   confident enough to auto-action. Anything it isn't confident about goes to a human review
   queue instead of being guessed.

Every step streams into a dashboard styled as a detective's corkboard case board — "Scout"
is the agent's voice and persona; the compliance record artifact itself stays plain and
serious, since that's the one document a health inspector actually reads.

## The honesty guarantees

- `report_date`/`recall_initiation_date` is the trigger signal — never a claim of "live
  recall status" (openFDA's own docs say status isn't reliably tracked).
- Low-confidence matches are never auto-actioned; they're routed to a human with Scout's
  stated reasoning attached.
- Recall content from external feeds is treated as untrusted data passed to Gemini, never
  as instructions — a stated prompt-injection guard, not an afterthought.

## How we built it

Google ADK agents on Cloud Run, event-driven via Pub/Sub (`recall.detected`), state
persisted in Firestore, triggered by Cloud Scheduler, reasoning via Gemini on Vertex AI.
[Fill in specifics once built: models used, any MCP-equivalent tool layer, notable
implementation details.]

## The proof (measured, not estimated)

[Fill in from `docs/EXPERIMENT.md` once the N=30 evaluation runs — precision, recall,
false-positive rate, false-negative rate, mean time-to-detection baseline vs. agent.]

## How it fits The Taskmaster

[Fill in: autonomous, multi-step, background workflow — sense/decide/act, the exception
path, the failure-injection demo moment.]

## Challenges we ran into

[Fill in as they happen — log real ones in `docs/PROGRESS.md` as they're hit, pull the
notable ones here at the end.]

## Accomplishments we're proud of

[Fill in.]

## What we learned

[Fill in.]

## What's next

[Fill in — e.g. additional recall sources, richer few-shot feedback loop from the human
review queue.]

## Built with

Gemini (Vertex AI) · Google ADK · Cloud Run · Firestore · Pub/Sub · Cloud Scheduler ·
[fill in frontend stack once chosen].

## Try it

[Fill in once there's a live URL or clear local spin-up instructions — see the README.]
