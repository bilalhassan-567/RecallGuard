"""Offline tests for invoice_store.py — no Firestore, no Gemini, no network. Redirects
storage.DATA_DIR to a temp directory, same pattern as agents/dashboard/test_server.py.

Run: python -m unittest test_invoice_store -v
"""
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import storage  # noqa: E402

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "local_data_test_invoice_store"
storage.DATA_DIR = TEST_DATA_DIR  # redirect BEFORE importing invoice_store, which imports storage too

import invoice_store  # noqa: E402

BUSINESS_ID = "biz-1"

SAMPLE_LINES = [
    {"rawText": "Chicken Breast 40lb", "supplier": "Sysco", "quantity": "2", "unit": "case",
     "dateReceived": "2026-08-01", "parsedProduct": None, "parsedLot": None},
    {"rawText": "Ground Beef 80/20", "supplier": "Sysco", "quantity": "1", "unit": "case",
     "dateReceived": "2026-08-01", "parsedProduct": None, "parsedLot": None},
]


class TestInvoiceStore(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)

    def tearDown(self):
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)

    def test_create_invoice_assigns_line_ids_and_resolves_supplier(self):
        invoice = invoice_store.create_invoice(BUSINESS_ID, "sysco_aug.csv", "csv", SAMPLE_LINES)

        self.assertEqual(invoice["sourceFileName"], "sysco_aug.csv")
        self.assertEqual(invoice["sourceType"], "csv")
        self.assertEqual(invoice["supplier"], "Sysco")  # resolved from the lines' own supplier field
        self.assertEqual(len(invoice["rawLineItems"]), 2)
        line_ids = {line["lineId"] for line in invoice["rawLineItems"]}
        self.assertEqual(len(line_ids), 2)  # unique per line

    def test_create_invoice_rejects_empty_lines(self):
        with self.assertRaises(ValueError):
            invoice_store.create_invoice(BUSINESS_ID, "empty.csv", "csv", [])

    def test_create_invoice_rejects_bad_source_type(self):
        with self.assertRaises(ValueError):
            invoice_store.create_invoice(BUSINESS_ID, "x.csv", "pdf", SAMPLE_LINES)

    def test_flatten_invoice_lines_embeds_invoice_id(self):
        inv1 = invoice_store.create_invoice(BUSINESS_ID, "a.csv", "csv", SAMPLE_LINES)
        inv2 = invoice_store.create_invoice(BUSINESS_ID, "b.csv", "csv", SAMPLE_LINES[:1])

        flat = invoice_store.flatten_invoice_lines(BUSINESS_ID)

        self.assertEqual(len(flat), 3)
        invoice_ids_seen = {line["invoiceId"] for line in flat}
        self.assertEqual(invoice_ids_seen, {inv1["_id"], inv2["_id"]})

    def test_flatten_skips_legacy_docs_without_raw_line_items(self):
        storage.save(f"businesses/{BUSINESS_ID}/invoices", "legacy-line-1", {
            "rawText": "Old flat line", "supplier": "Legacy", "quantity": "1",
            "unit": "", "dateReceived": "", "parsedProduct": None, "parsedLot": None,
        })
        flat = invoice_store.flatten_invoice_lines(BUSINESS_ID)
        self.assertEqual(flat, [])

    def test_list_invoices_reflects_reconciliation_counts(self):
        inv = invoice_store.create_invoice(BUSINESS_ID, "a.csv", "csv", SAMPLE_LINES)
        line_id = inv["rawLineItems"][0]["lineId"]
        storage.save(f"businesses/{BUSINESS_ID}/matches", "m1", {
            "recallId": "R-1",
            "invoiceLineRef": {**inv["rawLineItems"][0], "invoiceId": inv["_id"]},
            "confidenceScore": 90, "reasoning": "x", "status": "auto_actioned", "createdAt": "2026-08-01T00:00:00Z",
        })
        storage.save(f"businesses/{BUSINESS_ID}/matches", "m2", {
            "recallId": "R-2",
            "invoiceLineRef": {**inv["rawLineItems"][1], "invoiceId": inv["_id"]},
            "confidenceScore": 50, "reasoning": "x", "status": "pending_review", "createdAt": "2026-08-01T00:00:00Z",
        })

        summaries = invoice_store.list_invoices(BUSINESS_ID)

        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["lineCount"], 2)
        self.assertEqual(summaries[0]["autoActionedCount"], 1)
        self.assertEqual(summaries[0]["flaggedCount"], 1)
        self.assertEqual(summaries[0]["cleanCount"], 0)
        self.assertEqual(line_id, inv["rawLineItems"][0]["lineId"])  # sanity on fixture setup

    def test_get_invoice_detail_returns_match_history_sorted_desc(self):
        inv = invoice_store.create_invoice(BUSINESS_ID, "a.csv", "csv", SAMPLE_LINES[:1])
        line_id = inv["rawLineItems"][0]["lineId"]
        storage.save(f"businesses/{BUSINESS_ID}/matches", "m1", {
            "recallId": "R-1", "invoiceLineRef": {"invoiceId": inv["_id"], "lineId": line_id},
            "confidenceScore": 30, "reasoning": "old", "status": "rejected", "createdAt": "2026-08-01T00:00:00Z",
        })
        storage.save(f"businesses/{BUSINESS_ID}/matches", "m2", {
            "recallId": "R-2", "invoiceLineRef": {"invoiceId": inv["_id"], "lineId": line_id},
            "confidenceScore": 90, "reasoning": "new", "status": "auto_actioned", "createdAt": "2026-08-02T00:00:00Z",
        })

        detail = invoice_store.get_invoice_detail(BUSINESS_ID, inv["_id"])

        self.assertIsNotNone(detail)
        history = detail["lines"][0]["matchHistory"]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["recallId"], "R-2")  # most recent first

    def test_get_invoice_detail_returns_none_for_unknown_id(self):
        self.assertIsNone(invoice_store.get_invoice_detail(BUSINESS_ID, "does-not-exist"))

    def test_delete_invoice(self):
        inv = invoice_store.create_invoice(BUSINESS_ID, "a.csv", "csv", SAMPLE_LINES)
        self.assertTrue(invoice_store.delete_invoice(BUSINESS_ID, inv["_id"]))
        self.assertIsNone(invoice_store.get_invoice_detail(BUSINESS_ID, inv["_id"]))

    def test_delete_unknown_invoice_returns_false(self):
        self.assertFalse(invoice_store.delete_invoice(BUSINESS_ID, "does-not-exist"))


if __name__ == "__main__":
    unittest.main()
