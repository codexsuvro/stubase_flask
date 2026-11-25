from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _safe_text(value):
    return escape(str(value)) if value is not None else ""


def generate_invoice_pdf(invoice):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Invoice {_safe_text(invoice.invoice_number)}",
        author="StuBase Management System",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Title"],
        textColor=colors.HexColor("#1F2937"),
        alignment=TA_LEFT,
        spaceAfter=5 * mm,
    )
    normal_style = ParagraphStyle(
        "InvoiceNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#374151"),
    )
    right_style = ParagraphStyle(
        "InvoiceAmount",
        parent=normal_style,
        alignment=TA_RIGHT,
    )
    header_style = ParagraphStyle(
        "InvoiceTableHeader",
        parent=normal_style,
        fontName="Helvetica-Bold",
        fontSize=8,
        textColor=colors.white,
    )
    story = [
        Paragraph("FEE INVOICE", title_style),
        Paragraph(
            f"<b>Invoice number:</b> {_safe_text(invoice.invoice_number)}",
            normal_style,
        ),
        Paragraph(
            f"<b>Status:</b> {_safe_text(invoice.status)}",
            normal_style,
        ),
        Paragraph(
            f"<b>Issued:</b> {invoice.issued_at:%Y-%m-%d}",
            normal_style,
        ),
        Paragraph(
            f"<b>Due:</b> {_safe_text(invoice.due_date or 'Not specified')}",
            normal_style,
        ),
        Spacer(1, 5 * mm),
        Paragraph(
            "<b>Bill to:</b> "
            f"{_safe_text(invoice.student.first_name)} "
            f"{_safe_text(invoice.student.last_name)} "
            f"({_safe_text(invoice.student.student_id)})",
            normal_style,
        ),
        Paragraph(
            f"<b>Academic year:</b> "
            f"{_safe_text(invoice.academic_year.name)}",
            normal_style,
        ),
        Paragraph(
            f"<b>Semester:</b> "
            f"{_safe_text(invoice.semester.semester_name)}",
            normal_style,
        ),
        Spacer(1, 7 * mm),
    ]

    rows = [[
        Paragraph("Item", header_style),
        Paragraph("Fee code", header_style),
        Paragraph("Gross", header_style),
        Paragraph("Credits", header_style),
        Paragraph("Amount due", header_style),
    ]]
    for line in invoice.lines:
        rows.append([
            Paragraph(
                f"{_safe_text(line.item_name)}"
                + (
                    f"<br/><font size='7'>"
                    f"{_safe_text(line.item_description)}</font>"
                    if line.item_description
                    else ""
                ),
                normal_style,
            ),
            Paragraph(_safe_text(line.fee_code), normal_style),
            Paragraph(
                f"{invoice.currency_code} {line.gross_amount:.2f}",
                right_style,
            ),
            Paragraph(
                f"{invoice.currency_code} {line.adjustment_amount:.2f}",
                right_style,
            ),
            Paragraph(
                f"{invoice.currency_code} {line.amount_due:.2f}",
                right_style,
            ),
        ])

    table = Table(
        rows,
        colWidths=[61 * mm, 27 * mm, 27 * mm, 27 * mm, 32 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1D5DB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            colors.HexColor("#F3F4F6"),
        ]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([
        table,
        Spacer(1, 5 * mm),
        Paragraph(
            "<b>Total due:</b> "
            f"{_safe_text(invoice.currency_code)} "
            f"{invoice.total_amount:.2f}",
            ParagraphStyle(
                "InvoiceTotal",
                parent=right_style,
                fontName="Helvetica-Bold",
                fontSize=11,
            ),
        ),
    ])
    if invoice.status == "VOID":
        story.extend([
            Spacer(1, 4 * mm),
            Paragraph(
                f"<b>VOID:</b> {_safe_text(invoice.void_reason)}",
                normal_style,
            ),
        ])
    document.build(story)
    buffer.seek(0)
    return buffer
