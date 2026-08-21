# RecallGuard — Risk Register

| Risk | Mitigation |
|---|---|
| No dramatic live recall during build week | Seed with real historical recalls; also show one live poll against the current feed for authenticity, clearly labeled |
| FSIS API auth/access friction | Confirm key requirements on Day 1, not late; openFDA as fallback primary source if FSIS access is delayed |
| openFDA query gotchas eat build time | Budget explicit debugging time early; use the quoting/`.exact`/date-window fixes documented in `docs/PLAN.md` up front |
| Matching accuracy underwhelms | Curate invoice sample diversity deliberately so the demo has at least 2–3 clean true-positive catches |
| Judges perceive "just an API wrapper" | Emphasize the reasoning/confidence output and the human-review exception path on camera — that's the non-automatable part |

Update this table as new risks surface during the build — log the date a risk was
identified and, once mitigated, a short note on how.
