"""FSIS Recall API client.

No API key/auth required — confirmed against a real, working reference implementation
(github.com/justanesta/food_safety_recalls and github.com/leelesemann-sys/
food-recalls-database, both call this endpoint anonymously). This resolves the open risk
flagged in the original plan ("confirm FSIS auth requirements on Day 1, don't assume
anonymous access") — it IS anonymous.

IMPORTANT — verified separately from the app's dev sandbox (2026-08-22): this endpoint is
behind Akamai bot-management, and the sandbox's request was blocked with a 403 regardless
of User-Agent (browser UA and `curl/7.88` both failed identically) — openFDA, hit the same
way, worked fine. This looks like an IP-reputation block on the sandbox's network, not a
real auth wall — the reference repos' code (no key, just a UA header) is proof it works
from a normal network. **Needs testing from this machine and, later, from Cloud Run once
deployed** — if Cloud Run's IP range is also blocked, openFDA becomes the sole trigger
source and the risk register's existing fallback applies. See docs/RISK_REGISTER.md.

The endpoint returns the FULL current recall/alert list in one response — no documented
server-side date filtering — so filter client-side by field_recall_date.
"""
import time

import requests

BASE_URL = "https://www.fsis.usda.gov/fsis/api/recall/v/1"
TIMEOUT = 90  # the reference implementation needed this — the API can be slow
MAX_ATTEMPTS = 3


def fetch_all() -> list[dict]:
    headers = {"User-Agent": "curl/7.88", "Accept": "application/json"}
    last_error: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = requests.get(BASE_URL, headers=headers, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as err:
            last_error = err
            if attempt < MAX_ATTEMPTS:
                time.sleep(5 * attempt)
    raise RuntimeError(f"FSIS API unreachable after {MAX_ATTEMPTS} attempts: {last_error}")


def fetch_since(recall_date_from: str) -> list[dict]:
    """recall_date_from: "YYYY-MM-DD". Filters client-side on field_recall_date."""
    return [r for r in fetch_all() if r.get("field_recall_date", "") >= recall_date_from]
