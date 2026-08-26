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
  line(s) you pick and how long it took. Also resumable (Ctrl-C saves progress). The
  shown line order is shuffled once with a fixed seed (2026-08-27 fix) so it doesn't
  correlate with recall order — see `docs/PROGRESS.md` for the real bug this fixed.
- **`summarize_baseline.py`** — scores the human run with the same definitions, so the
  two sides are directly comparable.

## Status as of 2026-08-27 — complete on both sides

**Agent: 30/30, 100% precision, 100% recall, 13.44s mean time-to-detection, 0 false
positives.** **Human baseline: 30/30, 96.6% precision, 93.3% recall, 16.4s mean
time-to-detection, 2 missed + 1 wrong pick** (real, plausible human mistakes — see
`docs/EXPERIMENT.md`). Agent beats human on accuracy; the "10× faster" success
criterion is **not** met (actual speedup: 1.22×) — reported honestly, with the reason
why that's not actually the interesting number for this system (see `docs/EXPERIMENT.md`).

The human baseline was run once already and discarded — the shown line order had a
real bug (correlated with recall order, effectively leakable), caught by the person
running it, fixed with a seeded shuffle, and rerun clean. See `docs/PROGRESS.md`,
2026-08-27.

## Reproducing this

```
cd agents
python -m experiment.run_benchmark --limit 30
python -m experiment.summarize_results

python -m experiment.run_human_baseline --limit 10   # repeat until 30/30
python -m experiment.summarize_baseline
```
