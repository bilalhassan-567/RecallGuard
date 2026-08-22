"""Offline unit tests for normalize.py — no network needed, fast, deterministic.

Fixtures are real records, not invented ones: FSIS_SAMPLE was pulled live from
justanesta/food_safety_recalls's committed dataset (2026-08-22); it's a real FSIS recall
(Brazilian Taste, recall #036-2025), used verbatim as ground truth.

Run: python -m unittest test_normalize -v
"""
import unittest

import normalize

FSIS_SAMPLE = {
    "field_title": (
        "Brazilian Taste Recalls Frozen Chicken and Beef Croquette Products Due to "
        "Misbranding and an Undeclared Allergen"
    ),
    "field_recall_url": (
        "http://www.fsis.usda.gov/recalls-alerts/brazilian-taste-recalls-frozen-"
        "chicken-and-beef-croquette-products-due-misbranding"
    ),
    "field_active_notice": "True",
    "field_states": "Nationwide",
    "field_archive_recall": "False",
    "field_closed_date": "",
    "field_establishment": "Brazilian Taste",
    "field_risk_level": "High - Class I",
    "field_last_modified_date": "2025-11-04",
    "field_recall_classification": "Class I",
    "field_recall_date": "2025-11-04",
    "field_recall_number": "036-2025",
    "field_recall_reason": "Misbranding, Unreported Allergens",
    "field_recall_type": "Active Recall",
    "field_related_to_outbreak": "False",
}


class TestNormalizeFsis(unittest.TestCase):
    def test_known_record(self):
        result = normalize.normalize_fsis(FSIS_SAMPLE)
        self.assertEqual(result["source"], "FSIS")
        self.assertEqual(result["sourceRecordId"], "036-2025")
        self.assertEqual(
            result["productDescription"],
            "Brazilian Taste Recalls Frozen Chicken and Beef Croquette Products Due to "
            "Misbranding and an Undeclared Allergen",
        )
        self.assertEqual(result["hazardType"], "Misbranding, Unreported Allergens")
        self.assertEqual(result["classification"], "Class I")
        self.assertEqual(result["distributionStates"], ["Nationwide"])
        self.assertEqual(result["reportDate"], "2025-11-04")
        self.assertEqual(result["lotCodes"], [])
        self.assertEqual(result["rawSourcePayload"], FSIS_SAMPLE)

    def test_missing_fields_dont_crash(self):
        result = normalize.normalize_fsis({})
        self.assertEqual(result["sourceRecordId"], "")
        self.assertEqual(result["distributionStates"], [])


class TestNormalizeOpenFda(unittest.TestCase):
    def test_missing_fields_dont_crash(self):
        result = normalize.normalize_openfda({})
        self.assertEqual(result["source"], "openFDA")
        self.assertEqual(result["sourceRecordId"], "")
        self.assertEqual(result["distributionStates"], [])


class TestSplitStates(unittest.TestCase):
    """Covers the exact bug found and fixed during Phase 2 (2026-08-22): openFDA's
    distribution_pattern field often carries a boilerplate sentence prefix."""

    def test_empty(self):
        self.assertEqual(normalize._split_states(""), [])

    def test_nationwide(self):
        self.assertEqual(normalize._split_states("Nationwide"), ["Nationwide"])

    def test_plain_csv(self):
        self.assertEqual(normalize._split_states("CA, TX, NY"), ["CA", "TX", "NY"])

    def test_boilerplate_prefix(self):
        raw = "The recalled product was distributed to the following states:  MD, VA"
        self.assertEqual(normalize._split_states(raw), ["MD", "VA"])

    def test_single_state_no_comma(self):
        self.assertEqual(normalize._split_states("NC"), ["NC"])


if __name__ == "__main__":
    unittest.main()
