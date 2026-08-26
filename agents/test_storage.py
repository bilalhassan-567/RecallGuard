"""Offline tests for storage.py's local-JSON backend (USE_FIRESTORE unset/False in the
test environment) — round-trips save/get/list_collection/delete against a temp dir.

Run: python -m unittest test_storage -v
"""
import shutil
import unittest
from pathlib import Path

import storage

TEST_DATA_DIR = Path(__file__).resolve().parent / "local_data_test_storage"
storage.DATA_DIR = TEST_DATA_DIR


class TestStorage(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)

    def tearDown(self):
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)

    def test_save_then_get_round_trips(self):
        storage.save("widgets", "w1", {"name": "Widget"})
        self.assertEqual(storage.get("widgets", "w1"), {"name": "Widget"})

    def test_get_missing_doc_returns_none(self):
        self.assertIsNone(storage.get("widgets", "does-not-exist"))

    def test_list_collection_injects_id(self):
        storage.save("widgets", "w1", {"name": "A"})
        storage.save("widgets", "w2", {"name": "B"})
        results = storage.list_collection("widgets")
        ids = {r["_id"] for r in results}
        self.assertEqual(ids, {"w1", "w2"})

    def test_list_collection_empty_when_no_such_collection(self):
        self.assertEqual(storage.list_collection("nonexistent"), [])

    def test_list_collection_overwrites_preexisting_id_field(self):
        storage.save("widgets", "w1", {"name": "A", "_id": "should-be-overwritten"})
        results = storage.list_collection("widgets")
        self.assertEqual(results[0]["_id"], "w1")

    def test_delete_removes_doc(self):
        storage.save("widgets", "w1", {"name": "A"})
        storage.delete("widgets", "w1")
        self.assertIsNone(storage.get("widgets", "w1"))

    def test_delete_missing_doc_does_not_raise(self):
        storage.delete("widgets", "does-not-exist")  # should be a silent no-op


if __name__ == "__main__":
    unittest.main()
