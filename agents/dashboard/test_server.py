"""API tests for the dashboard backend, using FastAPI's TestClient (no live server, no
network, no Gemini calls) against a temporary storage directory — never touches real
agents/local_data/.

Run: python -m unittest test_server -v
"""
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "action"))

import storage  # noqa: E402

TEST_DATA_DIR = Path(__file__).resolve().parent.parent / "local_data_test_dashboard"
storage.DATA_DIR = TEST_DATA_DIR  # redirect BEFORE importing server, which imports storage too

import action_agent  # noqa: E402

action_agent.ARTIFACTS_DIR = TEST_DATA_DIR / "artifacts"  # keep test PDFs out of the real local_data/

import server  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

BUSINESS = {"id": "biz-1", "name": "Test Kitchen"}
RECALL = {
    "source": "openFDA",
    "sourceRecordId": "R-1",
    "productDescription": "Test Recalled Product",
    "hazardType": "Test hazard",
    "classification": "Class I",
}


class TestDashboardApi(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)
        storage.save("businesses", BUSINESS["id"], BUSINESS)
        storage.save("recalls", RECALL["sourceRecordId"], RECALL)
        self.client = TestClient(server.app)

    def tearDown(self):
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)

    def test_empty_state(self):
        resp = self.client.get(f"/api/state?business_id={BUSINESS['id']}")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["cases"], [])
        self.assertEqual(body["reviewQueue"], [])
        self.assertEqual(body["metrics"]["recallsChecked"], 0)

    def test_state_includes_matches_and_review_queue(self):
        match_id = "m-1"
        storage.save(
            f"businesses/{BUSINESS['id']}/matches",
            match_id,
            {
                "recallId": RECALL["sourceRecordId"],
                "invoiceLineRef": {"rawText": "some item", "supplier": "Acme"},
                "confidenceScore": 55,
                "reasoning": "unsure",
                "status": "pending_review",
            },
        )
        storage.save(
            f"businesses/{BUSINESS['id']}/review_queue",
            match_id,
            {"matchId": match_id, "reasonForFlag": "unsure", "reviewerDecision": None, "decidedAt": None},
        )

        resp = self.client.get(f"/api/state?business_id={BUSINESS['id']}")
        body = resp.json()
        self.assertEqual(len(body["cases"]), 1)
        self.assertEqual(len(body["reviewQueue"]), 1)
        self.assertEqual(body["reviewQueue"][0]["match"]["confidenceScore"], 55)

    def test_confirm_runs_action_agent_and_clears_queue(self):
        match_id = "m-2"
        storage.save(
            f"businesses/{BUSINESS['id']}/matches",
            match_id,
            {
                "recallId": RECALL["sourceRecordId"],
                "invoiceLineRef": {"rawText": "some item", "supplier": "Acme"},
                "confidenceScore": 55,
                "reasoning": "unsure",
                "status": "pending_review",
            },
        )
        storage.save(
            f"businesses/{BUSINESS['id']}/review_queue",
            match_id,
            {"matchId": match_id, "reasonForFlag": "unsure", "reviewerDecision": None, "decidedAt": None},
        )

        resp = self.client.post(f"/api/review/{match_id}/confirm?business_id={BUSINESS['id']}")
        self.assertEqual(resp.status_code, 200)

        state = self.client.get(f"/api/state?business_id={BUSINESS['id']}").json()
        self.assertEqual(len(state["reviewQueue"]), 0)  # resolved, no longer pending

        compliance = storage.get(f"businesses/{BUSINESS['id']}/compliance_log", match_id)
        self.assertIsNotNone(compliance)  # Action Agent actually ran

    def test_reject_unknown_match_returns_404(self):
        resp = self.client.post(f"/api/review/does-not-exist/reject?business_id={BUSINESS['id']}")
        self.assertEqual(resp.status_code, 404)

    def test_radar_includes_matches_and_review_but_not_rejected(self):
        recall_multi_state = {**RECALL, "sourceRecordId": "R-2", "distributionStates": ["MD", "VA"]}
        storage.save("recalls", "R-2", recall_multi_state)
        storage.save(
            f"businesses/{BUSINESS['id']}/matches",
            "m-auto",
            {"recallId": "R-2", "invoiceLineRef": {"rawText": "x"}, "confidenceScore": 90, "reasoning": "r", "status": "auto_actioned", "createdAt": "2026-08-23T00:00:00+00:00"},
        )
        storage.save(
            f"businesses/{BUSINESS['id']}/matches",
            "m-rejected",
            {"recallId": "R-2", "invoiceLineRef": {"rawText": "y"}, "confidenceScore": 5, "reasoning": "no", "status": "rejected"},
        )
        state = self.client.get(f"/api/state?business_id={BUSINESS['id']}").json()
        self.assertEqual(len(state["radar"]), 2)  # MD + VA from the one auto_actioned case, none from rejected
        self.assertTrue(all(p["type"] == "match" for p in state["radar"]))

    def test_streak_zero_when_match_today(self):
        storage.save(
            f"businesses/{BUSINESS['id']}/matches",
            "m-today",
            {
                "recallId": RECALL["sourceRecordId"],
                "invoiceLineRef": {"rawText": "x"},
                "confidenceScore": 90,
                "reasoning": "r",
                "status": "auto_actioned",
                "createdAt": server.datetime.now(server.timezone.utc).isoformat(),
            },
        )
        state = self.client.get(f"/api/state?business_id={BUSINESS['id']}").json()
        self.assertEqual(state["streakDays"], 0)

    def test_streak_falls_back_to_registration_date_with_no_matches(self):
        storage.save("businesses", BUSINESS["id"], {**BUSINESS, "registeredAt": "2020-01-01T00:00:00+00:00"})
        state = self.client.get(f"/api/state?business_id={BUSINESS['id']}").json()
        self.assertGreater(state["streakDays"], 365)


if __name__ == "__main__":
    unittest.main()
