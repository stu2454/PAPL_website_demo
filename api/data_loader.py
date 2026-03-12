"""
Loads all source data into memory at startup.
All routes import from this module.
"""

import json
from pathlib import Path
import yaml

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_catalogue():
    with open(DATA_DIR / "support_catalogue.json", encoding="utf-8") as f:
        return json.load(f)


def _load_papl_structure():
    with open(DATA_DIR / "papl_structure.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_papl_content(structure):
    content = {}
    for section in structure["sections"]:
        path = DATA_DIR / section["file"]
        if path.exists():
            content[section["slug"]] = path.read_text(encoding="utf-8")
    return content


# --- Loaded once at import time ---
catalogue = _load_catalogue()

# Flat list of all current items for fast filtering
current_items: list[dict] = catalogue["support_items"]["current"]
legacy_items: list[dict] = catalogue["support_items"]["legacy"]
all_items: list[dict] = current_items + legacy_items

# Lookup maps
items_by_number: dict[str, dict] = {
    item["support_item_number"]: item for item in all_items
}
categories: list[dict] = catalogue["support_categories"]
registration_groups: list[dict] = catalogue["registration_groups"]

papl_structure = _load_papl_structure()
papl_content: dict[str, str] = _load_papl_content(papl_structure)
