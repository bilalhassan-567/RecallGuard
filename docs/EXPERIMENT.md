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

## Implementation

Built in `agents/experiment/` — see that folder's `README.md` for the full tool list and
how to run/resume each half. Summary: 30 real recalls selected live from openFDA
(stratified 12 Class I / 12 Class II / 6 Class III, one per firm for diversity, frozen
after selection), checked against one shared 37-line invoice corpus (30 true positives +
3 near-misses + 4 easy negatives) — matching how the real Matching Agent checks a
business's recent invoice history against each new recall, not one invoice per recall.
The agent-side runner is checkpointed against the free-tier Gemini quota (20 req/day,
see `docs/RISK_REGISTER.md`) so it can run a few recalls at a time across multiple days.
The human-baseline side is a real timed CLI tool, not an informal stopwatch exercise —
same recall order, same invoice list, same scoring code as the agent side, so the
comparison is fair.

---

## Results

**Agent side complete as of 2026-08-26 — full N=30, not a partial run.** Human baseline
side is still 0/30 — that half needs a real unaided person's time and hasn't happened
yet (see `docs/PHASES.md` Phase 8). Reporting the agent numbers now anyway, per the
reporting discipline above — the success threshold in this doc explicitly requires a
comparison against the human baseline, so **this is not yet a completed experiment**,
just a completed half of one:

| Metric (agent, full n=30) | Value |
|---|---|
| Detected | 30/30 |
| Correctly auto-actioned | 30/30 |
| Correctly escalated for review | 0/30 |
| Missed (false negatives) | 0/30 |
| Dangerous false positives (wrongly auto-actioned) | 0 |
| Soft false positives (wrongly escalated) | 0 |
| Precision (on auto-actioned decisions) | 100% |
| Recall | 100% |
| Mean time-to-detection | 13.44s |

This is a genuinely clean run, not a cherry-picked one — two of the three near-miss
distractors (`TWIN SIS CHEDDAR CHEESE 2LB`, `UNCLE RAYS BBQ KETTLE CHIPS 8OZ`) were
tested against their real related recalls in this batch and correctly rejected every
time, which is real evidence the false-positive-avoidance behavior holds across the
full set, not an artifact of an easy test set.

**One honest caveat worth stating plainly, per this doc's own reporting discipline: 0/30
escalated to review is a property of this specific 37-line corpus, not evidence the
escalation path doesn't work.** This N=30 invoice corpus was built with clear true
positives, near-misses, and easy negatives — it doesn't include a deliberately
ambiguous, partial-match case the way the smaller 5-line demo dataset does (the
no-lot-code "Mexican Style Cottage Cheese" case, which correctly routes to
`pending_review` at 55-60% confidence, tested and confirmed separately — see
`docs/PHASES.md` Phase 5/8). A 100% precision/recall number with zero escalations
reads as suspiciously clean in isolation; the actual escalation behavior is real and
demonstrated, just not exercised by this particular N=30 set's design. Worth adding a
deliberately-ambiguous case to a future, larger N if this experiment is extended.

### A second, automated comparison point (not the human baseline)

`experiment/naive_baseline.py` — a non-LLM fuzzy-string matcher (stdlib `difflib`, no
API calls, no human). Not a substitute for the human baseline above; a different,
complementary question: does the Matching Agent's reasoning add value over simple
string similarity, or would naive fuzzy matching get the same result for free?

| Metric (naive baseline, full n=30) | Value |
|---|---|
| Detected | 10/30 (33%) |
| False positives | 0 |
| Precision | 100% |
| Recall | 33.3% |
| Mean time per recall | ~5ms (no API call) |

**Answer: no, it wouldn't.** The naive matcher misses two-thirds of the true positives —
it can't bridge real invoice abbreviation styles (e.g. "Lowes Foods sour cream and onion
flavored potato chips, 8oz. bag" vs. the invoice's "LOWES FD S/C ONION CHIPS 8Z" scores
below the match threshold on raw text similarity alone). This is honest, useful evidence
for why the project reaches for an LLM here instead of simpler string matching — the
gap naive matching leaves is exactly the gap Gemini's reasoning closes.
