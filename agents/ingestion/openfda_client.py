"""openFDA food enforcement client.

Known gotchas (see docs/PLAN.md section 1, verified against live responses 2026-08-22):
- Exact-match field values must be quoted: classification:"Class I", not unquoted.
- Aggregating/counting a text field needs the `.exact` suffix (not used yet here — no
  aggregation queries in the MVP, just fetch-and-normalize).
- report_date ranges before 2012-06-20 404 on all three enforcement endpoints even
  though the docs claim 2004+ coverage.
- Pagination is capped around skip+limit ~= 25000; for the MVP's incremental polling
  (new records since a cursor) this is never approached, so plain skip-based pagination
  is used rather than date-window bisection. Revisit only if a large historical backfill
  is ever needed (e.g. well beyond the N=30 experiment set in docs/EXPERIMENT.md).
"""
import time

import requests

BASE_URL = "https://api.fda.gov/food/enforcement.json"
MIN_REPORT_DATE = "2012-06-20"
PAGE_LIMIT = 100
MAX_RESULTS = 5000  # safety cap well under the ~25k pagination ceiling


def fetch_since(report_date_from: str, report_date_to: str | None = None) -> list[dict]:
    """report_date_from/to: "YYYY-MM-DD". Returns raw openFDA result dicts (call
    normalize.normalize_openfda on each before storing)."""
    if report_date_from < MIN_REPORT_DATE:
        raise ValueError(
            f"report_date_from {report_date_from} is before {MIN_REPORT_DATE} — "
            "openFDA 404s on enforcement queries before this date regardless of docs."
        )
    to_date = (report_date_to or _today()).replace("-", "")
    from_date = report_date_from.replace("-", "")
    search = f'report_date:[{from_date}+TO+{to_date}]'

    results: list[dict] = []
    skip = 0
    while skip < MAX_RESULTS:
        # Built as a raw query string, not passed via params= — requests would otherwise
        # percent-encode the literal "+" in "TO+" into "%2B", breaking openFDA's
        # Lucene-style date-range syntax (confirmed: this caused a 500 from the API).
        url = f"{BASE_URL}?search={search}&limit={PAGE_LIMIT}&skip={skip}"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 404:
            # openFDA 404s when a query matches zero results, not just on bad dates.
            break
        resp.raise_for_status()
        page = resp.json().get("results", [])
        if not page:
            break
        results.extend(page)
        if len(page) < PAGE_LIMIT:
            break
        skip += PAGE_LIMIT
        time.sleep(0.2)  # light self-throttle, openFDA has no documented key requirement here
    return results


def fetch_by_recall_number(recall_number: str) -> dict | None:
    """Looks up one specific recall by its exact recall_number. Used by tests (pinning
    against a known record is more reliable than guessing a date window) and useful
    generally for re-checking a specific recall later."""
    url = f'{BASE_URL}?search=recall_number:"{recall_number}"&limit=1'
    resp = requests.get(url, timeout=30)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None


def _today() -> str:
    return time.strftime("%Y-%m-%d")
