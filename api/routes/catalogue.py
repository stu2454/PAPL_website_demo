from fastapi import APIRouter, HTTPException, Query
from api import data_loader as db
from api.models import (
    CatalogueResponse,
    CategorySummary,
    RegistrationGroupSummary,
    SupportItem,
    SupportItemSummary,
)

router = APIRouter(prefix="/api", tags=["Support Catalogue"])


def _to_summary(item: dict) -> SupportItemSummary:
    pl = item.get("price_limits") or {}
    national_price = pl.get("NSW") or pl.get("ACT") or pl.get("VIC") or None
    return SupportItemSummary(
        support_item_number=item["support_item_number"],
        name=item["name"],
        support_category_number=item["support_category"]["number"],
        support_category_name=item["support_category"]["name"],
        registration_group_number=item["registration_group"]["number"],
        registration_group_name=item["registration_group"]["name"],
        unit_label=item.get("unit_label", item.get("unit", "")),
        requires_quote=item["requires_quote"],
        type=item.get("type"),
        national_price=national_price,
        legacy=item.get("legacy", False),
    )


@router.get("/support-items", response_model=CatalogueResponse, summary="List support items")
def list_support_items(
    q: str | None = Query(None, description="Search by item number or name"),
    category: int | None = Query(None, description="Filter by support category number"),
    registration_group: str | None = Query(None, description="Filter by registration group number"),
    type: str | None = Query(None, description="Filter by type (e.g. 'Price Limited Supports')"),
    requires_quote: bool | None = Query(None, description="Filter to quotable items"),
    include_legacy: bool = Query(False, description="Include legacy (deactivated) items"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    pool = db.all_items if include_legacy else db.current_items

    results = pool
    if q:
        q_lower = q.lower()
        results = [
            i for i in results
            if q_lower in i["name"].lower() or q_lower in i["support_item_number"].lower()
        ]
    if category is not None:
        results = [i for i in results if i["support_category"]["number"] == category]
    if registration_group is not None:
        results = [i for i in results if i["registration_group"]["number"] == registration_group]
    if type is not None:
        results = [i for i in results if i.get("type") == type]
    if requires_quote is not None:
        results = [i for i in results if i["requires_quote"] == requires_quote]

    total = len(results)
    page = results[offset: offset + limit]

    return CatalogueResponse(
        items=[_to_summary(i) for i in page],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/support-items/{item_number}", response_model=SupportItem, summary="Get a single support item")
def get_support_item(item_number: str):
    item = db.items_by_number.get(item_number)
    if not item:
        raise HTTPException(status_code=404, detail=f"Support item '{item_number}' not found")
    return SupportItem(**item)


@router.get("/categories", response_model=list[CategorySummary], summary="List support categories")
def list_categories(include_legacy: bool = Query(False)):
    pool = db.all_items if include_legacy else db.current_items
    counts: dict[int, int] = {}
    for item in pool:
        n = item["support_category"]["number"]
        counts[n] = counts.get(n, 0) + 1

    return [
        CategorySummary(
            number=cat["number"],
            name=cat["name"],
            name_pace=cat["name_pace"],
            item_count=counts.get(cat["number"], 0),
        )
        for cat in db.categories
    ]


@router.get("/registration-groups", response_model=list[RegistrationGroupSummary], summary="List registration groups")
def list_registration_groups(
    category: int | None = Query(None),
    include_legacy: bool = Query(False),
):
    pool = db.all_items if include_legacy else db.current_items
    if category is not None:
        pool = [i for i in pool if i["support_category"]["number"] == category]

    counts: dict[str, int] = {}
    for item in pool:
        n = item["registration_group"]["number"]
        counts[n] = counts.get(n, 0) + 1

    return [
        RegistrationGroupSummary(
            number=rg["number"],
            name=rg["name"],
            item_count=counts.get(rg["number"], 0),
        )
        for rg in db.registration_groups
        if counts.get(rg["number"], 0) > 0
    ]
