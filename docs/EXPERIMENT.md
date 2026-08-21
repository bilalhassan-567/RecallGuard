# RecallGuard — Quantitative Experiment

This is what produces the real numbers for the demo and submission — run for real, not
estimated. Results get filled in here (and cross-checked against `docs/PHASES.md` Phase 8)
once the matching agent exists.

## Design

- **Dataset:** 30 real historical recalls pulled from openFDA/FSIS archives — a mix of
  Class I/II/III, a mix of hazard types.
- **Invoice sample:** built so some invoices genuinely contain a recalled lot (true
  positives), some contain similar-but-not-recalled products (near-miss true negatives, to
  test false-positive rate), and some are unrelated (easy true negatives).
- **Baseline:** a human manually checks each of the 30 recalls against the invoice set,
  unaided. Time and correctness recorded.
- **Agent condition:** the same 30 cases run through RecallGuard. Time-to-detection, match
  confidence, and correctness recorded against the hand-labeled ground truth.

## Metrics reported

Precision, recall, false-positive rate, false-negative rate, mean time-to-detection
(baseline vs. agent), and number of cases correctly escalated to human review vs. wrongly
auto-actioned.

## Success threshold

Agent accuracy ≥ baseline human accuracy on the same set, with at least a 10× reduction in
mean time-to-detection, and **zero high-confidence false positives** that would have
triggered an unnecessary supplier notification.

## Reporting discipline

Report the numbers exactly as measured, even if imperfect — "82% precision, 91% recall, 40
seconds vs. 22 minutes" reads as credible; a suspiciously clean 100% reads as staged.

---

## Results

*(Not yet run — Phase 8. This section gets filled in with the actual measured table once
the experiment executes, plus a short note on any misses and why.)*
