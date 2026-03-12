import markdown as md
from fastapi import APIRouter, HTTPException
from api import data_loader as db
from api.models import PaplSection, PaplSectionContent

router = APIRouter(prefix="/api/papl", tags=["PAPL Documentation"])


@router.get("/sections", response_model=list[PaplSection], summary="List PAPL sections")
def list_sections():
    return [
        PaplSection(**section)
        for section in db.papl_structure["sections"]
        if db.papl_content.get(section["slug"])  # only sections with content
    ]


@router.get("/{slug}", response_model=PaplSectionContent, summary="Get a PAPL section rendered as HTML")
def get_section(slug: str):
    raw = db.papl_content.get(slug)
    if raw is None:
        raise HTTPException(status_code=404, detail=f"Section '{slug}' not found")

    # Find metadata from structure
    section_meta = next(
        (s for s in db.papl_structure["sections"] if s["slug"] == slug), {}
    )

    content_html = md.markdown(
        raw,
        extensions=["tables", "toc"],
    )

    return PaplSectionContent(
        title=section_meta.get("title", slug),
        slug=slug,
        content_html=content_html,
        headings=section_meta.get("headings", []),
    )
