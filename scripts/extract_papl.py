"""
Extract NDIS Pricing Arrangements and Price Limits from Word doc.

Produces:
  data/papl/  - one Markdown file per top-level section
  data/papl_structure.yaml - document outline / metadata

Usage: python scripts/extract_papl.py
"""

import re
import yaml
from pathlib import Path
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

DOCX_PATH = Path("assets/NDIS Pricing Arrangements and Price Limits 2025-26 v1.1_0.docx")
OUTPUT_DIR = Path("data/papl")

# Styles that map to Markdown headings
HEADING_STYLES = {
    "Heading 1": 1,
    "Heading 2": 2,
    "Heading 3": 3,
    "Heading 4": 4,
    "Heading 5": 5,
    "CEO Brief - Heading 1": 1,
}


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text or "section"


def table_to_markdown(table: Table) -> str:
    """Convert a docx table to a Markdown table."""
    rows = []
    for row in table.rows:
        cells = [cell.text.replace("\n", " ").strip() for cell in row.cells]
        rows.append(cells)

    if not rows:
        return ""

    lines = []
    # Header row
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
        level = HEADING_STYLES[style]
        return f"{'#' * level} {text}"

    if style == "Dot Point":
        return f"- {text}"

    if style == "List Paragraph":
        # Check indent level via paragraph format
        return f"- {text}"

    # Normal and others → plain paragraph
    return text


def iter_block_items(doc):
    """Iterate over paragraphs and tables in document order."""
    from docx.oxml.ns import qn
    parent = doc.element.body
    for child in parent.iterchildren():
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "p":
            yield Paragraph(child, doc)
        elif tag == "tbl":
            yield Table(child, doc)


def extract_sections(doc):
    """
    Split document into sections based on H1 headings.
    Returns list of (title, slug, content_lines).
    """
    sections = []
    current_title = "preamble"
    current_lines = []

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            style = block.style.name
            text = block.text.strip()

            if style in HEADING_STYLES and HEADING_STYLES[style] == 1:
                # Save current section
                if current_lines:
                    sections.append((current_title, current_lines))
                current_title = text or "untitled"
                current_lines = [f"# {text}" if text else ""]
            else:
                md = para_to_markdown(block)
                if md:
                    current_lines.append(md)
                elif block.text.strip() == "":
                    # Preserve blank lines between paragraphs (deduplicated)
                    if current_lines and current_lines[-1] != "":
                        current_lines.append("")

        elif isinstance(block, Table):
            md_table = table_to_markdown(block)
            if md_table:
                current_lines.append("")
                current_lines.append(md_table)
                current_lines.append("")

    # Final section
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
        # Handle duplicate slugs (e.g. empty H1s)
        count = seen_slugs.get(base_slug, 0)
        seen_slugs[base_slug] = count + 1
        slug = base_slug if count == 0 else f"{base_slug}-{count}"

        # Write markdown file
        content = "\n".join(lines).strip()
        # Collapse excessive blank lines
        content = re.sub(r"\n{3,}", "\n\n", content)

        out_file = OUTPUT_DIR / f"{slug}.md"
        out_file.write_text(content, encoding="utf-8")

        # Collect headings within this section for the outline
        headings = []
        for line in lines:
            m = re.match(r"^(#{1,5})\s+(.+)", line)
            if m:
                headings.append({
                    "level": len(m.group(1)),
                    "text": m.group(2),
                    "anchor": slugify(m.group(2)),
                })

        structure.append({
            "title": title,
            "slug": slug,
            "file": f"papl/{slug}.md",
            "headings": headings,
        })

        print(f"  {out_file}  ({len(lines)} lines)")

    # Write structure YAML
    structure_path = Path("data/papl_structure.yaml")
    with open(structure_path, "w", encoding="utf-8") as f:
        yaml.dump(
            {
                "title": "NDIS Pricing Arrangements and Price Limits 2025-26",
                "version": "1.1",
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
