from pydantic import BaseModel


class PriceLimits(BaseModel):
    ACT: float | None = None
    NSW: float | None = None
    NT: float | None = None
    QLD: float | None = None
    SA: float | None = None
    TAS: float | None = None
    VIC: float | None = None
    WA: float | None = None
    remote: float | None = None
    very_remote: float | None = None


class ClaimingRules(BaseModel):
    non_face_to_face: bool | None = None
    provider_travel: bool | None = None
    short_notice_cancellations: bool | None = None
    ndia_requested_reports: bool | None = None
    irregular_sil_supports: bool | None = None


class SupportItem(BaseModel):
    support_item_number: str
    name: str
    registration_group: dict
    support_category: dict
    unit: str
    unit_label: str
    requires_quote: bool
    effective_from: str | None
    effective_to: str | None
    type: str | None
    price_limits: PriceLimits | None
    claiming_rules: ClaimingRules
    legacy: bool = False


class SupportItemSummary(BaseModel):
    support_item_number: str
    name: str
    support_category_number: int
    support_category_name: str
    registration_group_number: str
    registration_group_name: str
    unit_label: str
    requires_quote: bool
    type: str | None
    national_price: float | None  # NSW price as proxy for national
    legacy: bool = False


class CatalogueResponse(BaseModel):
    items: list[SupportItemSummary]
    total: int
    limit: int
    offset: int


class CategorySummary(BaseModel):
    number: int
    name: str
    name_pace: str
    item_count: int


class RegistrationGroupSummary(BaseModel):
    number: str
    name: str
    item_count: int


class PaplSection(BaseModel):
    title: str
    slug: str
    file: str
    headings: list[dict]


class PaplSectionContent(BaseModel):
    title: str
    slug: str
    content_html: str
    headings: list[dict]
