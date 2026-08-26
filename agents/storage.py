"""Firestore-addressed storage, backed by either real Firestore or a local JSON-file
stand-in depending on USE_FIRESTORE. Same collection/document addressing Firestore uses
(`businesses/{id}/invoices/{id}`) either way, so the agent code calling these functions
(collection_path, doc_id, data) never needs to know which backend is live.

Local mode's storage root is gitignored (agents/local_data/) — runtime state, not source.
Firestore mode requires GOOGLE_APPLICATION_CREDENTIALS or ambient GCP credentials
(Cloud Run's default service account provides this automatically; no explicit key file
needed there).
"""
import json
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "local_data"

USE_FIRESTORE = os.environ.get("USE_FIRESTORE", "FALSE").upper() == "TRUE"

_firestore_client = None


def _client():
    global _firestore_client
    if _firestore_client is None:
        from google.cloud import firestore
        _firestore_client = firestore.Client()
    return _firestore_client


def save(collection_path: str, doc_id: str, data: dict) -> None:
    if USE_FIRESTORE:
        _client().collection(collection_path).document(doc_id).set(data)
        return
    path = _doc_path(collection_path, doc_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def get(collection_path: str, doc_id: str) -> dict[str, Any] | None:
    if USE_FIRESTORE:
        snapshot = _client().collection(collection_path).document(doc_id).get()
        return snapshot.to_dict() if snapshot.exists else None
    path = _doc_path(collection_path, doc_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_collection(collection_path: str) -> list[dict[str, Any]]:
    """Each returned dict gets an `_id` key (the document's own ID) even if the caller
    never stored one — otherwise a caller has no reliable way to know which document a
    listed record came from. Overwrites any pre-existing `_id` field in the stored data;
    don't use that key for anything else."""
    if USE_FIRESTORE:
        results = []
        for snapshot in _client().collection(collection_path).stream():
            record = snapshot.to_dict() or {}
            record["_id"] = snapshot.id
            results.append(record)
        return results
    dir_path = DATA_DIR / collection_path
    if not dir_path.exists():
        return []
    results = []
    for p in sorted(dir_path.glob("*.json")):
        record = json.loads(p.read_text(encoding="utf-8"))
        record["_id"] = p.stem
        results.append(record)
    return results


def _doc_path(collection_path: str, doc_id: str) -> Path:
    return DATA_DIR / collection_path / f"{doc_id}.json"
