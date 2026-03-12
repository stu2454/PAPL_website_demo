# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project purpose

Proof-of-concept to demonstrate a **digital-first approach** to NDIS pricing artefacts. The current state is two static files (Word + Excel) downloaded from the NDIS public website. This PoC shows how the same data can power a web interface and a REST API, serving users from casual participants to large providers.

## Tech stack

- **Backend**: FastAPI (Python) — `api/`
- **Frontend**: Static HTML/CSS/JS served by FastAPI — `frontend/`
- **Deployment**: Render (via GitHub) — `render.yaml`
- **Python env**: `.venv/` managed with `python3 -m venv .venv`

Activate venv: `source .venv/bin/activate`

Install deps: `pip install -r requirements.txt`

Run locally: `uvicorn api.main:app --reload`
- App: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs

## App structure

```
api/
  main.py          # FastAPI app, static file mounting, HTML page routes
  data_loader.py   # Loads all JSON/YAML/MD into memory at startup
  models.py        # Pydantic response models
  routes/
    catalogue.py   # /api/support-items, /api/categories, /api/registration-groups
    papl.py        # /api/papl/sections, /api/papl/{slug}
frontend/
  index.html       # Landing page with hero, feature cards, before/after compare
  catalogue.html   # Filterable support item browser
  item.html        # Individual support item detail page
  papl.html        # PAPL section reader with sidebar nav and TOC
  static/
    style.css      # All styles (CSS custom properties, no framework)
    catalogue.js   # Catalogue filter/search/pagination logic
    papl.js        # PAPL sidebar + section loading logic
```

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /api/support-items` | List/filter items. Params: `q`, `category`, `registration_group`, `type`, `requires_quote`, `include_legacy`, `limit`, `offset` |
| `GET /api/support-items/{item_number}` | Single item detail |
| `GET /api/categories` | Support categories with item counts |
| `GET /api/registration-groups` | Registration groups (filterable by `category`) |
| `GET /api/papl/sections` | PAPL section list |
| `GET /api/papl/{slug}` | Section content rendered as HTML |

## Data architecture (digital-first model)

The `data/` directory is the **single source of truth**, extracted from the assets in `assets/`.

```
data/
  support_catalogue.json    # All support items (635 current + 36 legacy)
  papl_structure.yaml       # Document outline / section index
  papl/                     # One Markdown file per top-level PAPL section
    introduction.md
    general-claiming-rules.md
    core-assistance-with-daily-life.md
    ... (20 sections total)
```

### support_catalogue.json structure

```json
{
  "metadata": { "version", "effective_date", ... },
  "support_categories": [ { "number", "name", "number_pace", "name_pace" } ],
  "registration_groups": [ { "number", "name" } ],
  "support_items": {
    "current": [ <635 items> ],
    "legacy":  [ <36 items> ]
  }
}
```

Each support item has:
- `support_item_number` — e.g. `"01_002_0107_1_1"` (format: `CC_NNN_RRRR_P_V`)
- `registration_group` and `support_category` (nested objects)
- `unit` / `unit_label` — H=Hour, D=Day, WK=Week, MON=Month, YR=Year, E=Each
- `requires_quote` — boolean; quotable supports have no price limits
- `price_limits` — dict of state codes + `remote` + `very_remote` (null if quotable)
- `claiming_rules` — `non_face_to_face`, `provider_travel`, `short_notice_cancellations`, `ndia_requested_reports`, `irregular_sil_supports` (true/false/null where null = not applicable)
- `type` — `"Price Limited Supports"`, `"Quotable Supports"`, `"Unit Price = $1"`

### PAPL Markdown sections

Extracted from the Word doc with headings preserved (H1–H5 → `#`–`#####`). Tables converted to Markdown. One file per H1 section. `papl_structure.yaml` contains the full outline with anchors.

## Extraction scripts

Source-to-data conversion. Run these when a new version of the source files is published:

```bash
python scripts/extract_catalogue.py   # Excel → data/support_catalogue.json
python scripts/extract_papl.py        # Word  → data/papl/*.md + papl_structure.yaml
```

Dependencies: `openpyxl`, `python-docx`, `pyyaml`

## Stakeholder context

Multiple internal audiences need to be convinced of the digital-first approach:
- **Public website team** — show the web UI is better than a Word download
- **Provider/participant portals** — show API access and embeddability
- **Legal** — Git history is better version control than filename versioning
- **Cybersecurity** — API with rate limiting is more controlled than open file downloads
- **Policy/IT** — single source of truth eliminates manual dual-maintenance

The PoC should demonstrate all three layers: human web UI, REST API with Swagger docs, and the ability to still generate static downloads from the same source data.
