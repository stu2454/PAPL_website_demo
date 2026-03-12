import markdown as md
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from api import data_loader as db

router = APIRouter(prefix="/api/atcg", tags=["AT & HM Code Guide"])


class AtcgSection(BaseModel):
    title: str
    slug: str
    file: str
    headings: list[dict]
    relevant_categories: list[int]


class AtcgSectionContent(BaseModel):
    title: str
    slug: str
    content_html: str
    headings: list[dict]
    relevant_categories: list[int]


@router.get("/sections", response_model=list[AtcgSection], summary="List Code Guide sections")
def list_sections(category: int | None = Query(None, description="Filter to sections relevant for a support category")):
    sections = [
        s for s in db.atcg_structure["sections"]
        if db.atcg_content.get(s["slug"])
    ]
    if category is not None:
        sections = [s for s in sections if category in s.get("relevant_categories", [])]
    return [AtcgSection(**s) for s in sections]


@router.get("/{slug}", response_model=AtcgSectionContent, summary="Get a Code Guide section rendered as HTML")
def get_section(slug: str):
    raw = db.atcg_content.get(slug)
    if raw is None:
        raise HTTPException(status_code=404, detail=f"Section '{slug}' not found")

    section_meta = next(
        (s for s in db.atcg_structure["sections"] if s["slug"] == slug), {}
    )

    content_html = md.markdown(raw, extensions=["tables", "toc"])

    return AtcgSectionContent(
        title=section_meta.get("title", slug),
        slug=slug,
        content_html=content_html,
        headings=section_meta.get("headings", []),
        relevant_categories=section_meta.get("relevant_categories", []),
    )
