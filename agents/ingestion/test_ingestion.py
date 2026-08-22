"""Smoke test for both recall ingestion clients. Run: python -m ingestion.test_ingestion

openFDA should just work. FSIS is the one to watch — see the note at the top of
fsis_client.py. If FSIS fails here too, that's a real signal, not a fluke.
"""
import json

import fsis_client
import normalize
import openfda_client


def test_openfda() -> None:
    print("=== openFDA ===")
    raw = openfda_client.fetch_since("2026-08-01")
    print(f"Fetched {len(raw)} raw records")
    if raw:
        sample = normalize.normalize_openfda(raw[0])
        print("Sample normalized record:")
        print(json.dumps({k: v for k, v in sample.items() if k != "rawSourcePayload"}, indent=2))


def test_fsis() -> None:
    print("\n=== FSIS ===")
    try:
        raw = fsis_client.fetch_since("2026-01-01")
        print(f"Fetched {len(raw)} raw records")
        if raw:
            sample = normalize.normalize_fsis(raw[0])
            print("Sample normalized record:")
            print(json.dumps({k: v for k, v in sample.items() if k != "rawSourcePayload"}, indent=2))
    except RuntimeError as err:
        print(f"FSIS FAILED: {err}")
        print("If this fails here too, treat FSIS as unreachable from this network for now —")
        print("see the note at the top of fsis_client.py and docs/RISK_REGISTER.md.")


if __name__ == "__main__":
    test_openfda()
    test_fsis()
