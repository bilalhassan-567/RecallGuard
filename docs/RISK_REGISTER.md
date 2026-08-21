# RecallGuard — Risk Register

| Risk | Mitigation |
|---|---|
| No dramatic live recall during build week | Seed with real historical recalls; also show one live poll against the current feed for authenticity, clearly labeled |
| FSIS API auth/access friction | Confirm key requirements on Day 1, not late; openFDA as fallback primary source if FSIS access is delayed |
| openFDA query gotchas eat build time | Budget explicit debugging time early; use the quoting/`.exact`/date-window fixes documented in `docs/PLAN.md` up front |
| Matching accuracy underwhelms | Curate invoice sample diversity deliberately so the demo has at least 2–3 clean true-positive catches |
| Judges perceive "just an API wrapper" | Emphasize the reasoning/confidence output and the human-review exception path on camera — that's the non-automatable part |
| $150 GCP credit form deadline (Aug 28, 12pm PT, or while supplies last) missed | Request it immediately — don't bundle with other Day-1 setup, treat as a same-day action independent of the build schedule |
| Taskmaster's BYOF ("Bring Your Own Friction") criterion reads the project as generic B2B rather than a personally-felt problem | Decide the submission narrative deliberately (README + video framing) rather than leaving the personal connection implicit |
| Calendar (9 days from 2026-08-22) doesn't fit the plan's 10-working-day schedule | See `docs/PHASES.md` — pull the N=30 experiment earlier and/or treat Aug 30 as the real internal deadline, Aug 31 as buffer only |

Update this table as new risks surface during the build — log the date a risk was
identified and, once mitigated, a short note on how.
