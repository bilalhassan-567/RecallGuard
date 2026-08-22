"""Live network tests against real, specific historical recalls — pinned by exact
recall_number rather than a date window, so they're stable regardless of when they run.
Both recall numbers below were fetched live and manually verified during Phase 2
(2026-08-22/23); this test locks in that ground truth so a future regression is caught.

Needs network access to api.fda.gov (confirmed reachable — see docs/RISK_REGISTER.md;
unlike FSIS, openFDA has no known geographic block).

Run: python -m unittest test_openfda_live -v
"""
import unittest

import normalize
import openfda_client


class TestKnownRecalls(unittest.TestCase):
    def test_uncle_rays_potato_chips_class_ii(self):
        raw = openfda_client.fetch_by_recall_number("H-0552-2026")
        self.assertIsNotNone(raw, "known recall H-0552-2026 not found — API or data changed")
        result = normalize.normalize_openfda(raw)
        self.assertEqual(result["sourceRecordId"], "H-0552-2026")
        self.assertEqual(result["classification"], "Class II")
        self.assertIn("potato chips", result["productDescription"].lower())

    def test_selectos_latinos_cottage_cheese_class_i(self):
        raw = openfda_client.fetch_by_recall_number("H-1219-2026")
        self.assertIsNotNone(raw, "known recall H-1219-2026 not found — API or data changed")
        result = normalize.normalize_openfda(raw)
        self.assertEqual(result["sourceRecordId"], "H-1219-2026")
        self.assertEqual(result["classification"], "Class I")
        self.assertEqual(result["distributionStates"], ["MD", "VA"])
        self.assertIn("listeria", result["hazardType"].lower())

    def test_unknown_recall_number_returns_none(self):
        raw = openfda_client.fetch_by_recall_number("NOT-A-REAL-RECALL-NUMBER-000")
        self.assertIsNone(raw)


if __name__ == "__main__":
    unittest.main()
