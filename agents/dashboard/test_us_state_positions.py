"""Run: python -m unittest test_us_state_positions -v"""
import unittest

import us_state_positions


class TestPositionsForStates(unittest.TestCase):
    def test_known_state_code(self):
        result = us_state_positions.positions_for_states(["MD"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["state"], "MD")

    def test_lowercase_and_whitespace_normalized(self):
        result = us_state_positions.positions_for_states([" md "])
        self.assertEqual(result[0]["state"], "MD")

    def test_unrecognized_value_skipped_not_guessed(self):
        result = us_state_positions.positions_for_states(["Nationwide", "somewhere unclear"])
        self.assertEqual(result, [])

    def test_mixed_known_and_unknown(self):
        result = us_state_positions.positions_for_states(["VA", "Nationwide", "NC"])
        states = {r["state"] for r in result}
        self.assertEqual(states, {"VA", "NC"})

    def test_every_position_has_valid_percentage_coordinates(self):
        for code, (x, y) in us_state_positions.STATE_POSITIONS.items():
            with self.subTest(state=code):
                self.assertTrue(0 <= x <= 100)
                self.assertTrue(0 <= y <= 100)


if __name__ == "__main__":
    unittest.main()
