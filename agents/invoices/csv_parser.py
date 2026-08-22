"""Parses a supplier invoice CSV into rawLineItems per docs/DATA_MODEL.md.

Column names vary between suppliers — confirmed by hand against the 5 formats in
agents/sample_data/invoices/ (Sysco, US Foods, a local distributor, a wholesale club, and
Restaurant Depot all use different headers for the same concepts). Rather than assume one
fixed schema, this looks up a small set of known aliases per field. If a description-like
column isn't found at all, it falls back to a full key:value dump of the row so nothing is
silently dropped — the Matching Agent's job is to reason about messy text anyway.
"""
import csv
from pathlib import Path

DESCRIPTION_KEYS = ["description", "item description", "product description", "item", "product"]
QUANTITY_KEYS = ["qty", "quantity", "qty ordered", "qty shipped", "qty cases"]
UNIT_KEYS = ["unit", "pack/size", "size", "case pack"]
DATE_KEYS = ["date delivered", "delivery date", "date received", "received", "date"]


def parse_csv(path: str, supplier: str | None = None) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        lower_map = {name.lower().strip(): name for name in fieldnames}
        desc_col = _first_match(lower_map, DESCRIPTION_KEYS)
        qty_col = _first_match(lower_map, QUANTITY_KEYS)
        unit_col = _first_match(lower_map, UNIT_KEYS)
        date_col = _first_match(lower_map, DATE_KEYS)

        for row in reader:
            raw_text = (
                row.get(desc_col, "").strip()
                if desc_col
                else ", ".join(f"{k}: {v}" for k, v in row.items())
            )
            rows.append(
                {
                    "rawText": raw_text,
                    "supplier": supplier or Path(path).stem,
                    "quantity": row.get(qty_col, "").strip() if qty_col else "",
                    "unit": row.get(unit_col, "").strip() if unit_col else "",
                    "dateReceived": row.get(date_col, "").strip() if date_col else "",
                    "parsedProduct": None,
                    "parsedLot": None,
                }
            )
    return rows


def _first_match(lower_map: dict, keys: list[str]) -> str | None:
    for key in keys:
        if key in lower_map:
            return lower_map[key]
    return None
