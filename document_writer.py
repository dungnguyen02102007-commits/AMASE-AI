"""
Writes the rewritten CV back to the original file format:
PDF, DOCX, or TXT.
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable
)


def write_cv(rewritten_text: str, output_path: str, file_format: str) -> str:
    """
    Writes the rewritten CV text to the specified format.
    Returns the final output path.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fmt = file_format.lower().lstrip(".")

    if fmt == "pdf":
        _write_pdf(rewritten_text, str(path))
    elif fmt == "docx":
        _write_docx(rewritten_text, str(path))
    elif fmt == "txt":
        _write_txt(rewritten_text, str(path))
    else:
        raise ValueError(f"Unsupported output format: {fmt}")

    return str(path)


def _write_txt(text: str, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)


def _write_docx(text: str, output_path: str) -> None:
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin    = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin   = Inches(1.0)
        section.right_margin  = Inches(1.0)

    lines = text.split("\n")

    for line in lines:
        stripped = line.strip()

        # Detect section headers (ALL CAPS or ends with colon)
        if stripped.isupper() and len(stripped) > 2:
            para = doc.add_paragraph()
            run  = para.add_run(stripped)
            run.bold          = True
            run.font.size     = Pt(12)
            run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)
            para.paragraph_format.space_before = Pt(8)
            para.paragraph_format.space_after  = Pt(2)

        # Detect bullet points
        elif stripped.startswith(("-", "*", "•")):
            para = doc.add_paragraph(style="List Bullet")
            para.add_run(stripped.lstrip("-*• "))
            para.paragraph_format.left_indent = Inches(0.25)

        # Detect name (first non-empty line assumed to be name)
        elif stripped and not doc.paragraphs:
            para = doc.add_paragraph()
            run  = para.add_run(stripped)
            run.bold          = True
            run.font.size     = Pt(18)
            para.alignment    = WD_ALIGN_PARAGRAPH.CENTER

        elif stripped == "":
            doc.add_paragraph()

        else:
            doc.add_paragraph(stripped)

    doc.save(output_path)


def _write_pdf(text: str, output_path: str) -> None:
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles    = getSampleStyleSheet()
    story     = []
    lines     = text.split("\n")
    is_first  = True

    name_style = ParagraphStyle(
        "Name",
        parent    = styles["Normal"],
        fontSize  = 20,
        fontName  = "Helvetica-Bold",
        textColor = colors.HexColor("#1A1A2E"),
        spaceAfter = 4,
        alignment = 1,   # Center
    )
    header_style = ParagraphStyle(
        "SectionHeader",
        parent    = styles["Normal"],
        fontSize  = 11,
        fontName  = "Helvetica-Bold",
        textColor = colors.HexColor("#1A1A2E"),
        spaceBefore = 10,
        spaceAfter  = 2,
    )
    body_style = ParagraphStyle(
        "Body",
        parent    = styles["Normal"],
        fontSize  = 10,
        fontName  = "Helvetica",
        textColor = colors.HexColor("#2D2D2D"),
        spaceAfter = 2,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent     = styles["Normal"],
        fontSize   = 10,
        fontName   = "Helvetica",
        leftIndent = 15,
        spaceAfter = 2,
    )

    for line in lines:
        stripped = line.strip()

        if not stripped:
            story.append(Spacer(1, 4))
            continue

        # Name (first meaningful line)
        if is_first and stripped:
            story.append(Paragraph(stripped, name_style))
            story.append(HRFlowable(width="100%", thickness=1,
                                    color=colors.HexColor("#1A1A2E")))
            story.append(Spacer(1, 6))
            is_first = False
            continue

        # Section headers
        if stripped.isupper() and len(stripped) > 2:
            story.append(Spacer(1, 6))
            story.append(Paragraph(stripped, header_style))
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.HexColor("#CCCCCC")))
            story.append(Spacer(1, 3))
            continue

        # Bullet points
        if stripped.startswith(("-", "*", "•")):
            content = stripped.lstrip("-*• ")
            story.append(Paragraph(f"&bull; {content}", bullet_style))
            continue

        # Normal body
        story.append(Paragraph(stripped, body_style))

    doc.build(story)
