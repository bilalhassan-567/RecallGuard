# RecallGuard — 4-Minute Demo Script

Draft, timestamped — refine once the build exists to record against. Be explicit on camera
about which parts are live-triggered vs. seeded historical data; an honest, unedited demo
reads as more credible than an oversold one.

- **0:00–0:25 — Problem.** "Every year, small restaurants and grocers get the same recall
  notices as everyone else — but nobody has time to check every invoice against every
  recall. Foodborne illness costs the U.S. $74.7 billion a year, per USDA's Economic
  Research Service."
- **0:25–0:55 — Hook.** Show a real historical recall notice + a real sample invoice side
  by side. "Would you have caught this? Meet Scout — RecallGuard's detective agent."
- **0:55–2:30 — Live run, narrated in Scout's voice.** Cloud Scheduler triggers → Cloud Run
  logs show the Monitor agent firing → Pub/Sub message → a new case gets pinned on the
  corkboard → Matching Agent's reasoning appears on screen (the actual confidence + reasoning
  text) → string connects the recall poster to the matching invoice evidence card →
  paw-stamp lands: "CAUGHT IT." Action Agent produces the checklist/notification/compliance
  record, visible live in Firestore. Cut to one low-confidence case: "Scout's unsure — take
  a look" routes to the case-file review screen instead of guessing — the exception-handling
  moment, shown, not claimed.
- **2:30–3:15 — The proof.** The deliberately unfunny, serious compliance record artifact
  side by side with the fun UI, and the dashboard with the real N=30 experiment numbers
  (time-to-detection, precision/recall) plus the streak counter. Include the
  photographed/scanned invoice case explicitly — "this one wasn't a clean CSV, it's a photo
  of a real invoice" — the Best Multimodal UX moment.
- **3:15–3:45 — Live failure-injection beat.** Kill the recall API connection or feed a
  malformed record on camera; show the system retry/log/degrade gracefully instead of
  crashing. "This is what happens when a tool fails — the agent doesn't guess, it flags it."
- **3:45–4:00 — Architecture + proof of Cloud.** Diagram walkthrough + Google Cloud Console
  proof (Cloud Run service page, Vertex AI request logs, Firestore data browser).

## Recording checklist (fill in once there's a build to record)

- [ ] Fault/failure scenario rehearsed until it's a clean, repeatable ~15s beat
- [ ] Real N=30 numbers pulled from `docs/EXPERIMENT.md` results (not estimated)
- [ ] Photographed invoice case pre-selected and verified to work on camera
- [ ] Screen recording at 1080p+, audio checked, no third-party copyrighted music
