"""Offline tests for the billing-guard decision logic.

Deploying this to a real Cloud Function is a slow, real-billing-account-touching
operation. Before doing that, this proves the actual decision logic — the part
that could have a bug — behaves correctly: it must disable billing when (and
only when) reported cost has reached the budget, and must never call the
disable API when it doesn't need to (idempotent on an already-disabled
project, and refuses to act if the budget amount itself is missing/zero
rather than guessing).

`functions_framework` and `google-cloud-billing` aren't installed locally (they
belong to the Cloud Functions runtime), so both are faked here with the
minimum surface `main.py` actually calls, injected into `sys.modules` before
import. This tests our logic, not Google's SDKs.
"""

import base64
import json
import os
import sys
import types
import unittest
from unittest.mock import MagicMock

os.environ["GCP_PROJECT_ID"] = "test-project"

fake_functions_framework = types.ModuleType("functions_framework")
fake_functions_framework.cloud_event = lambda fn: fn
sys.modules["functions_framework"] = fake_functions_framework

fake_google = types.ModuleType("google")
fake_google_cloud = types.ModuleType("google.cloud")
fake_billing_v1 = types.ModuleType("google.cloud.billing_v1")


class _FakeProjectBillingInfo:
    def __init__(self, billing_account_name=""):
        self.billing_account_name = billing_account_name


fake_billing_v1.ProjectBillingInfo = _FakeProjectBillingInfo
fake_billing_v1.CloudBillingClient = MagicMock  # replaced per-test via patch
fake_google_cloud.billing_v1 = fake_billing_v1
sys.modules["google"] = fake_google
sys.modules["google.cloud"] = fake_google_cloud
sys.modules["google.cloud.billing_v1"] = fake_billing_v1

sys.path.insert(0, os.path.dirname(__file__))
import main  # noqa: E402


def make_event(cost_amount, budget_amount, budget_name="test-budget"):
    payload = {
        "budgetDisplayName": budget_name,
        "costAmount": cost_amount,
        "budgetAmount": budget_amount,
    }
    encoded = base64.b64encode(json.dumps(payload).encode()).decode()
    return types.SimpleNamespace(data={"message": {"data": encoded}})


class TestBillingGuard(unittest.TestCase):
    def _make_client(self, billing_enabled=True):
        client = MagicMock()
        client.get_project_billing_info.return_value = types.SimpleNamespace(
            billing_enabled=billing_enabled
        )
        return client

    def test_under_budget_does_nothing(self):
        client = self._make_client(billing_enabled=True)
        main.billing_v1.CloudBillingClient = MagicMock(return_value=client)

        main.disable_billing_on_budget_exceeded(make_event(cost_amount=0.4, budget_amount=1.0))

        client.update_project_billing_info.assert_not_called()

    def test_cost_equal_to_budget_disables_billing(self):
        client = self._make_client(billing_enabled=True)
        main.billing_v1.CloudBillingClient = MagicMock(return_value=client)

        main.disable_billing_on_budget_exceeded(make_event(cost_amount=1.0, budget_amount=1.0))

        client.update_project_billing_info.assert_called_once()
        _, kwargs = client.update_project_billing_info.call_args
        self.assertEqual(kwargs["name"], "projects/test-project")
        self.assertEqual(kwargs["project_billing_info"].billing_account_name, "")

    def test_cost_over_budget_disables_billing(self):
        client = self._make_client(billing_enabled=True)
        main.billing_v1.CloudBillingClient = MagicMock(return_value=client)

        main.disable_billing_on_budget_exceeded(make_event(cost_amount=999, budget_amount=1.0))

        client.update_project_billing_info.assert_called_once()

    def test_already_disabled_is_idempotent(self):
        client = self._make_client(billing_enabled=False)
        main.billing_v1.CloudBillingClient = MagicMock(return_value=client)

        main.disable_billing_on_budget_exceeded(make_event(cost_amount=999, budget_amount=1.0))

        client.update_project_billing_info.assert_not_called()

    def test_missing_budget_amount_refuses_to_act(self):
        client = self._make_client(billing_enabled=True)
        main.billing_v1.CloudBillingClient = MagicMock(return_value=client)

        main.disable_billing_on_budget_exceeded(make_event(cost_amount=999, budget_amount=0))

        client.get_project_billing_info.assert_not_called()
        client.update_project_billing_info.assert_not_called()


if __name__ == "__main__":
    unittest.main()
