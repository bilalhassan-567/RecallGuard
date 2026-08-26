# RecallGuard — Architecture

```mermaid
flowchart TB
    subgraph Sources["Recall sources"]
        FSIS["FSIS Recall API<br/>near-real-time (geo-blocked in dev — see Risk Register)"]
        FDA["openFDA enforcement<br/>weekly, historical"]
    end

    SCHED["Cloud Scheduler<br/>daily poll trigger"]

    subgraph Monitor["Recall Monitor (agent #1) — Cloud Function, HTTP-triggered"]
        MON["Normalizes new recalls, dedups against Firestore<br/>never calls Gemini"]
    end

    TOPIC["Pub/Sub topic: recall-detected"]

    subgraph MatchAction["Matching + Action Agents (#2, #3) — one Cloud Function, Pub/Sub-triggered"]
        MATCH["Matching Agent (Gemini): fuzzy-matches recall vs. invoice line items<br/>returns confidence 0-100 + stated reasoning"]
        ACT["Action Agent: drafts pull-checklist, notification, compliance record<br/>no LLM calls — deterministic templating only"]
        MATCH -->|confidence >= 80| ACT
    end

    UPLOAD["Business user uploads invoice<br/>(CSV or photo) via the dashboard"]
    FS[("Firestore<br/>businesses/{id}/invoices, matches, review_queue, compliance_log")]

    REVIEW["Human Review Queue<br/>(Firestore doc, surfaced in UI)"]
    UI["Dashboard — Cloud Run<br/>reads Firestore in near-real-time"]

    SCHED --> MON
    FSIS -.-> MON
    FDA --> MON
    MON -->|publish, new recalls only| TOPIC
    TOPIC -->|push| MATCH
    UPLOAD --> FS
    MATCH <-->|reads invoice lines, writes match record| FS
    MATCH -->|confidence 40-79| REVIEW
    MATCH -.->|confidence < 40, discarded + logged| FS
    ACT --> FS
    REVIEW --> FS
    FS --> UI
    UI --> UPLOAD
```

*(FSIS is dashed above — the client is built and tested, but geo-blocked from this dev
environment; openFDA is the confirmed-working live trigger source today. See
`docs/RISK_REGISTER.md`.)*

## Why three agents, not one or six

One agent conflates "detect," "reason about a fuzzy match," and "produce a compliance
artifact" into a single prompt — harder to test, harder to explain, and it hides the
exception-handling step judges are told to look for. Three agents map 1:1 to the three real
jobs: **sense → decide → act.**

## Data direction and failure paths

- **Sense (Monitor):** pulls from two external APIs on a schedule. On API failure: retry
  with backoff, log the gap in Firestore, advance nothing — never silently skip a poll
  window.
- **Decide (Matching):** reads an event off Pub/Sub + reads invoice data from Firestore,
  writes a match record back to Firestore with its confidence and reasoning attached. Never
  writes directly to the review queue or compliance log except through its own explicit
  routing decision.
- **Act (Action):** only runs on `auto_actioned` matches. If a downstream step fails
  mid-artifact-generation (e.g. PDF export fails after the checklist succeeds), per-step
  state in Firestore means the workflow resumes from the failed step, not from scratch.
- **Human Review Queue:** the escape hatch for anything the Matching Agent isn't confident
  about — nothing pending review is ever auto-actioned.

## Google Cloud services

| Service | Role |
|---|---|
| Cloud Run | Hosts the dashboard (upload UI, case board, review queue) — scales to zero when idle |
| Cloud Functions (gen2) | Hosts the Recall Monitor (HTTP-triggered) and the Matching+Action pipeline (Pub/Sub-triggered) — same free-tier, no separate always-on services needed |
| Pub/Sub | Decouples detection from matching — async, retryable, fans out per business |
| Firestore | Persistent per-business state across sessions; NoSQL fits variable invoice schemas |
| Gemini API (Developer API / AI Studio key) | The reasoning engine for fuzzy matching, both locally and from the deployed Cloud Function — deliberately **not** Vertex AI, since Vertex has no free tier and this project stays inside Always-Free-tier billing everywhere it can; a one-line env flip (`GOOGLE_GENAI_USE_VERTEXAI=TRUE`) is all a future move to Vertex would need |
| Cloud Scheduler | Triggers the Recall Monitor poll, once daily — the one deterministic piece; the agentic value is downstream |
| Secret Manager | Delivers the Gemini API key to both Cloud Run and the Cloud Functions — never a plain env var |

## Data model and agent logic

- Firestore schema: `docs/DATA_MODEL.md`
- Full per-agent pseudocode: `docs/AGENTS.md`
