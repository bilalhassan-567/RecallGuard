# RecallGuard — Agent Logic

Pseudocode for the three ADK agents. See `docs/ARCHITECTURE.md` for how they connect and
`docs/DATA_MODEL.md` for the schemas referenced below.

## Agent 1 — Recall Monitor

```
on schedule (every 15 min, or on Pub/Sub push if FSIS supports it):
  fetch new records from FSIS API where reportDate > last_checked_cursor
  fetch new records from openFDA where report_date > last_checked_cursor
    (respect quoting/.exact rules; page past the 26k-result cap using
     report_date-bounded windows, not raw skip)
  normalize both into the recalls/{recallId} schema
  write to Firestore
  publish one Pub/Sub message per new recall to topic "recall.detected"
  advance cursor
```

## Agent 2 — Matching Agent (subscribes to `recall.detected`)

```
on message(recallId):
  recall = Firestore.get(recallId)
  for each business in businesses:
    candidateLines = business.invoices.recentLineItems (e.g. trailing 120 days)
    prompt Gemini with:
      - recall.productDescription, recall.lotCodes, recall.hazardType
      - candidateLines (raw, messy text)
      - instruction: "For each line, decide: does this plausibly refer to the
         recalled product? Give a confidence 0-100 and a one-sentence reason.
         If uncertain, say so — do not guess."
    for each returned candidate match:
      if confidence >= 80: status = "auto_actioned"; enqueue Action Agent
      elif confidence >= 40: status = "pending_review"; write to review_queue
      else: discard (log as considered-and-rejected, for the false-negative audit)
    write match record with reasoning text stored (needed for the demo and the eval)
```

## Agent 3 — Action Agent

```
on new "auto_actioned" match:
  generate:
    - pull_checklist (structured list: item, location-in-storage hint, lot code, quantity if known)
    - notification_draft (to supplier + to local health dept template — DRAFT ONLY, not sent)
    - compliance_record (what was detected, when, what action was drafted, confidence + reasoning attached)
  write artifacts to Firestore + generate a downloadable PDF
  update compliance_log
```

## Human review loop

The dashboard surfaces `pending_review` items; a human clicks confirm/reject; the decision
is logged. (Stretch: feed confirmed/rejected decisions back as few-shot examples to improve
future matching — a "improves through feedback" story, though the submission itself targets
Taskmaster, not Collaborative Partner.)

## Prompt-injection guard

Recall content (from FSIS/openFDA) is **untrusted data**, never instructions. It's passed
to Gemini as data to reason about, never concatenated into anything that could alter agent
behavior or trigger unintended tool calls. This applies at every step that touches raw
recall text, not just the Matching Agent.
