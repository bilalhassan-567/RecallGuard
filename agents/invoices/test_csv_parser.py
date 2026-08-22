"""Tests the CSV parser against the actual sample invoice fixtures (not synthetic mini
CSVs) — the whole point is verifying it handles 5 genuinely different column layouts, so
testing against anything simpler would miss what actually matters here.

Run: python -m unittest test_csv_parser -v
"""
import unittest
from pathlib import Path

import csv_parser

SAMPLES = Path(__file__).parent.parent / "sample_data" / "invoices"


class TestCsvParser(unittest.TestCase):
    def test_sysco_format(self):
        rows = csv_parser.parse_csv(SAMPLES / "sysco_001_true_positive.csv")
        self.assertEqual(len(rows), 6)
        chips = next(r for r in rows if "ONION CHIPS" in r["rawText"])
        self.assertEqual(chips["quantity"], "4")
        self.assertEqual(chips["dateReceived"], "2026-08-15")

    def test_usfoods_format(self):
        rows = csv_parser.parse_csv(SAMPLES / "usfoods_002_true_positive.csv")
        self.assertEqual(len(rows), 5)
        cheese = next(r for r in rows if "REQUESON" in r["rawText"])
        self.assertEqual(cheese["quantity"], "2")

    def test_local_distributor_format(self):
        rows = csv_parser.parse_csv(SAMPLES / "local_distributor_003_near_miss.csv")
        self.assertEqual(len(rows), 5)
        chips = next(r for r in rows if "BBQ" in r["rawText"])
        self.assertEqual(chips["unit"], "bag")

    def test_wholesale_format_missing_unit_column(self):
        rows = csv_parser.parse_csv(SAMPLES / "wholesale_004_easy_negative.csv")
        self.assertEqual(len(rows), 6)
        # No unit-like column in this format — should degrade to empty, not crash.
        self.assertEqual(rows[0]["unit"], "")

    def test_restaurant_depot_format(self):
        rows = csv_parser.parse_csv(SAMPLES / "restaurant_depot_005_ambiguous.csv")
        self.assertEqual(len(rows), 5)
        cheese = next(r for r in rows if "Cottage Cheese" in r["rawText"])
        self.assertEqual(cheese["unit"], "16oz")

    def test_supplier_defaults_to_filename_stem(self):
        rows = csv_parser.parse_csv(SAMPLES / "sysco_001_true_positive.csv")
        self.assertEqual(rows[0]["supplier"], "sysco_001_true_positive")

    def test_supplier_override(self):
        rows = csv_parser.parse_csv(SAMPLES / "sysco_001_true_positive.csv", supplier="Sysco")
        self.assertEqual(rows[0]["supplier"], "Sysco")


if __name__ == "__main__":
    unittest.main()
