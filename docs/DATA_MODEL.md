# RecallGuard — Firestore Data Model

```
businesses/{businessId}
  name, address, contactEmail, registeredAt

businesses/{businessId}/invoices/{invoiceId}
  sourceFileName, sourceType: "csv" | "image", supplier, uploadedAt
  rawLineItems: [
    { lineId, rawText, supplier, quantity, unit, dateReceived, parsedProduct?, parsedLot? }
  ]

recalls/{recallId}                      # normalized, source-agnostic
  source: "FSIS" | "openFDA"
  sourceRecordId
  productDescription
  lotCodes: []
  hazardType
  classification
  distributionStates: []
  reportDate / recallInitiationDate
  rawSourcePayload                      # kept for audit/debug

businesses/{businessId}/matches/{matchId}
  recallId, invoiceLineRef              # invoiceLineRef is a VALUE-COPY of one
                                         # rawLineItems entry at match time, not a
                                         # foreign key — but it carries invoiceId and
                                         # lineId (embedded by the code that assembles
                                         # the line list before matching), which is what
                                         # makes a match traceable back to its source
                                         # invoice. There is no separate top-level
                                         # invoiceId field on the match itself.
  confidenceScore, reasoning            # the agent's stated reasoning — shown in the UI
  status: "auto_actioned" | "pending_review" | "rejected"
  createdAt

businesses/{businessId}/review_queue/{reviewId}
  matchId, reason_for_flag, reviewerDecision, decidedAt

businesses/{businessId}/compliance_log/{logId}
  matchId, actionsTaken: [checklist_generated, notification_drafted, ...]
  generatedArtifactRefs: []
  timestamp

metrics/{businessId}_daily
  recallsChecked, matchesFound, avgTimeToDetectionSeconds, falsePositiveCount (post-hoc labeled)
```

## Notes

- **`recalls/{recallId}` is source-agnostic** — FSIS and openFDA records normalize into the
  same shape so the Matching Agent never has to branch on source. `rawSourcePayload` is kept
  for audit/debug, never used directly in matching logic.
- **`reasoning` on a match is not optional** — it's what makes the demo credible (Scout's
  stated rationale, shown live) and what the N=30 evaluation is scored against.
- **Firestore security rules must scope every read/write to the caller's `businessId`** —
  no cross-business reads, ever (see security notes in `docs/PLAN.md`).
- **`metrics/{businessId}_daily`** is a rollup, not a source of truth — recompute-safe, so a
  bad write here is recoverable from the underlying `matches`/`compliance_log` collections.
