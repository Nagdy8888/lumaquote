from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def quotation_pdf(quote: dict, customer: dict) -> bytes:
    """Render the persisted canonical revision as a readable PDF; never recalculate prices during document generation."""
    output = BytesIO()
    styles = getSampleStyleSheet()
    content = quote["content"]
    story = [
        Paragraph("LumaQuote / Commercial lighting", styles["Title"]),
        Paragraph("Synthetic supplier records — portfolio project", styles["Normal"]),
        Spacer(1, 9 * mm),
        Paragraph(escape(f"{quote['number']} / Revision {quote['revision']}"), styles["Heading1"]),
        Paragraph(
            escape(f"Prepared for {customer['customer_name']} · {customer['customer_company']}"),
            styles["Normal"],
        ),
        Paragraph(
            escape(f"Valid until {quote['valid_until'].strftime('%d %b %Y')} · USD · Tax excluded"),
            styles["Normal"],
        ),
        Spacer(1, 7 * mm),
    ]
    rows = [["Product / SKU", "Qty", "Unit USD", "Total USD"]]
    for line in content["lines"]:
        rows.append(
            [
                Paragraph(escape(line["name"]) + "<br/>" + escape(line["sku"]), styles["Normal"]),
                str(line["quantity"]),
                line["unit_price"],
                line["line_total"],
            ]
        )
    table = Table(rows, colWidths=[91 * mm, 15 * mm, 29 * mm, 29 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#202426")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("LINEBELOW", (0, 1), (-1, -1), 0.4, colors.HexColor("#cccccc")),
            ]
        )
    )
    story.extend([table, Spacer(1, 7 * mm)])
    for label, key in [
        ("Subtotal", "subtotal"),
        ("Discount", "discount"),
        ("Shipping", "shipping"),
        ("Total USD", "total"),
    ]:
        story.append(
            Paragraph(f"{label}: {escape(content[key])}", styles["Heading3" if key == "total" else "Normal"])
        )
    story.extend(
        [
            Spacer(1, 8 * mm),
            Paragraph(escape(content["terms"]), styles["Normal"]),
            Paragraph("Availability is a snapshot. This quotation does not reserve stock.", styles["Normal"]),
        ]
    )
    SimpleDocTemplate(
        output,
        pagesize=(210 * mm, 297 * mm),
        rightMargin=23 * mm,
        leftMargin=23 * mm,
        title=quote["number"],
        author="LumaQuote",
    ).build(story)
    return output.getvalue()
