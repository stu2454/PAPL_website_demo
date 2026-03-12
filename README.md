# NDIS Pricing Artefacts — Digital-First Exemplar

A proof-of-concept web application built by the **NDIA Markets Delivery Branch** to demonstrate what becomes possible when NDIS pricing artefacts are maintained as structured data rather than static Word and Excel files.

Live deployment: [https://ndis-pricing-exemplar.onrender.com](https://ndis-pricing-exemplar.onrender.com)
API documentation: [https://ndis-pricing-exemplar.onrender.com/docs](https://ndis-pricing-exemplar.onrender.com/docs)

---

## Background

The two primary NDIS pricing artefacts — the **Pricing Arrangements and Price Limits (PAPL)** and the **Support Catalogue** — are among the most downloaded documents on the NDIS website. They are published as a Word document and an Excel spreadsheet respectively, and updated several times a year.

While these formats are familiar, they create real constraints:

- Users must download and manually search large files to find what they need
- Provider portals and software vendors that need pricing data must re-key it from the Excel file — there is no machine-readable source
- Every update requires re-publishing complete new versions of all files; version history is managed through filename conventions (`v1.1_0.docx`) rather than a proper audit trail
- There is no way to filter, compare, or query the data without opening the file
- The **AT, Home Modifications and Consumables Code Guide** is a separate document that users must locate and cross-reference independently

This exemplar demonstrates an alternative: **structured data as the master copy**, with the website, API, and any future static document exports all generated from the same source.

The primary purpose of this exemplar is to reduce uncertainty about *whether* the approach is technically feasible — and to give stakeholders (public website team, provider portals, IT, legal, cybersecurity, policy) a working system to react to, rather than an abstract proposal.

---

## What it demonstrates

### Support Catalogue browser
All 635 current (and 36 legacy) support items from the 2025–26 Support Catalogue, queryable in real time:
- Full-text search by name or item number
- Filter by support category, registration group, and item type
- Paginated results with 50 items per page
- Individual item detail pages showing price limits by jurisdiction, claiming rules, and classification metadata

### PAPL reader
The full text of the Pricing Arrangements and Price Limits 2025–26 v1.1, rendered as navigable web content:
- Persistent sidebar navigation across all 20 sections
- In-page table of contents for sections with multiple headings
- The three sections that were previously stubs pointing to the Code Guide (**Capital – Assistive Technology**, **Core – Consumables**, **Capital – Home Modifications & SDA**) now include the relevant Code Guide content merged in directly at serve time

### REST API
Every piece of data the website uses is accessible via a documented REST API:
- Full OpenAPI 3.0 specification with Swagger UI at `/docs`
- Filterable, searchable, paginated support item listing
- Per-item lookup by item number
- PAPL sections as structured JSON with rendered HTML and heading metadata
- AT & HM Code Guide sections individually accessible

---

## Architecture

### Data formats

The exemplar uses three structured formats, each suited to a different type of content:

| Format | Content | Source |
|--------|---------|--------|
| **JSON** | Support Catalogue — all 671 items with typed fields for price limits, claiming rules, registration group, unit, effective dates | `data/support_catalogue.json` |
| **Markdown** | PAPL narrative text — 20 sections, one file per H1 | `data/papl/*.md` |
| **Markdown** | AT & HM Code Guide — 15 sections | `data/atcg/*.md` |
| **YAML** | Document structure for PAPL and Code Guide — section titles, slugs, headings, category mappings | `data/papl_structure.yaml`, `data/atcg_structure.yaml` |

### API layer

**FastAPI** (`api/`) loads all structured data into memory at startup and exposes it through three routers:

- `api/routes/catalogue.py` — `/api/support-items`, `/api/categories`, `/api/registration-groups`
- `api/routes/papl.py` — `/api/papl/sections`, `/api/papl/{slug}`
- `api/routes/atcg.py` — `/api/atcg/sections`, `/api/atcg/{slug}`

For the three PAPL sections that were sparse stubs in the original Word document (`capital-assistive-technology`, `core-consumables`, `capital-home-modifications-and-specialist-disability-accommodation`), the PAPL route merges in the relevant Code Guide Markdown at serve time before converting to HTML. The source files remain separate; the merge is a runtime operation defined in `ATCG_MERGE` in `api/routes/papl.py`.

**Pydantic v2** models (`api/models.py`) validate all API responses and generate the OpenAPI schema.

### Frontend

Plain HTML/CSS/JS — no framework. Five pages served as static files by FastAPI:

- `/` — Home page with quick search
- `/catalogue` — Support Catalogue browser (`frontend/static/catalogue.js`)
- `/catalogue/{item_number}` — Item detail page
- `/papl` / `/papl/{slug}` — PAPL reader (`frontend/static/papl.js`)
- `/explainer` — How It Works

All pages fetch data from the API at runtime using the same endpoints available to any external consumer.

---

## Data extraction

The structured data files were extracted from the original source documents using Python scripts. This is a one-time process each time a new version of the artefacts is published.

### `scripts/extract_catalogue.py`
Reads the Support Catalogue Excel file row by row. Each support item becomes a structured JSON object. Price limits are normalised into a per-jurisdiction map (`ACT`, `NSW`, `NT`, `QLD`, `SA`, `TAS`, `VIC`, `WA`, `remote`, `very_remote`). Claiming rule flags (Y/N/NA) are converted to typed booleans or `null`. Reference tables for categories and registration groups are deduplicated automatically.

Output: `data/support_catalogue.json`

### `scripts/extract_papl.py`
Parses the PAPL Word document paragraph by paragraph. Heading styles (Heading 1–5) become Markdown headings. Tables are converted to Markdown table syntax. Each top-level section (Heading 1) becomes its own Markdown file, and the document outline is written to a YAML index with section slugs and heading metadata.

Output: `data/papl/*.md` + `data/papl_structure.yaml`

### `scripts/extract_atcg.py`
The same process applied to the AT, Home Modifications and Consumables Code Guide. An additional metadata field — `relevant_categories` — maps each section to the NDIS support categories it covers (03, 05, 06). This metadata drives the runtime content merge into PAPL.

Output: `data/atcg/*.md` + `data/atcg_structure.yaml`

---

## Local development

**Requirements:** Python 3.12

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the development server
uvicorn api.main:app --reload
```

The application will be available at `http://localhost:8000`. The API documentation is at `http://localhost:8000/docs`.

---

## Deployment

The application is deployed on [Render](https://render.com) using the Blueprint defined in `render.yaml` (free plan).

```yaml
services:
  - type: web
    name: ndis-pricing-exemplar
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

To deploy your own instance: fork the repository, create a new Render web service, and connect it to your fork. Render will detect `render.yaml` automatically.

---

## Repository structure

```
.
├── api/
│   ├── main.py              # FastAPI app, static file serving, HTML routes
│   ├── data_loader.py       # Loads all structured data at startup
│   ├── models.py            # Pydantic response models
│   └── routes/
│       ├── catalogue.py     # Support Catalogue endpoints
│       ├── papl.py          # PAPL endpoints (includes Code Guide merge logic)
│       └── atcg.py          # AT & HM Code Guide endpoints
├── data/
│   ├── support_catalogue.json
│   ├── papl_structure.yaml
│   ├── atcg_structure.yaml
│   ├── papl/                # 20 Markdown files, one per PAPL section
│   └── atcg/                # 15 Markdown files, one per Code Guide section
├── frontend/
│   ├── index.html
│   ├── catalogue.html
│   ├── item.html
│   ├── papl.html
│   ├── explainer.html
│   └── static/
│       ├── style.css
│       ├── catalogue.js
│       └── papl.js
├── scripts/
│   ├── extract_catalogue.py
│   ├── extract_papl.py
│   └── extract_atcg.py
├── requirements.txt
├── render.yaml
└── runtime.txt
```

---

## What this exemplar is not

This is a proof of concept, not a production system. A production implementation would require:

- Formal content governance — who can update the source data, what review process applies, how errors are corrected
- Security review of the API (authentication, rate limiting, access controls for write operations)
- Integration with existing publishing and CMS workflows
- Accessibility audit of the web interface (WCAG 2.1 AA)
- Legal review of content representation and liability for data accuracy

The intent is to demonstrate that the approach is technically feasible and to illustrate the user experience — not to be the final implementation.

---

## Source data

Content is extracted from the following NDIS publications (2025–26 v1.1):

- NDIS Pricing Arrangements and Price Limits 2025–26
- NDIS Support Catalogue 2025–26
- NDIS Assistive Technology, Home Modifications and Consumables Code Guide 2025–26

Always refer to the [NDIS website](https://www.ndis.gov.au/providers/pricing-arrangements) for the authoritative current versions of these documents.

---

*NDIA Markets Delivery Branch · Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)*
