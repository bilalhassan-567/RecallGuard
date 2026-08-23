"""Run: python -m unittest test_naive_baseline -v"""
import unittest

from naive_baseline import best_match


class TestBestMatch(unittest.TestCase):
    def test_exact_text_scores_1(self):
        _, score = best_match("SOME PRODUCT", ["SOME PRODUCT", "unrelated"])
        self.assertEqual(score, 1.0)

    def test_completely_unrelated_scores_low(self):
        _, score = best_match("Ellsworth Sour Cream and Onion Seasoning", ["Toasted Cherry Biscotti"])
        self.assertLess(score, 0.3)

    def test_picks_the_higher_scoring_line(self):
        line, score = best_match(
            "Ellsworth Sour Cream and Onion Seasoning",
            ["Toasted Cherry Biscotti", "Ellsworth Sour Cream and Onion Seasoning 25lb"],
        )
        self.assertIn("Ellsworth", line)

    def test_empty_lines_returns_zero_score(self):
        line, score = best_match("anything", [])
        self.assertEqual(score, 0.0)
        self.assertEqual(line, "")

    def test_heavy_abbreviation_scores_below_naive_threshold(self):
        """Documents the actual finding: this is WHY the naive baseline undershoots —
        real invoice abbreviation styles score below the 0.5 threshold even for a true
        match, which is exactly the gap the LLM's reasoning closes."""
        _, score = best_match(
            "Lowes Foods sour cream and onion flavored potato chips, 8oz. bag, UPC 7 41643 05576 6",
            ["LOWES FD S/C ONION CHIPS 8Z"],
        )
        self.assertLess(score, 0.5)


if __name__ == "__main__":
    unittest.main()
