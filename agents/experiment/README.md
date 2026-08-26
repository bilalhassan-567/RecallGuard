# experiment/ — the N=30 evaluation (Phase 8, docs/EXPERIMENT.md)

## What's here

- **`ground_truth_recalls.json`** — 30 real recalls (12 Class I / 12 Class II / 6 Class
  III), selected live from openFDA, one per firm for diversity. **Frozen** — don't
  re-run the selector once invoice test cases are written against it.
- **`invoices/`** — a shared invoice corpus (3 CSVs, 37 lines): one realistic
  abbreviated true-positive line per recall, plus 7 distractors (3 near-misses, 4 easy
  negatives). Checked against every recall, same as the real Matching Agent would check
  a business's recent invoice history against each new recall — not one invoice per
  recall.
- **`invoice_ground_truth.json`** — the answer key. Also frozen.
- **`run_benchmark.py`** — runs the agent side. **Checkpointed against the 20/day
  free-tier Gemini quota** (docs/RISK_REGISTER.md) — completed recalls are saved to
  `benchmark_results.jsonl` immediately and skipped on the next run, so it's safe to run
  a few at a time across multiple days: `python -m experiment.run_benchmark --limit 10`.
- **`summarize_results.py`** — scores the agent's results: precision, recall, false
  positives (split into "dangerous" — wrongly auto-actioned — vs. "soft" — wrongly
  escalated to review, not acted on), mean time-to-detection.
- **`run_human_baseline.py`** — the human half. A real timed CLI (not "go do this with a
  stopwatch") — shows the same recall + same invoice list the agent sees, records which
  line(s) you pick and how long it took. Also resumable (Ctrl-C saves progress).
- **`summarize_baseline.py`** — scores the human run with the same definitions, so the
  two sides are directly comparable.

## Status as of 2026-08-26

**Agent side complete: 30/30 scored.** 30/30 detected, 30/30 correctly auto-actioned,
0 false positives (dangerous or soft), 100% precision, 100% recall, 13.44s mean
time-to-detection. **Human baseline is still 0/30** — that half needs a real unaided
person's time and can't be run by an AI without fabricating the exact comparison this
experiment exists to make. See `docs/EXPERIMENT.md` for the full write-up, including an
honest caveat about why 0/30 cases escalated to review in this particular corpus (a
property of this test set's design, not evidence the escalation path doesn't work).

## To finish this

Only the human side remains:

```
cd agents
python -m experiment.run_human_baseline --limit 10   # a real person, timed, unaided — repeat until 30/30
python -m experiment.summarize_baseline
```
