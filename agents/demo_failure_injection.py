"""Live failure-injection demo, for the demo video's failure-handling beat
(docs/PHASES.md Phase 9). Costs zero Gemini quota — the Action Agent makes no LLM calls
at all, so this is free to rehearse as many times as needed.

This is a REAL failure, not a mock: it replaces agents/local_data/artifacts (normally a
directory) with a plain file, so pdf_export.write_compliance_pdf's own
`output_path.parent.mkdir(...)` genuinely raises an OS error. Shows the checklist and
notification drafts already survived the crash (per-step progress state), removes the
injected failure, and re-runs to completion.

Runs against LOCAL storage only (agents/local_data/), never production Firestore,
regardless of any USE_FIRESTORE setting elsewhere — safe to run repeatedly without
touching anything live. Clears any existing files under agents/local_data/artifacts/
each run (regenerable output, not source — same as every other local_data/ path in this
project).

Run from agents/: python demo_failure_injection.py
"""
import shutil
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent / "action"))

import action_agent  # noqa: E402
import storage  # noqa: E402

storage.USE_FIRESTORE = False  # this demo never touches production, regardless of env

DEMO_BUSINESS_ID = "demo-biz-1"
DEMO_MATCH_ID = "failure-injection-demo"

PAUSE = 1.2  # seconds between beats, tune to taste when actually recording


def main() -> None:
    business = storage.get("businesses", DEMO_BUSINESS_ID) or {
        "id": DEMO_BUSINESS_ID, "name": "Maple & Vine Kitchen",
    }
    recall = {
        "source": "openFDA", "sourceRecordId": "DEMO-RECALL-001",
        "productDescription": "Demo Recalled Product — Failure-Injection Rehearsal",
        "hazardType": "Demo hazard", "classification": "Class I", "lotCodes": [],
    }
    match = {
        "recallId": recall["sourceRecordId"],
        "invoiceLineRef": {
            "rawText": "Demo Item", "supplier": "Demo Supplier",
            "quantity": "1", "unit": "case", "dateReceived": "2026-08-26",
        },
        "confidenceScore": 95, "reasoning": "Demo match for rehearsal.", "status": "auto_actioned",
    }

    storage.delete(f"businesses/{DEMO_BUSINESS_ID}/action_progress", DEMO_MATCH_ID)
    storage.delete(f"businesses/{DEMO_BUSINESS_ID}/compliance_log", DEMO_MATCH_ID)
    artifacts_dir = action_agent.ARTIFACTS_DIR
    shutil.rmtree(artifacts_dir, ignore_errors=True)

    _beat("STEP 1 — Inject a real failure: block the artifacts directory")
    artifacts_dir.parent.mkdir(parents=True, exist_ok=True)
    artifacts_dir.write_text("blocking file — simulates a real disk/permissions failure")
    print(f"Created a FILE at {artifacts_dir} (a directory is expected there).")

    _beat("STEP 2 — Run the Action Agent and watch it fail for real")
    try:
        action_agent.run_action_agent(match, recall, business, match_id=DEMO_MATCH_ID)
        print("UNEXPECTED: this should have failed — demo setup is broken.")
        return
    except Exception as e:
        print(f"Failed as expected: {type(e).__name__}: {e}")

    _beat("STEP 3 — Check what survived the crash")
    progress = storage.get(f"businesses/{DEMO_BUSINESS_ID}/action_progress", DEMO_MATCH_ID)
    print(f"Progress state: step={progress.get('step')!r}")
    print(f"Checklist already generated: {progress['checklist']['item']!r} "
          f"-> stored at {progress['checklist']['storageHint']!r}")
    print("The checklist and notification drafts survived the crash — only the PDF step failed.")

    _beat("STEP 4 — Fix the failure and retry")
    artifacts_dir.unlink()
    print(f"Removed the blocking file at {artifacts_dir}.")
    result = action_agent.run_action_agent(match, recall, business, match_id=DEMO_MATCH_ID)
    print(f"Succeeded. PDF written to: {result['compliancePdfPath']}")
    print("The checklist/drafts were reused from Step 3's saved state, not regenerated.")


def _beat(title: str) -> None:
    time.sleep(PAUSE)
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


if __name__ == "__main__":
    main()
