"""Local stand-in for Firestore, used until the GCP project/billing is unblocked (see
docs/PHASES.md). Same collection/document addressing Firestore uses
(`businesses/{id}/invoices/{id}`), backed by plain JSON files instead of the real thing —
swapping to real Firestore later means rewriting these functions' bodies, not the agent
code that calls them, since the call shape (collection_path, doc_id, data) stays the same.

Storage root is gitignored (agents/local_data/) — this is runtime state, not source.
"""
import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "local_data"


def save(collection_path: str, doc_id: str, data: dict) -> None:
    path = _doc_path(collection_path, doc_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def get(collection_path: str, doc_id: str) -> dict[str, Any] | None:
    path = _doc_path(collection_path, doc_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_collection(collection_path: str) -> list[dict[str, Any]]:
    dir_path = DATA_DIR / collection_path
    if not dir_path.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(dir_path.glob("*.json"))]


def _doc_path(collection_path: str, doc_id: str) -> Path:
    return DATA_DIR / collection_path / f"{doc_id}.json"
