"""Live test of multimodal invoice extraction against the synthetic test image in
agents/sample_data/invoices/photo_006_true_positive.jpg (generate it first via
agents/sample_data/generate_test_invoice_image.py if missing). Needs a working
GOOGLE_API_KEY. Non-deterministic by nature (LLM output) — asserts on content being
present, not exact wording.

Run: python -m unittest test_image_parser -v
"""
import unittest
from pathlib import Path

import image_parser

IMAGE_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "invoices" / "photo_006_true_positive.jpg"


class TestImageParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not IMAGE_PATH.exists():
            raise unittest.SkipTest(
                f"{IMAGE_PATH} missing — run generate_test_invoice_image.py first"
            )
        cls.lines = image_parser.parse_image(str(IMAGE_PATH))

    def test_extracted_some_lines(self):
        self.assertGreaterEqual(len(self.lines), 4)

    def test_found_the_recalled_product(self):
        matches = [l for l in self.lines if "requeson" in l["rawText"].lower() or "selectos" in l["rawText"].lower()]
        self.assertTrue(matches, f"expected the Selectos Latinos line, got: {[l['rawText'] for l in self.lines]}")

    def test_line_shape_matches_csv_parser_output(self):
        line = self.lines[0]
        for key in ("rawText", "supplier", "quantity", "unit", "dateReceived", "parsedProduct", "parsedLot"):
            self.assertIn(key, line)


if __name__ == "__main__":
    unittest.main()
