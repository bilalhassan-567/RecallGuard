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

## Status as of 2026-08-24

**19/30 agent-side recalls scored, 0 human baseline runs yet.** Results so far:
19/19 detected, 19/19 correctly auto-actioned, 0 false positives (dangerous or soft),
100% precision, 100% recall, ~13s mean time-to-detection. **Not the final numbers** —
report the real N=30 numbers once both sides are complete, not this partial run; see
`docs/EXPERIMENT.md` for the live-updated summary and `docs/PROGRESS.md` for the dated
log of each session's progress.

## To finish this

```
cd agents
python -m experiment.run_benchmark --limit 10   # repeat until "30/30 total scored"
python -m experiment.summarize_results

python -m experiment.run_human_baseline          # a real person, timed, unaided
python -m experiment.summarize_baseline
```
