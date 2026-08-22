"""Renders the compliance record as a PDF — deliberately plain and serious, no Scout
branding, per the brand guide's own rule: this is the one document a health inspector
actually reads, and it needs to look like it, not like a mascot product.

All external/untrusted text (recall descriptions, invoice line text, match reasoning —
all ultimately sourced from outside this codebase) is escaped via `xml.sax.saxutils.escape`
before being handed to reportlab's Paragraph, which interprets a subset of markup tags in
its input. Un-escaped text here could break rendering or inject unintended formatting —
see the security note at the top of action_agent.py.
"""
from pathlib import Path
from xml.sax.saxutils import escape as _escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

STYLES = getSampleStyleSheet()
TITLE_STYLE = ParagraphStyle("ComplianceTitle", parent=STYLES["Title"], fontSize=16)
LABEL_STYLE = ParagraphStyle("Label", parent=STYLES["Normal"], fontName="Helvetica-Bold")
BODY_STYLE = STYLES["Normal"]


def write_compliance_pdf(record: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=LETTER)

    story = [
        Paragraph("RecallGuard Compliance Record", TITLE_STYLE),
        Spacer(1, 0.15 * inch),
        _field("Detected at", record.get("detectedAt", "")),
        _field("Business ID", record.get("businessId", "")),
        _field("Recall source", f"{record.get('recallSource', '')} #{record.get('recallId', '')}"),
        _field("Invoice line item", record.get("invoiceLine", "")),
        _field("Invoice supplier", record.get("invoiceSupplier", "")),
        _field("Match confidence", f"{record.get('matchConfidence', '')}%"),
        Spacer(1, 0.1 * inch),
        Paragraph("Matching reasoning", LABEL_STYLE),
        Paragraph(_escape(str(record.get("matchReasoning", ""))), BODY_STYLE),
        Spacer(1, 0.15 * inch),
        Paragraph("Actions taken", LABEL_STYLE),
        Paragraph(_escape(", ".join(record.get("actionsTaken", []))), BODY_STYLE),
        Spacer(1, 0.2 * inch),
    ]

    checklist = record.get("checklist")
    if checklist:
        story.append(Paragraph("Pull checklist", LABEL_STYLE))
        story.append(Spacer(1, 0.05 * inch))
        rows = [["Field", "Value"]]
        for key in ("item", "supplier", "quantity", "storageHint", "lotCode", "recallSource", "recallId"):
            value = checklist.get(key, "")
            rows.append([key, _escape(str(value))])
        table = Table(rows, colWidths=[1.5 * inch, 4.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B2E33")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(table)

    doc.build(story)
    return output_path


def _field(label: str, value: str) -> Paragraph:
    return Paragraph(f"<b>{_escape(label)}:</b> {_escape(str(value))}", BODY_STYLE)
