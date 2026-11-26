from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _safe_text(value):
    return escape(str(value)) if value is not None else ""


def generate_payment_receipt_pdf(payment):
    invoice = payment.invoice
    student = invoice.student
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
        title=f"Payment receipt {_safe_text(payment.receipt_number)}",
        author="StuBase Management System",
    )
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        "ReceiptNormal",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#374151"),
    )
    title_style = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Title"],
        alignment=TA_LEFT,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=6 * mm,
    )
    amount_style = ParagraphStyle(
        "ReceiptAmount",
        parent=normal_style,
        alignment=TA_RIGHT,
        fontName="Helvetica-Bold",
    )
    story = [
        Paragraph("PAYMENT RECEIPT", title_style),
        Paragraph(
            "<b>Receipt number:</b> "
            f"{_safe_text(payment.receipt_number)}",
            normal_style,
        ),
        Paragraph(
            f"<b>Invoice number:</b> {_safe_text(invoice.invoice_number)}",
            normal_style,
        ),
        Paragraph(
            f"<b>Student:</b> {_safe_text(student.first_name)} "
            f"{_safe_text(student.last_name)} "
            f"({_safe_text(student.student_id)})",
            normal_style,
        ),
        Spacer(1, 7 * mm),
    ]
    rows = [
        [
            Paragraph("Payment received", normal_style),
            Paragraph(
                f"{invoice.currency_code} {payment.amount:.2f}",
                amount_style,
            ),
        ],
        [
            Paragraph("Payment method", normal_style),
            Paragraph(_safe_text(payment.payment_method), amount_style),
        ],
        [
            Paragraph("Reference", normal_style),
            Paragraph(
                _safe_text(payment.payment_reference or "Not provided"),
                amount_style,
            ),
        ],
        [
            Paragraph("Date received", normal_style),
            Paragraph(
                payment.received_at.strftime("%Y-%m-%d %H:%M UTC"),
                amount_style,
            ),
        ],
        [
            Paragraph("Total paid on invoice", normal_style),
            Paragraph(
                f"{invoice.currency_code} "
                f"{payment.amount_paid_after:.2f}",
                amount_style,
            ),
        ],
        [
            Paragraph("Invoice balance after payment", normal_style),
            Paragraph(
                f"{invoice.currency_code} {payment.balance_after:.2f}",
                amount_style,
            ),
        ],
    ]
    table = Table(rows, colWidths=[90 * mm, 70 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1D5DB")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([
        table,
        Spacer(1, 8 * mm),
        Paragraph(
            "This receipt acknowledges payment received. "
            "Keep it with your invoice records.",
            normal_style,
        ),
    ])
    document.build(story)
    buffer.seek(0)
    return buffer
