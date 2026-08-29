"""API tests for the dashboard backend, using FastAPI's TestClient (no live server, no
network, no Gemini calls) against a temporary storage directory — never touches real
agents/local_data/.

Run: python -m unittest test_server -v
"""
import shutil
import sys
import unittest
from pathlib import Path
from unittest import mock

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

        # Regression: confirm used to pass a bare {"id": business_id} stub into the
        # Action Agent, producing a blank "From: Business ()" on every draft generated
        # via a human confirmation — found by reading a live draft's actual text, not
        # by re-reading this code. The real business name must appear.
        self.assertIn(BUSINESS["name"], compliance["notificationDrafts"]["healthDeptDraft"])

        # The whole point of this endpoint: prove the PDF that was just generated is
        # actually retrievable afterward, via a separate request — not just that
        # generation succeeded (see docs/PROGRESS.md, 2026-08-27, for why this
        # specific gap went uncaught: those are two different claims).
        pdf_resp = self.client.get(f"/api/compliance/{match_id}/pdf?business_id={BUSINESS['id']}")
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp.headers["content-type"], "application/pdf")
        self.assertTrue(pdf_resp.content.startswith(b"%PDF"))

    def test_notification_drafts_endpoint_returns_real_text(self):
        match_id = "m-drafts-test"
        storage.save(
            f"businesses/{BUSINESS['id']}/matches",
            match_id,
            {
                "recallId": RECALL["sourceRecordId"],
                "invoiceLineRef": {"rawText": "some item", "supplier": "Acme"},
                "confidenceScore": 55, "reasoning": "unsure", "status": "pending_review",
            },
        )
        storage.save(
            f"businesses/{BUSINESS['id']}/review_queue", match_id,
            {"matchId": match_id, "reasonForFlag": "unsure", "reviewerDecision": None, "decidedAt": None},
        )
        self.client.post(f"/api/review/{match_id}/confirm?business_id={BUSINESS['id']}")

        resp = self.client.get(f"/api/compliance/{match_id}/drafts?business_id={BUSINESS['id']}")
        self.assertEqual(resp.status_code, 200)
        text = resp.text
        self.assertIn("SUPPLIER DRAFT", text)
        self.assertIn("HEALTH DEPARTMENT DRAFT", text)
        self.assertIn("DRAFT — NOT SENT", text)  # the actual draft content made it through

    def test_notification_drafts_404_for_unknown_match(self):
        resp = self.client.get(f"/api/compliance/does-not-exist/drafts?business_id={BUSINESS['id']}")
        self.assertEqual(resp.status_code, 404)

    def test_compliance_pdf_404_for_unknown_match(self):
        resp = self.client.get(f"/api/compliance/does-not-exist/pdf?business_id={BUSINESS['id']}")
        self.assertEqual(resp.status_code, 404)

    def test_compliance_pdf_served_from_gcs_in_cloud_mode(self):
        match_id = "m-gcs-test"
        storage.save(
            f"businesses/{BUSINESS['id']}/compliance_log",
            match_id,
            {"pdfStoragePath": "businesses/biz-1/compliance/m-gcs-test.pdf"},
        )
        fake_blob = mock.MagicMock()
        fake_blob.download_as_bytes.return_value = b"%PDF-fake-content"
        fake_bucket = mock.MagicMock()
        fake_bucket.blob.return_value = fake_blob
        fake_client = mock.MagicMock()
        fake_client.bucket.return_value = fake_bucket

        with mock.patch("google.cloud.storage.Client", return_value=fake_client):
            resp = self.client.get(f"/api/compliance/{match_id}/pdf?business_id={BUSINESS['id']}")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"%PDF-fake-content")
        fake_bucket.blob.assert_called_once_with("businesses/biz-1/compliance/m-gcs-test.pdf")

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

    # --- Invoices ---

    def test_upload_csv_creates_grouped_invoice(self):
        csv_bytes = b"description,qty,unit,date\nChicken Breast,2,case,2026-08-01\nGround Beef,1,case,2026-08-01\n"
        resp = self.client.post(
            "/api/invoices/upload",
            files={"file": ("delivery.csv", csv_bytes, "text/csv")},
            data={"business_id": BUSINESS["id"]},
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["sourceType"], "csv")
        self.assertEqual(len(body["rawLineItems"]), 2)
        self.assertTrue(all("lineId" in line for line in body["rawLineItems"]))

    def test_upload_csv_without_explicit_supplier_uses_uploaded_filename_not_temp_path(self):
        # Regression test: the endpoint writes the upload to a server-generated
        # tempfile before parsing (NamedTemporaryFile), and csv_parser's own internal
        # fallback derives an unnamed CSV's "supplier" from whatever path it's handed.
        # Passing that tempfile path straight through produced garbage like
        # "tmpjtql5bqw" instead of anything derived from what was actually uploaded —
        # found live, 2026-08-30, while seeding a demo case for the submission video.
        csv_bytes = b"description,qty,unit,date\nItem A,1,case,2026-08-01\n"
        resp = self.client.post(
            "/api/invoices/upload",
            files={"file": ("restaurant_depot_005_ambiguous.csv", csv_bytes, "text/csv")},
            data={"business_id": BUSINESS["id"]},
        )
        body = resp.json()
        self.assertEqual(body["supplier"], "restaurant_depot_005_ambiguous")
        self.assertTrue(all(line["supplier"] == "restaurant_depot_005_ambiguous" for line in body["rawLineItems"]))
        self.assertNotIn("tmp", body["supplier"].lower())

    def test_upload_image_calls_parser_exactly_once(self):
        fake_lines = [{
            "rawText": "Test Item", "supplier": "Acme", "quantity": "1", "unit": "case",
            "dateReceived": "2026-08-01", "parsedProduct": None, "parsedLot": None,
        }]
        with mock.patch.object(server.image_parser, "parse_image", return_value=fake_lines) as mocked:
            resp = self.client.post(
                "/api/invoices/upload",
                files={"file": ("photo.jpg", b"fake-image-bytes", "image/jpeg")},
                data={"business_id": BUSINESS["id"]},
            )
        self.assertEqual(resp.status_code, 200)
        mocked.assert_called_once()  # never call Gemini more than once per upload

    def test_upload_rejects_unsupported_extension(self):
        resp = self.client.post(
            "/api/invoices/upload",
            files={"file": ("invoice.pdf", b"whatever", "application/pdf")},
            data={"business_id": BUSINESS["id"]},
        )
        self.assertEqual(resp.status_code, 400)

    def test_upload_empty_csv_returns_422(self):
        resp = self.client.post(
            "/api/invoices/upload",
            files={"file": ("empty.csv", b"description,qty,unit,date\n", "text/csv")},
            data={"business_id": BUSINESS["id"]},
        )
        self.assertEqual(resp.status_code, 422)

    def test_list_invoices_reflects_reconciliation_counts(self):
        upload = self.client.post(
            "/api/invoices/upload",
            files={"file": ("supplierx.csv", b"description,qty,unit,date\nItem A,1,case,2026-08-01\n", "text/csv")},
            data={"business_id": BUSINESS["id"]},
        ).json()
        storage.save(
            f"businesses/{BUSINESS['id']}/matches", "m-inv-1",
            {
                "recallId": RECALL["sourceRecordId"],
                "invoiceLineRef": {**upload["rawLineItems"][0], "invoiceId": upload["_id"]},
                "confidenceScore": 90, "reasoning": "x", "status": "auto_actioned",
                "createdAt": "2026-08-01T00:00:00Z",
            },
        )

        resp = self.client.get(f"/api/invoices?business_id={BUSINESS['id']}")
        self.assertEqual(resp.status_code, 200)
        invoices = resp.json()
        self.assertEqual(len(invoices), 1)
        self.assertEqual(invoices[0]["autoActionedCount"], 1)

    def test_invoice_detail_returns_match_history(self):
        upload = self.client.post(
            "/api/invoices/upload",
            files={"file": ("supplierz.csv", b"description,qty,unit,date\nItem B,1,case,2026-08-01\n", "text/csv")},
            data={"business_id": BUSINESS["id"]},
        ).json()

        resp = self.client.get(f"/api/invoices/{upload['_id']}?business_id={BUSINESS['id']}")
        self.assertEqual(resp.status_code, 200)
        detail = resp.json()
        self.assertEqual(len(detail["lines"]), 1)
        self.assertEqual(detail["lines"][0]["matchHistory"], [])

    def test_invoice_detail_404_for_unknown_id(self):
        resp = self.client.get(f"/api/invoices/does-not-exist?business_id={BUSINESS['id']}")
        self.assertEqual(resp.status_code, 404)

    def test_search_filter_narrows_results(self):
        csv_bytes = b"description,qty,unit,date\nItem,1,case,2026-08-01\n"
        self.client.post("/api/invoices/upload", files={"file": ("sysco_order.csv", csv_bytes, "text/csv")}, data={"business_id": BUSINESS["id"]})
        self.client.post("/api/invoices/upload", files={"file": ("usfoods_order.csv", csv_bytes, "text/csv")}, data={"business_id": BUSINESS["id"]})

        resp = self.client.get(f"/api/invoices?business_id={BUSINESS['id']}&q=sysco")
        invoices = resp.json()
        self.assertEqual(len(invoices), 1)
        self.assertIn("sysco", invoices[0]["sourceFileName"].lower())

    def test_delete_invoice_then_404s(self):
        upload = self.client.post(
            "/api/invoices/upload",
            files={"file": ("todelete.csv", b"description,qty,unit,date\nItem,1,case,2026-08-01\n", "text/csv")},
            data={"business_id": BUSINESS["id"]},
        ).json()

        resp = self.client.delete(f"/api/invoices/{upload['_id']}?business_id={BUSINESS['id']}")
        self.assertEqual(resp.status_code, 200)

        resp2 = self.client.get(f"/api/invoices/{upload['_id']}?business_id={BUSINESS['id']}")
        self.assertEqual(resp2.status_code, 404)

    def test_delete_unknown_invoice_returns_404(self):
        resp = self.client.delete(f"/api/invoices/does-not-exist?business_id={BUSINESS['id']}")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
