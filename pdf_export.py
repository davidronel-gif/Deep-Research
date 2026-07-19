# pdf_export.py
# Renders the report's markdown into a downloadable PDF via reportlab.
# Only handles the subset of markdown report_builder actually emits
# (## headings, **bold**, [text](url) links, "- " / "N. " lines).

import io
import re

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ANCHOR_RE = re.compile(r'<a id="[^"]*"></a>')


def _inline_markup(line: str) -> str:
    """Escape XML entities, then convert the markdown our reports use into
    reportlab's paragraph markup. Internal in-page anchors (#src-N) have no
    meaning in a flattened PDF, so they render as bold text, not links."""
    text = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = _ANCHOR_RE.sub("", text)
    text = _BOLD_RE.sub(r"<b>\1</b>", text)

    def link_sub(match: re.Match) -> str:
        label, url = match.group(1), match.group(2)
        if url.startswith("#"):
            return label
        return f'<a href="{url}" color="#1a73e8">{label}</a>'

    return _LINK_RE.sub(link_sub, text)


def markdown_report_to_pdf(markdown_text: str) -> bytes:
    """Convert report_markdown into PDF bytes for download."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=LETTER,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    body = ParagraphStyle("ReportBody", parent=styles["BodyText"], spaceAfter=8, leading=15)
    bullet = ParagraphStyle("ReportBullet", parent=body, leftIndent=16, bulletIndent=4)
    h1 = ParagraphStyle("ReportH1", parent=styles["Heading1"], spaceBefore=4, spaceAfter=10)
    h2 = ParagraphStyle("ReportH2", parent=styles["Heading2"], spaceBefore=14, spaceAfter=8)

    story = [Paragraph("Deep Researcher — Report", h1), Spacer(1, 4)]

    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("## "):
            story.append(Paragraph(_inline_markup(line[3:]), h2))
        elif line.startswith("# "):
            story.append(Paragraph(_inline_markup(line[2:]), h1))
        elif line.startswith("- "):
            story.append(Paragraph(f"&bull;&nbsp; {_inline_markup(line[2:])}", bullet))
        elif re.match(r"^\d+\.\s", line):
            story.append(Paragraph(_inline_markup(line), bullet))
        else:
            story.append(Paragraph(_inline_markup(line), body))

    doc.build(story)
    return buf.getvalue()
