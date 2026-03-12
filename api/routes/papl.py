import re
import markdown as md
from fastapi import APIRouter, HTTPException
from api import data_loader as db
from api.models import PaplSection, PaplSectionContent

router = APIRouter(prefix="/api/papl", tags=["PAPL Documentation"])

# These PAPL sections contain only a stub pointing to the Code Guide.
# We replace the stub body with the full merged Code Guide content.
ATCG_MERGE: dict[str, list[str]] = {
    "capital-assistive-technology": [
        "low-cost-assistive-technology-mostly-items-1500",
        "repairs-and-maintenance",
        "rental-supports",
        "delivery-supports",
        "capital-supports-assistive-technology-support-category-05",
    ],
    "core-consumables": [
        "consumables-support-category-03",
    ],
    "capital-home-modifications-and-specialist-disability-accommodation": [
        "home-modifications-support-category-06",
    ],
}


def _strip_leading_h1(markdown_text: str) -> str:
    """Remove the first H1 heading from a Markdown string."""
    return re.sub(r"^#\s+.+\n?", "", markdown_text, count=1).lstrip("\n")


def _merge_atcg(papl_slug: str, papl_title: str) -> tuple[str, list[dict]]:
    """
    Build merged Markdown + combined headings for a PAPL section that
    integrates Code Guide content.
    """
    atcg_slugs = ATCG_MERGE[papl_slug]
    merged_parts = [f"# {papl_title}\n"]
    merged_headings = [{"level": 1, "text": papl_title, "anchor": papl_slug}]

    for slug in atcg_slugs:
        raw = db.atcg_content.get(slug)
        if not raw:
            continue
        # Strip the Code Guide section's own H1 — the PAPL H1 is the parent
        merged_parts.append(_strip_leading_h1(raw))
        merged_parts.append("\n\n")

        # Collect headings (skip H1, already stripped)
        atcg_meta = next(
            (s for s in db.atcg_structure["sections"] if s["slug"] == slug), {}
        )
        for h in atcg_meta.get("headings", []):
            if h["level"] > 1:
                merged_headings.append(h)

    return "\n".join(merged_parts), merged_headings


@router.get("/sections", response_model=list[PaplSection], summary="List PAPL sections")
def list_sections():
    return [
        PaplSection(**section)
        for section in db.papl_structure["sections"]
        if db.papl_content.get(section["slug"])
    ]


@router.get("/{slug}", response_model=PaplSectionContent, summary="Get a PAPL section rendered as HTML")
def get_section(slug: str):
    raw = db.papl_content.get(slug)
    if raw is None:
        raise HTTPException(status_code=404, detail=f"Section '{slug}' not found")

    section_meta = next(
        (s for s in db.papl_structure["sections"] if s["slug"] == slug), {}
    )
    title = section_meta.get("title", slug)

    if slug in ATCG_MERGE:
        merged_md, headings = _merge_atcg(slug, title)
        content_html = md.markdown(merged_md, extensions=["tables", "toc"])
    else:
        content_html = md.markdown(raw, extensions=["tables", "toc"])
        headings = section_meta.get("headings", [])

    return PaplSectionContent(
        title=title,
        slug=slug,
        content_html=content_html,
        headings=headings,
    )
