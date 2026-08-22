"""Normalizes raw FSIS and openFDA records into the source-agnostic shape defined in
docs/DATA_MODEL.md (`recalls/{recallId}`). Neither source provides clean structured lot
codes or a distribution-state array — that messiness is exactly what the Matching Agent's
reasoning step exists to handle, so we don't fake structure that isn't there."""


def normalize_openfda(record: dict) -> dict:
    return {
        "source": "openFDA",
        "sourceRecordId": record.get("recall_number", ""),
        "productDescription": record.get("product_description", ""),
        "lotCodes": [],  # not a clean field; extracted at matching time if needed
        "hazardType": record.get("reason_for_recall", ""),
        "classification": record.get("classification", ""),
        "distributionStates": _split_states(record.get("distribution_pattern", "")),
        "reportDate": record.get("report_date", ""),
        "recallInitiationDate": record.get("recall_initiation_date", ""),
        "rawSourcePayload": record,
    }


def normalize_fsis(record: dict) -> dict:
    return {
        "source": "FSIS",
        "sourceRecordId": record.get("field_recall_number", ""),
        "productDescription": record.get("field_title", ""),
        "lotCodes": [],  # embedded as free text in field_product_items, not structured
        "hazardType": record.get("field_recall_reason", ""),
        "classification": record.get("field_recall_classification", ""),
        "distributionStates": _split_states(record.get("field_states", "")),
        "reportDate": record.get("field_recall_date", ""),
        "recallInitiationDate": record.get("field_recall_date", ""),
        "rawSourcePayload": record,
    }


def _split_states(raw: str) -> list:
    """Both sources give a free-text states/distribution string, not an array. openFDA
    often prefixes it with a boilerplate sentence ("The recalled product was distributed
    to the following states: MD, VA") — strip anything before the last colon first, then
    comma-split. "Nationwide" and similar phrases are left as a single-element list
    rather than guessed at further."""
    if not raw:
        return []
    if ":" in raw:
        raw = raw.rsplit(":", 1)[-1]
    if "," in raw:
        return [s.strip() for s in raw.split(",") if s.strip()]
    return [raw.strip()] if raw.strip() else []
