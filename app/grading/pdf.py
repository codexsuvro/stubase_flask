
from io import BytesIO
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def safe_text(value):
    """Escape dynamic text before passing it to ReportLab Paragraph."""
    if value is None:
        return ""

    return escape(str(value))


def generate_transcript_pdf(transcript):
    """
    Generate an academic transcript PDF in memory.

    Args:
        transcript (dict): Data returned by
            grading.service.get_student_transcript().

    Returns:
        BytesIO: Generated PDF file stream.
    """

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Academic Transcript",
        author="StuBase Management System",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TranscriptTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1F2937"),
        spaceAfter=5 * mm,
    )

    subtitle_style = ParagraphStyle(
        "TranscriptSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=8 * mm,
    )

    section_style = ParagraphStyle(
        "TranscriptSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1F2937"),
        spaceBefore=5 * mm,
        spaceAfter=3 * mm,
    )

    normal_style = ParagraphStyle(
        "TranscriptNormal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#374151"),
    )

    header_style = ParagraphStyle(
        "TranscriptTableHeader",
        parent=normal_style,
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        textColor=colors.white,
        alignment=TA_LEFT,
    )

    cell_style = ParagraphStyle(
        "TranscriptTableCell",
        parent=normal_style,
        fontSize=7,
        leading=10,
        wordWrap="CJK",
    )

    story = []

    # --------------------------------------------------
    # Document heading
    # --------------------------------------------------

    story.append(
        Paragraph(
            "ACADEMIC TRANSCRIPT",
            title_style,
        )
    )

    generated_at = datetime.now(
        timezone.utc
    ).strftime("%d %B %Y, %H:%M UTC")

    story.append(
        Paragraph(
            f"Generated on {generated_at}",
            subtitle_style,
        )
    )

    # --------------------------------------------------
    # Student information
    # --------------------------------------------------

    story.append(
        Paragraph(
            "STUDENT INFORMATION",
            section_style,
        )
    )

    student_data = [
        [
            Paragraph("<b>Student Name</b>", cell_style),
            Paragraph(
                safe_text(transcript["student_name"]),
                cell_style,
            ),
        ],
        [
            Paragraph("<b>Student ID</b>", cell_style),
            Paragraph(
                safe_text(transcript["student_id"]),
                cell_style,
            ),
        ],
    ]

    student_table = Table(
        student_data,
        colWidths=[45 * mm, 125 * mm],
    )

    student_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#F3F4F6"),
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#D1D5DB"),
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.3,
                colors.HexColor("#D1D5DB"),
            ),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])
    )

    story.append(student_table)

    # --------------------------------------------------
    # Academic summary
    # --------------------------------------------------

    story.append(
        Paragraph(
            "ACADEMIC SUMMARY",
            section_style,
        )
    )

    summary_data = [
        [
            Paragraph("<b>Total Credits</b>", cell_style),
            Paragraph("<b>Earned Credits</b>", cell_style),
            Paragraph("<b>CGPA</b>", cell_style),
        ],
        [
            safe_text(transcript["total_credits"]),
            safe_text(transcript["earned_credits"]),
            safe_text(transcript["cgpa"]),
        ],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[56.67 * mm] * 3,
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#F3F4F6"),
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, 1),
                colors.white,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#D1D5DB"),
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.3,
                colors.HexColor("#D1D5DB"),
            ),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    story.append(summary_table)

    # --------------------------------------------------
    # Course-wise academic record
    # --------------------------------------------------

    story.append(
        Paragraph(
            "COURSE-WISE ACADEMIC RECORD",
            section_style,
        )
    )

    course_headers = [
        "Course Code",
        "Course Name",
        "Credits",
        "Year",
        "Semester",
        "Percentage",
        "Grade",
        "Result",
    ]

    course_data = [
        [
            Paragraph(header, header_style)
            for header in course_headers
        ]
    ]

    for course in transcript["courses"]:
        course_data.append([
            Paragraph(
                safe_text(course["course_code"]),
                cell_style,
            ),
            Paragraph(
                safe_text(course["course_name"]),
                cell_style,
            ),
            safe_text(course["credits"]),
            Paragraph(
                safe_text(course["academic_year"]),
                cell_style,
            ),
            safe_text(course["semester"]),
            safe_text(course["percentage"]),
            safe_text(course["letter_grade"]),
            safe_text(course["result_status"]),
        ])

    if not transcript["courses"]:
        course_data.append([
            Paragraph(
                "No published course grades available.",
                cell_style,
            ),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ])

    course_table = Table(
        course_data,
        colWidths=[
            21 * mm,
            38 * mm,
            13 * mm,
            22 * mm,
            15 * mm,
            22 * mm,
            15 * mm,
            18 * mm,
        ],
        repeatRows=1,
    )

    course_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1F2937"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#D1D5DB"),
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.3,
                colors.HexColor("#D1D5DB"),
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.HexColor("#F9FAFB"),
                ],
            ),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (2, 1), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ])
    )

    story.append(course_table)

    # --------------------------------------------------
    # Footer
    # --------------------------------------------------

    story.append(Spacer(1, 10 * mm))

    footer_style = ParagraphStyle(
        "TranscriptFooter",
        parent=normal_style,
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6B7280"),
    )

    story.append(
        Paragraph(
            "This document contains academic records "
            "published in the StuBase Management System.",
            footer_style,
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer
