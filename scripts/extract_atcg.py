"""
Extract NDIS AT, Home Modifications and Consumables Code Guide from Word doc.

Produces:
  data/atcg/  - one Markdown file per top-level section
  data/atcg_structure.yaml - document outline / metadata

Usage: python scripts/extract_atcg.py
"""

import re
import yaml
from pathlib import Path
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

DOCX_PATH = Path("assets/NDIS Assistive Technology Home Modifications and Consumables Code Guide 2025-26 v2.0 (2).docx")
OUTPUT_DIR = Path("data/atcg")

HEADING_STYLES = {
    "Heading 1": 1,
    "Heading 2": 2,
    "Heading 3": 3,
    "Heading 4": 4,
}

# Maps section slugs to the support categories they are relevant for
CATEGORY_RELEVANCE = {
    "introduction":                                                        [3, 5, 6],
    "general-claiming-rules":                                              [3, 5, 6],
    "low-cost-assistive-technology-mostly-items-1500":                     [5],
    "repairs-and-maintenance":                                             [5],
    "rental-supports":                                                     [5],
    "delivery-supports":                                                   [5],
    "consumables-support-category-03":                                     [3],
    "capital-supports-assistive-technology-support-category-05":           [5],
    "home-modifications-support-category-06":                              [6],
}


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "section"


def table_to_markdown(table: Table) -> str:
    rows = []
    for row in table.rows:
        cells = [cell.text.replace("\n", " ").strip() for cell in row.cells]
        rows.append(cells)
    if not rows:
        return ""
    lines = []
    lines.append("| " + " | ".join(rows[0]) + " |")
    lines.append("| " + " | ".join(["---"] * len(rows[0])) + " |")
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def para_to_markdown(para: Paragraph) -> str:
    style = para.style.name
    text = para.text.strip()
    if not text:
        return ""
    if style in HEADING_STYLES:
        return f"{'#' * HEADING_STYLES[style]} {text}"
    if style in ("List Paragraph", "table list bullet"):
        return f"- {text}"
    return text


def iter_block_items(doc):
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "p":
            yield Paragraph(child, doc)
        elif tag == "tbl":
            yield Table(child, doc)


def extract_sections(doc):
    sections = []
    current_title = "preamble"
    current_lines = []

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            style = block.style.name
            text = block.text.strip()

            if style in HEADING_STYLES and HEADING_STYLES[style] == 1:
                if current_lines:
                    sections.append((current_title, current_lines))
                current_title = text or "untitled"
                current_lines = [f"# {text}" if text else ""]
            else:
                md = para_to_markdown(block)
                if md:
                    current_lines.append(md)
                elif block.text.strip() == "":
                    if current_lines and current_lines[-1] != "":
                        current_lines.append("")

        elif isinstance(block, Table):
            md_table = table_to_markdown(block)
            if md_table:
                current_lines.append("")
                current_lines.append(md_table)
                current_lines.append("")

    if current_lines:
        sections.append((current_title, current_lines))

    return sections


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    doc = Document(DOCX_PATH)
    sections = extract_sections(doc)

    structure = []
    seen_slugs = {}

    for title, lines in sections:
        base_slug = slugify(title)
        count = seen_slugs.get(base_slug, 0)
        seen_slugs[base_slug] = count + 1
        slug = base_slug if count == 0 else f"{base_slug}-{count}"

        content = "\n".join(lines).strip()
        content = re.sub(r"\n{3,}", "\n\n", content)

        out_file = OUTPUT_DIR / f"{slug}.md"
        out_file.write_text(content, encoding="utf-8")

        headings = []
        for line in lines:
            m = re.match(r"^(#{1,4})\s+(.+)", line)
            if m:
                headings.append({
                    "level": len(m.group(1)),
                    "text": m.group(2),
                    "anchor": slugify(m.group(2)),
                })

        relevant_categories = CATEGORY_RELEVANCE.get(slug, [])

        structure.append({
            "title": title,
            "slug": slug,
            "file": f"atcg/{slug}.md",
            "headings": headings,
            "relevant_categories": relevant_categories,
        })

        print(f"  {out_file}  ({len(lines)} lines)  cats={relevant_categories}")

    structure_path = Path("data/atcg_structure.yaml")
    with open(structure_path, "w", encoding="utf-8") as f:
        yaml.dump(
            {
                "title": "NDIS AT, Home Modifications and Consumables Code Guide 2025-26",
                "version": "2.0",
                "source": DOCX_PATH.name,
                "sections": structure,
            },
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

    print(f"\nExtracted {len(sections)} sections → {OUTPUT_DIR}/")
    print(f"Structure written to {structure_path}")


if __name__ == "__main__":
    main()
