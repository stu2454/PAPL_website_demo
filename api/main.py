from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from api.routes import catalogue, papl

app = FastAPI(
    title="NDIS Pricing Artefacts API",
    description=(
        "Digital-first access to NDIS pricing information. "
        "Exposes the NDIS Support Catalogue and Pricing Arrangements as structured data. "
        "This is a proof-of-concept demonstrating what becomes possible when pricing artefacts "
        "are maintained in machine-readable formats rather than static Word/Excel files."
    ),
    version="0.1.0",
    contact={"name": "NDIA Pricing Team"},
    license_info={"name": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"},
)

app.include_router(catalogue.router)
app.include_router(papl.router)

# Serve frontend static files
# Try multiple path strategies to handle different deployment environments
_here = Path(__file__).resolve().parent  # api/
_candidates = [
    _here.parent / "frontend",       # repo root / frontend (most common)
    Path.cwd() / "frontend",         # cwd / frontend (Render fallback)
]
FRONTEND_DIR = next((p for p in _candidates if p.is_dir()), _here.parent / "frontend")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")


# Serve HTML pages
@app.get("/", include_in_schema=False)
def serve_home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/catalogue", include_in_schema=False)
def serve_catalogue():
    return FileResponse(FRONTEND_DIR / "catalogue.html")


@app.get("/catalogue/{item_number}", include_in_schema=False)
def serve_item(item_number: str):
    return FileResponse(FRONTEND_DIR / "item.html")


@app.get("/papl", include_in_schema=False)
def serve_papl():
    return FileResponse(FRONTEND_DIR / "papl.html")


@app.get("/papl/{slug}", include_in_schema=False)
def serve_papl_section(slug: str):
    return FileResponse(FRONTEND_DIR / "papl.html")
