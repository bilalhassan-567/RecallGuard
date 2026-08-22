# RecallGuard — Risk Register

| Risk | Mitigation |
|---|---|
| No dramatic live recall during build week | Seed with real historical recalls; also show one live poll against the current feed for authenticity, clearly labeled |
| FSIS API access — **confirmed blocked from both the dev sandbox AND the user's real Pakistani residential network** (2026-08-22/23), same 403 both times. No API key issue (confirmed via real working reference code) — working theory is a geographic block on non-US traffic at the Akamai layer in front of this US federal (.gov) site. | Stopped investigating further in dev — not fixable from here. Use openFDA as the primary/sole trigger source for now. Re-test FSIS once Cloud Run is deployed in a US region (Phase 6+); if still blocked, openFDA-only is the permanent fallback, already accounted for in the plan and in the failure-handling design (retry/log/continue) |
| openFDA query gotchas eat build time | Budget explicit debugging time early; use the quoting/`.exact`/date-window fixes documented in `docs/PLAN.md` up front |
| Matching accuracy underwhelms | Curate invoice sample diversity deliberately so the demo has at least 2–3 clean true-positive catches |
| Judges perceive "just an API wrapper" | Emphasize the reasoning/confidence output and the human-review exception path on camera — that's the non-automatable part |
| $150 GCP credit form deadline (Aug 28, 12pm PT, or while supplies last) missed | Request it immediately — don't bundle with other Day-1 setup, treat as a same-day action independent of the build schedule |
| Taskmaster's BYOF ("Bring Your Own Friction") criterion reads the project as generic B2B rather than a personally-felt problem | Decide the submission narrative deliberately (README + video framing) rather than leaving the personal connection implicit |
| Calendar (9 days from 2026-08-22) doesn't fit the plan's 10-working-day schedule | See `docs/PHASES.md` — pull the N=30 experiment earlier and/or treat Aug 30 as the real internal deadline, Aug 31 as buffer only |
| **Gemini free-tier (AI Studio key) quota is 20 requests/day per model** (hit 2026-08-23, mid-testing — `RESOURCE_EXHAUSTED`, `GenerateRequestsPerDayPerProjectPerModel-FreeTier`). Directly threatens Phase 8's N=30 experiment, which needs far more than 20 calls in one run. | Pace local dev/test calls more deliberately going forward — don't re-run the full demo repeatedly in one session. For Phase 8: either spread the N=30 run across multiple days on the free tier, or move to Vertex AI (paid, higher quota) once GCP billing clears — which we need anyway for the actual deployment. Worth checking Vertex AI's quota story specifically before Phase 8. |

Update this table as new risks surface during the build — log the date a risk was
identified and, once mitigated, a short note on how.
