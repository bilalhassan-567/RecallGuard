"""Selects the frozen N=30 recall set for the Phase 8 experiment (docs/EXPERIMENT.md).
Run ONCE — the output (ground_truth_recalls.json) is frozen after that; re-running would
change the evaluation set out from under any invoice test cases already written against
it. Real recalls only (fetched live from openFDA, no Gemini needed), stratified across
classifications so the set isn't skewed toward the easy/common cases.

Run from agents/: python -m experiment.select_ground_truth_recalls
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingestion"))
import normalize  # noqa: E402
import openfda_client  # noqa: E402

OUTPUT_PATH = Path(__file__).resolve().parent / "ground_truth_recalls.json"
TARGET_PER_CLASS = {"Class I": 12, "Class II": 12, "Class III": 6}  # N=30 total
DATE_FROM = "2025-06-01"
DATE_TO = "2026-08-24"


def main() -> None:
    if OUTPUT_PATH.exists():
        print(f"{OUTPUT_PATH} already exists — frozen, not overwriting. Delete it manually if you really mean to reselect.")
        return

    raw = openfda_client.fetch_since(DATE_FROM, DATE_TO)
    print(f"Fetched {len(raw)} candidate recalls from {DATE_FROM} to {DATE_TO}")

    by_class: dict[str, list[dict]] = {}
    for record in raw:
        by_class.setdefault(record.get("classification", "Unknown"), []).append(record)

    selected = []
    seen_firms = set()
    for classification, target_count in TARGET_PER_CLASS.items():
        candidates = by_class.get(classification, [])
        for record in candidates:
            if len(selected) >= sum(TARGET_PER_CLASS.values()):
                break
            firm = record.get("recalling_firm", "")
            # Skip if we already picked this firm — keeps product/supplier diversity
            # instead of several near-duplicate recalls from the same company.
            if firm in seen_firms:
                continue
            class_count = sum(1 for r in selected if r.get("classification") == classification)
            if class_count >= target_count:
                continue
            seen_firms.add(firm)
            selected.append(record)

    normalized = [normalize.normalize_openfda(r) for r in selected]
    OUTPUT_PATH.write_text(json.dumps(normalized, indent=2), encoding="utf-8")

    from collections import Counter
    print(f"Selected {len(normalized)} recalls -> {OUTPUT_PATH}")
    print("By classification:", Counter(r["classification"] for r in normalized))


if __name__ == "__main__":
    main()
