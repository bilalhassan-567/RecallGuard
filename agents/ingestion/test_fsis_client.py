"""Tests the retry/backoff failure-handling behavior itself (docs/PLAN.md's failure-modes
table: "Recall API unreachable -> Retry with backoff; log gap; monitor doesn't silently
skip") — not just that fsis_client.py has retry code, but that it actually retries the
right number of times and eventually fails loudly rather than swallowing the error.
Mocks requests.get and time.sleep so this runs in milliseconds, not ~15s of real backoff.

Run: python -m unittest test_fsis_client -v
"""
import unittest
from unittest.mock import MagicMock, patch

import requests

import fsis_client


class TestFsisRetryBehavior(unittest.TestCase):
    @patch("fsis_client.time.sleep")
    @patch("fsis_client.requests.get")
    def test_succeeds_immediately_when_reachable(self, mock_get, mock_sleep):
        mock_response = MagicMock()
        mock_response.json.return_value = [{"field_recall_number": "001-2026"}]
        mock_get.return_value = mock_response

        result = fsis_client.fetch_all()

        self.assertEqual(result, [{"field_recall_number": "001-2026"}])
        self.assertEqual(mock_get.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("fsis_client.time.sleep")
    @patch("fsis_client.requests.get")
    def test_retries_on_transient_failure_then_succeeds(self, mock_get, mock_sleep):
        mock_response = MagicMock()
        mock_response.json.return_value = [{"field_recall_number": "001-2026"}]
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("transient network blip"),
            mock_response,
        ]

        result = fsis_client.fetch_all()

        self.assertEqual(result, [{"field_recall_number": "001-2026"}])
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once()  # backed off once, between attempt 1 and 2

    @patch("fsis_client.time.sleep")
    @patch("fsis_client.requests.get")
    def test_raises_loudly_after_exhausting_all_attempts(self, mock_get, mock_sleep):
        """The failure mode this exists to prevent: silently returning nothing/stale
        data instead of a real, visible failure the caller (and eventually the Recall
        Monitor's logging) can act on."""
        mock_get.side_effect = requests.exceptions.ConnectionError("still down")

        with self.assertRaises(RuntimeError) as ctx:
            fsis_client.fetch_all()

        self.assertIn("unreachable after 3 attempts", str(ctx.exception))
        self.assertEqual(mock_get.call_count, fsis_client.MAX_ATTEMPTS)
        self.assertEqual(mock_sleep.call_count, fsis_client.MAX_ATTEMPTS - 1)  # backs off between attempts, not after the last one

    @patch("fsis_client.time.sleep")
    @patch("fsis_client.requests.get")
    def test_http_error_status_also_triggers_retry(self, mock_get, mock_sleep):
        """A 403/500 (the actual real-world failure this project hit — see the module
        docstring) must retry the same as a connection error, not just network-level
        exceptions."""
        error_response = MagicMock()
        error_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Forbidden")
        mock_get.return_value = error_response

        with self.assertRaises(RuntimeError):
            fsis_client.fetch_all()

        self.assertEqual(mock_get.call_count, fsis_client.MAX_ATTEMPTS)


if __name__ == "__main__":
    unittest.main()
