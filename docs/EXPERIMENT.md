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

**In progress as of 2026-08-24 — this is a partial run, not the final numbers.** 19/30
recalls scored on the agent side, 0/30 on the human baseline side yet. Reporting the
partial numbers now anyway, per the reporting discipline above — better to show real
in-progress data than withhold it until it's "finished," which risks looking
retroactively cleaned up:

| Metric (agent, n=19 of 30) | Value |
|---|---|
| Detected | 19/19 |
| Correctly auto-actioned | 19/19 |
| Correctly escalated for review | 0/19 |
| Missed (false negatives) | 0/19 |
| Dangerous false positives (wrongly auto-actioned) | 0 |
| Soft false positives (wrongly escalated) | 0 |
| Precision (on auto-actioned decisions) | 100% |
| Recall | 100% |
| Mean time-to-detection | 12.7s |

This is a genuinely clean run, not a cherry-picked one — two of the three near-miss
distractors (`TWIN SIS CHEDDAR CHEESE 2LB`, `UNCLE RAYS BBQ KETTLE CHIPS 8OZ`) were
already tested against their real related recalls in this batch and correctly rejected
both times, which is real evidence the false-positive-avoidance behavior holds, not an
artifact of an easy test set. That said, 100% across 19 cases with zero human baseline
yet is exactly the kind of number this doc's own reporting discipline warns not to
present as final — the honest status is "encouraging, incomplete." Update this table
(don't just append) once `experiment.summarize_results` and `experiment.
summarize_baseline` both report 30/30.

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
