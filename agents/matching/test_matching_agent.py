"""Live test of the Matching Agent against real recalls and the ground-truth cases in
agents/sample_data/invoices/ground_truth.json. Needs a working GOOGLE_API_KEY (network +
real Gemini calls) and is non-deterministic by nature (LLM output) — asserts on the
routing OUTCOME (auto_actioned / pending_review / rejected), not exact confidence numbers
or exact wording, since those can legitimately vary run to run while still being correct.

Run: python -m unittest test_matching_agent -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # agents/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingestion"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "invoices"))

import matching_agent  # noqa: E402  (path setup must run first)
import csv_parser  # noqa: E402
import normalize  # noqa: E402
import openfda_client  # noqa: E402

SAMPLES = Path(__file__).resolve().parent.parent / "sample_data" / "invoices"


class TestMatchingAgentAgainstGroundTruth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chips_recall = normalize.normalize_openfda(
            openfda_client.fetch_by_recall_number("H-0552-2026")
        )
        cls.all_lines = []
        for csv_path in sorted(SAMPLES.glob("*.csv")):
            cls.all_lines.extend(csv_parser.parse_csv(csv_path, supplier=csv_path.stem))
        cls.matches = matching_agent.match_recall_against_lines(cls.chips_recall, cls.all_lines)

    def _status_for(self, text_fragment: str) -> str:
        for m in self.matches:
            if text_fragment in m["invoiceLineRef"]["rawText"]:
                return m["status"]
        self.fail(f"no match returned for a line containing {text_fragment!r}")

    def test_true_positive_auto_actioned(self):
        # "LOWES FD S/C ONION CHIPS 8Z" — the actual recalled product, abbreviated.
        self.assertEqual(self._status_for("ONION CHIPS"), "auto_actioned")

    def test_near_miss_not_auto_actioned(self):
        # Same brand family (Uncle Ray's), different flavor — must NOT be auto-actioned
        # on brand-name similarity alone. pending_review is an acceptable cautious call;
        # auto_actioned would be a real false positive and is the one wrong outcome here.
        status = self._status_for("BBQ Kettle Chips")
        self.assertNotEqual(status, "auto_actioned")

    def test_unrelated_products_rejected(self):
        for fragment in ("Bananas", "Dish Soap", "Coffee Beans"):
            with self.subTest(fragment=fragment):
                self.assertEqual(self._status_for(fragment), "rejected")


if __name__ == "__main__":
    unittest.main()
