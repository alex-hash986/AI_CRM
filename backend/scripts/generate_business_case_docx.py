"""Render the portfolio case from docs/BUSINESS_CASE.md with python-docx."""

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from generate_tz import ROOT, callout, configure, table

INLINE = re.compile(r"\*\*([^*]+)\*\*|`([^`]+)`|\[([^\]]+)\]\(([^)]+)\)")
IMAGE = re.compile(r"^!\[([^\]]+)\]\(([^)]+)\)$")
PAGE_STARTS = {
    "Сценарии работы с лидами",
    "Сценарии коммуникаций и аналитики",
    "Ожидаемый эффект для бизнеса",
    "Безопасность и масштабирование",
}


def add_link(paragraph, label, target):
    relationship = paragraph.part.relate_to(target, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), relationship)
    run = OxmlElement("w:r")
    properties = OxmlElement("w:rPr")
    style = OxmlElement("w:rStyle")
    style.set(qn("w:val"), "Hyperlink")
    properties.append(style)
    run.append(properties)
    text = OxmlElement("w:t")
    text.text = label
    run.append(text)
    link.append(run)
    paragraph._p.append(link)


def add_text(paragraph, text):
    text = text.replace("₽", "руб.")
    offset = 0
    for match in INLINE.finditer(text):
        paragraph.add_run(text[offset:match.start()])
        bold, code, label, target = match.groups()
        if label is not None:
            add_link(paragraph, label, target)
        else:
            run = paragraph.add_run(bold or code)
            run.bold = bold is not None
            if code is not None:
                run.font.name = "Liberation Mono"
        offset = match.end()
    paragraph.add_run(text[offset:])


def add_picture(document, path, caption):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(2)
    paragraph.paragraph_format.keep_with_next = True
    width = 2.48 if path.name == "ai-drawer.png" else 3.95
    shape = paragraph.add_run().add_picture(str(path), width=Inches(width))
    shape._inline.docPr.set("descr", caption)
    paragraph = document.add_paragraph(caption, style="Caption")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_table(document, lines):
    rows = [tuple(cell.strip() for cell in line.strip("|").split("|")) for line in lines]
    headers = rows[0]
    if len(headers) != 3 or len(rows) < 3 or any(len(row) != 3 for row in rows):
        raise ValueError("Expected a three-column Markdown table with a header")
    table(document, headers, rows[2:], (1.48, 2.04, 3.15))


def build(source):
    document = Document()
    configure(document)
    document.core_properties.title = "Бизнес кейс AI Sales CRM"
    document.styles["Normal"].font.size = Pt(10.5)
    document.styles["Normal"].paragraph_format.space_after = Pt(6)
    document.styles["Heading 1"].paragraph_format.space_before = Pt(15)
    document.styles["Heading 2"].paragraph_format.space_before = Pt(8)
    document.styles["Caption"].font.name = "Liberation Sans"
    document.styles["Caption"].font.size = Pt(9)

    lines = iter(source.read_text(encoding="utf-8").splitlines())
    line = next(lines, "")
    while line is not None:
        if line.startswith("# "):
            document.add_paragraph(line[2:], "Title")
            document.add_paragraph("Кейс для портфолио", "Subtitle")
        elif line.startswith("## "):
            heading = line[3:]
            if heading in PAGE_STARTS:
                document.add_page_break()
            document.add_heading(heading, 1)
        elif line.startswith("### "):
            document.add_heading(line[4:], 2)
        elif line.startswith("> "):
            callout(document, "Как это работает", line[2:])
        elif line.startswith("|"):
            rows = []
            while line is not None and line.startswith("|"):
                rows.append(line)
                line = next(lines, None)
            add_table(document, rows)
            continue
        elif line.startswith("```"):
            for code in lines:
                if code.startswith("```"):
                    break
                paragraph = document.add_paragraph()
                run = paragraph.add_run(code)
                run.font.name = "Liberation Mono"
                run.font.size = Pt(9)
        elif match := IMAGE.fullmatch(line):
            add_picture(document, source.parent / match[2], match[1])
        elif line.strip():
            add_text(document.add_paragraph(), line)
        line = next(lines, None)
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "docs" / "BUSINESS_CASE.md")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "Business_Case_AI_Sales_CRM.docx")
    options = parser.parse_args()
    document = build(options.source)
    options.output.parent.mkdir(parents=True, exist_ok=True)
    document.save(options.output)
    print(options.output.resolve())


if __name__ == "__main__":
    main()
