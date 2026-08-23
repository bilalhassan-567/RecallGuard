"""Tests for the Action Agent. No network/LLM needed — everything here is deterministic
templating, which is the whole point (see the security note at the top of action_agent.py).

Run: python -m unittest test_action_agent -v
"""
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import action_agent

TEST_ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "local_data" / "test_artifacts"

RECALL = {
    "source": "openFDA",
    "sourceRecordId": "H-0552-2026",
    "productDescription": "Lowes Foods sour cream and onion flavored potato chips, 8oz. bag",
    "lotCodes": [],
    "hazardType": "Inaccurate nutritional data; undeclared ingredients",
    "classification": "Class II",
}
BUSINESS = {"id": "demo-biz-1", "name": "Maple & Vine Kitchen", "address": "12 Main St"}
AUTO_MATCH = {
    "recallId": "H-0552-2026",
    "invoiceLineRef": {
        "rawText": "LOWES FD S/C ONION CHIPS 8Z",
        "supplier": "sysco_001_true_positive",
        "quantity": "4",
        "dateReceived": "2026-08-15",
    },
    "confidenceScore": 95,
    "reasoning": "Strong match on brand, flavor abbreviation, and size.",
    "status": "auto_actioned",
}
PENDING_MATCH = {**AUTO_MATCH, "status": "pending_review"}


class TestActionAgentRefusal(unittest.TestCase):
    """The structural refusal is the security-relevant behavior — worth its own class."""

    def test_refuses_pending_review_match(self):
        with self.assertRaises(ValueError):
            action_agent.run_action_agent(PENDING_MATCH, RECALL, BUSINESS)

    def test_refuses_rejected_match(self):
        rejected = {**AUTO_MATCH, "status": "rejected"}
        with self.assertRaises(ValueError):
            action_agent.run_action_agent(rejected, RECALL, BUSINESS)


class TestChecklistAndDrafts(unittest.TestCase):
    def test_checklist_fields(self):
        checklist = action_agent.generate_pull_checklist(AUTO_MATCH, RECALL)
        self.assertEqual(checklist["item"], "LOWES FD S/C ONION CHIPS 8Z")
        self.assertEqual(checklist["recallId"], "H-0552-2026")
        self.assertIn("not provided by source", checklist["lotCode"][0])

    def test_storage_hint_matches_chips(self):
        checklist = action_agent.generate_pull_checklist(AUTO_MATCH, RECALL)
        self.assertIn("dry storage", checklist["storageHint"])

    def test_notification_drafts_are_labeled_and_unsendable(self):
        drafts = action_agent.generate_notification_drafts(AUTO_MATCH, RECALL, BUSINESS)
        for draft in drafts.values():
            self.assertIn("DRAFT", draft)
            self.assertIn("NOT SENT", draft)

    def test_no_network_send_capability_in_module(self):
        """Defense in depth: parse the actual imports (not a substring search, which
        would false-positive on the module's own docstring explaining this property) and
        assert none of them are network/send-capable."""
        import ast

        tree = ast.parse(Path(action_agent.__file__).read_text())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        forbidden = {"smtplib", "requests", "urllib.request", "http.client", "socket"}
        self.assertFalse(imported & forbidden, f"found forbidden imports: {imported & forbidden}")


class TestFilenameSafety(unittest.TestCase):
    def test_safe_filename_strips_path_traversal(self):
        result = action_agent._safe_filename("../../etc/passwd")
        self.assertNotIn("/", result)
        self.assertNotIn("..", result)

    def test_safe_filename_strips_special_chars(self):
        result = action_agent._safe_filename('H-0552<script>alert(1)</script>')
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)


class TestRunActionAgentEndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        action_agent.ARTIFACTS_DIR = TEST_ARTIFACTS_DIR  # redirect output for the test run

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_ARTIFACTS_DIR, ignore_errors=True)
        shutil.rmtree(Path(__file__).resolve().parent.parent / "local_data" / "businesses", ignore_errors=True)

    def test_full_run_produces_pdf_and_compliance_log(self):
        result = action_agent.run_action_agent(AUTO_MATCH, RECALL, BUSINESS)
        self.assertTrue(Path(result["compliancePdfPath"]).exists())
        self.assertEqual(result["complianceRecord"]["status"], "draft_ready_for_human_review")
        self.assertIn("checklist_generated", result["complianceRecord"]["actionsTaken"])


class TestResumeAfterPdfFailure(unittest.TestCase):
    """Simulates docs/PLAN.md's failure mode: 'match found, PDF generation fails ->
    workflow resumes from the failed step, not from scratch.'"""

    @classmethod
    def setUpClass(cls):
        action_agent.ARTIFACTS_DIR = TEST_ARTIFACTS_DIR

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_ARTIFACTS_DIR, ignore_errors=True)
        shutil.rmtree(Path(__file__).resolve().parent.parent / "local_data" / "businesses", ignore_errors=True)

    def test_retry_skips_regenerating_artifacts_and_succeeds(self):
        match_id = "resume-test-match"

        with patch.object(action_agent, "generate_pull_checklist", wraps=action_agent.generate_pull_checklist) as spy_checklist:
            with patch.object(action_agent.pdf_export, "write_compliance_pdf", side_effect=RuntimeError("disk full")):
                with self.assertRaises(RuntimeError):
                    action_agent.run_action_agent(AUTO_MATCH, RECALL, BUSINESS, match_id=match_id)
            self.assertEqual(spy_checklist.call_count, 1)  # ran once, before the simulated failure

            progress = action_agent.storage.get(f"businesses/{BUSINESS['id']}/action_progress", match_id)
            self.assertEqual(progress["step"], "artifacts_ready")

            # Retry — PDF export works this time. The checklist must NOT be regenerated.
            result = action_agent.run_action_agent(AUTO_MATCH, RECALL, BUSINESS, match_id=match_id)
            self.assertEqual(spy_checklist.call_count, 1, "checklist was regenerated on retry instead of reusing saved progress")

        self.assertTrue(Path(result["compliancePdfPath"]).exists())
        final_progress = action_agent.storage.get(f"businesses/{BUSINESS['id']}/action_progress", match_id)
        self.assertEqual(final_progress["step"], "complete")

    def test_two_matches_same_recall_dont_collide_when_match_id_given(self):
        """Regression test: found on a real run where the same recall matched two
        different invoice lines for one business — without an explicit match_id, both
        wrote to the same PDF path derived from recall+business alone, and the second
        silently overwrote the first."""
        second_match = {**AUTO_MATCH, "invoiceLineRef": {**AUTO_MATCH["invoiceLineRef"], "rawText": "a different line"}}
        result_a = action_agent.run_action_agent(AUTO_MATCH, RECALL, BUSINESS, match_id="match-a")
        result_b = action_agent.run_action_agent(second_match, RECALL, BUSINESS, match_id="match-b")
        self.assertNotEqual(result_a["compliancePdfPath"], result_b["compliancePdfPath"])
        self.assertTrue(Path(result_a["compliancePdfPath"]).exists())
        self.assertTrue(Path(result_b["compliancePdfPath"]).exists())


if __name__ == "__main__":
    unittest.main()
