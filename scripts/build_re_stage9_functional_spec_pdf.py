"""Render the RE9 functional specification to a verified Korean PDF.

The user explicitly excluded screenshot image analysis, so this builder performs
text, page, font-resource, and required-section verification without rendering
pages to bitmap images.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_ROOT / "reports/re_stage9/functional_spec.md"
OUTPUT = PROJECT_ROOT / "output/pdf/RE9_기능명세서.pdf"
REGULAR_FONT = Path("C:/Windows/Fonts/malgun.ttf")
BOLD_FONT = Path("C:/Windows/Fonts/malgunbd.ttf")


def inline_markup(value: str) -> str:
    escaped = html.escape(value.strip())
    escaped = re.sub(r"`([^`]+)`", r'<font name="MalgunGothic">\1</font>', escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    return escaped


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "KTitle",
            parent=base["Title"],
            fontName="MalgunGothicBold",
            fontSize=23,
            leading=32,
            textColor=colors.HexColor("#17385D"),
            alignment=TA_LEFT,
            spaceAfter=16,
        ),
        "h2": ParagraphStyle(
            "KH2",
            parent=base["Heading2"],
            fontName="MalgunGothicBold",
            fontSize=14,
            leading=21,
            textColor=colors.HexColor("#17385D"),
            spaceBefore=12,
            spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "KH3",
            parent=base["Heading3"],
            fontName="MalgunGothicBold",
            fontSize=11,
            leading=17,
            textColor=colors.HexColor("#265A88"),
            spaceBefore=9,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "KBody",
            parent=base["BodyText"],
            fontName="MalgunGothic",
            fontSize=9.2,
            leading=15,
            textColor=colors.HexColor("#263748"),
            spaceAfter=6,
            wordWrap="CJK",
        ),
        "small": ParagraphStyle(
            "KSmall",
            parent=base["BodyText"],
            fontName="MalgunGothic",
            fontSize=7.5,
            leading=11,
            textColor=colors.HexColor("#263748"),
            wordWrap="CJK",
        ),
        "footer": ParagraphStyle(
            "KFooter",
            parent=base["BodyText"],
            fontName="MalgunGothic",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#65788A"),
            alignment=TA_CENTER,
        ),
    }


def parse_table(lines: list[str], style: ParagraphStyle):
    raw_rows = []
    for line in lines:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        raw_rows.append(cells)
    columns = max(len(row) for row in raw_rows)
    rows = [
        [Paragraph(inline_markup(cell), style) for cell in row + [""] * (columns - len(row))]
        for row in raw_rows
    ]
    available = A4[0] - 36 * mm
    if columns == 2:
        widths = [available * 0.30, available * 0.70]
    elif columns == 3:
        widths = [available * 0.24, available * 0.20, available * 0.56]
    elif columns == 4:
        widths = [available * 0.16, available * 0.22, available * 0.24, available * 0.38]
    else:
        widths = [available / columns] * columns
    table = LongTable(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF1F7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17385D")),
                ("FONTNAME", (0, 0), (-1, 0), "MalgunGothicBold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B9C7D4")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FAFC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def build_story(markdown: str, style_map: dict[str, ParagraphStyle]):
    story = []
    lines = markdown.splitlines()
    index = 0
    first_title = True
    while index < len(lines):
        line = lines[index].rstrip()
        if not line:
            story.append(Spacer(1, 2.5 * mm))
            index += 1
            continue
        if line.startswith("|"):
            table_lines = []
            while index < len(lines) and lines[index].lstrip().startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.append(parse_table(table_lines, style_map["small"]))
            story.append(Spacer(1, 3 * mm))
            continue
        if line.startswith("# "):
            if not first_title:
                story.append(PageBreak())
            story.append(Paragraph(inline_markup(line[2:]), style_map["title"]))
            story.append(
                Paragraph(
                    "RE Stage 9 · 구현 기준일 2026-08-17 · 로컬 제출준비본",
                    style_map["small"],
                )
            )
            story.append(Spacer(1, 5 * mm))
            first_title = False
        elif line.startswith("## "):
            story.append(Paragraph(inline_markup(line[3:]), style_map["h2"]))
        elif line.startswith("### "):
            story.append(Paragraph(inline_markup(line[4:]), style_map["h3"]))
        elif re.match(r"^\d+\. ", line):
            items = []
            while index < len(lines) and re.match(r"^\d+\. ", lines[index]):
                items.append(
                    ListItem(
                        Paragraph(
                            inline_markup(re.sub(r"^\d+\. ", "", lines[index])),
                            style_map["body"],
                        ),
                        leftIndent=7 * mm,
                    )
                )
                index += 1
            story.append(ListFlowable(items, bulletType="1", leftIndent=5 * mm))
            continue
        elif line.startswith("- "):
            items = []
            while index < len(lines) and lines[index].startswith("- "):
                items.append(
                    ListItem(
                        Paragraph(inline_markup(lines[index][2:]), style_map["body"]),
                        leftIndent=7 * mm,
                    )
                )
                index += 1
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=5 * mm))
            continue
        else:
            story.append(Paragraph(inline_markup(line), style_map["body"]))
        index += 1
    return story


def page_frame(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D5DEE7"))
    canvas.line(18 * mm, 15 * mm, A4[0] - 18 * mm, 15 * mm)
    canvas.setFont("MalgunGothic", 7)
    canvas.setFillColor(colors.HexColor("#65788A"))
    canvas.drawString(18 * mm, 9 * mm, "정책금융 영향 시뮬레이터 · 기능명세서")
    canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, str(document.page))
    canvas.restoreState()


def verify_pdf(path: Path) -> dict[str, object]:
    reader = PdfReader(path)
    texts = [(page.extract_text() or "").strip() for page in reader.pages]
    combined = "\n".join(texts)
    required = [
        "서비스 목적",
        "실제 구현범위",
        "AI 역할",
        "개인정보 처리",
        "샘플 입력과 예상 결과",
        "MVP 한계",
    ]
    missing = [item for item in required if item not in combined]
    if not reader.pages or any(len(text) < 40 for text in texts):
        raise RuntimeError("PDF page text extraction is unexpectedly empty")
    if missing:
        raise RuntimeError(f"Required PDF sections are missing: {missing}")
    if "\ufffd" in combined:
        raise RuntimeError("PDF text contains replacement characters")
    font_resource_pages = 0
    for page in reader.pages:
        resources = page.get("/Resources") or {}
        fonts = resources.get("/Font") if hasattr(resources, "get") else None
        if fonts:
            font_resource_pages += 1
    if font_resource_pages != len(reader.pages):
        raise RuntimeError("Every PDF page must declare font resources")
    return {
        "page_count": len(reader.pages),
        "all_pages_have_text": True,
        "all_pages_have_font_resources": True,
        "required_sections_present": True,
        "replacement_character_count": 0,
        "screenshot_image_analysis_performed": False,
    }


def main() -> None:
    for font in (REGULAR_FONT, BOLD_FONT):
        if not font.is_file():
            raise FileNotFoundError(font)
    pdfmetrics.registerFont(TTFont("MalgunGothic", str(REGULAR_FONT)))
    pdfmetrics.registerFont(TTFont("MalgunGothicBold", str(BOLD_FONT)))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title="정책금융 영향 시뮬레이터 기능명세서",
        author="2026 금융 AI Challenge",
    )
    document.build(
        build_story(SOURCE.read_text(encoding="utf-8"), styles()),
        onFirstPage=page_frame,
        onLaterPages=page_frame,
    )
    qa = verify_pdf(OUTPUT)
    qa_path = PROJECT_ROOT / "reports/re_stage9/functional_spec_pdf_qa.json"
    qa_path.write_text(
        __import__("json").dumps(qa, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Created {OUTPUT.relative_to(PROJECT_ROOT)} ({qa['page_count']} pages)")


if __name__ == "__main__":
    main()
