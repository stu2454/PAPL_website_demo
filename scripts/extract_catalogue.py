"""
Extract NDIS Support Catalogue from Excel to structured JSON.

Usage: python scripts/extract_catalogue.py
Output: data/support_catalogue.json
"""

import json
import openpyxl
from datetime import date
from pathlib import Path

EXCEL_PATH = Path("assets/NDIS-Support Catalogue-2025-26 -v1.1.xlsx")
OUTPUT_PATH = Path("data/support_catalogue.json")

COLUMNS = [
    "support_item_number",      # 0
    "name",                     # 1
    "registration_group_number",# 2
    "registration_group_name",  # 3
    "support_category_number",  # 4
    "support_category_number_pace", # 5
    "support_category_name",    # 6
    "support_category_name_pace", # 7
    "unit",                     # 8
    "quote",                    # 9
    "start_date",               # 10
    "end_date",                 # 11
    "ACT",                      # 12
    "NSW",                      # 13
    "NT",                       # 14
    "QLD",                      # 15
    "SA",                       # 16
    "TAS",                      # 17
    "VIC",                      # 18
    "WA",                       # 19
    "remote",                   # 20
    "very_remote",              # 21
    "non_face_to_face",         # 22
    "provider_travel",          # 23
    "short_notice_cancellations", # 24
    "ndia_requested_reports",   # 25
    "irregular_sil_supports",   # 26
    "type",                     # 27
]

STATES = ["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"]
CLAIMING_FLAGS = [
    "non_face_to_face",
    "provider_travel",
    "short_notice_cancellations",
    "ndia_requested_reports",
    "irregular_sil_supports",
]

UNIT_LABELS = {
    "H": "Hour",
    "D": "Day",
    "WK": "Week",
    "MON": "Month",
    "YR": "Year",
    "E": "Each",
}


def parse_date(value):
    """Convert Excel date integer or string to ISO date string."""
    if value is None:
        return None
    if isinstance(value, int):
        # Excel stores dates as integers; openpyxl may return them raw
        # 99991231 means no end date
        if value == 99991231:
            return None
        s = str(value)
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    if isinstance(value, str):
        if value == "99991231":
            return None
        if len(value) == 8:
            return f"{value[:4]}-{value[4:6]}-{value[6:8]}"
    # Already a date object
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def parse_flag(value):
    """Convert Y/N/NA/None to boolean or null."""
    if value in ("Y", "Yes"):
        return True
    if value in ("N", "No"):
        return False
    return None  # NA or missing means not applicable


def parse_price(value):
    """Return float price or None."""
    if value is None:
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def parse_row(row_dict):
    item = {
        "support_item_number": row_dict["support_item_number"],
        "name": row_dict["name"],
        "registration_group": {
            "number": row_dict["registration_group_number"],
            "name": row_dict["registration_group_name"],
        },
        "support_category": {
            "number": row_dict["support_category_number"],
            "number_pace": row_dict["support_category_number_pace"],
            "name": row_dict["support_category_name"],
            "name_pace": row_dict["support_category_name_pace"],
        },
        "unit": row_dict["unit"],
        "unit_label": UNIT_LABELS.get(row_dict["unit"], row_dict["unit"]),
        "requires_quote": row_dict["quote"] == "Yes",
        "effective_from": parse_date(row_dict["start_date"]),
        "effective_to": parse_date(row_dict["end_date"]),
        "type": row_dict["type"],
    }

    # Price limits by state
    price_limits = {}
    for state in STATES:
        p = parse_price(row_dict[state])
        if p is not None:
            price_limits[state] = p
    if (r := parse_price(row_dict["remote"])) is not None:
        price_limits["remote"] = r
    if (vr := parse_price(row_dict["very_remote"])) is not None:
        price_limits["very_remote"] = vr
    item["price_limits"] = price_limits if price_limits else None

    # Claiming rules
    claiming = {}
    for flag in CLAIMING_FLAGS:
        claiming[flag] = parse_flag(row_dict[flag])
    item["claiming_rules"] = claiming

    return item


def extract_sheet(ws, is_legacy=False):
    rows = list(ws.iter_rows(values_only=True))
    items = []
    for row in rows[1:]:  # skip header
        if not row[0]:
            continue
        row_dict = dict(zip(COLUMNS, row))
        item = parse_row(row_dict)
        if is_legacy:
            item["legacy"] = True
        items.append(item)
    return items


def build_reference_data(items):
    """Build deduplicated lookup tables for categories and registration groups."""
    categories = {}
    reg_groups = {}

    for item in items:
        cat = item["support_category"]
        num = cat["number"]
        if num not in categories:
            categories[num] = {
                "number": num,
                "number_pace": cat["number_pace"],
                "name": cat["name"],
                "name_pace": cat["name_pace"],
            }

        rg = item["registration_group"]
        rnum = rg["number"]
        if rnum not in reg_groups:
            reg_groups[rnum] = {
                "number": rnum,
                "name": rg["name"],
            }

    return (
        sorted(categories.values(), key=lambda x: x["number"]),
        sorted(reg_groups.values(), key=lambda x: x["number"]),
    )


def main():
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True)

    current_items = extract_sheet(wb["Current Support Items"], is_legacy=False)
    legacy_items = extract_sheet(wb["Legacy Support Items"], is_legacy=True)
    all_items = current_items + legacy_items

    categories, reg_groups = build_reference_data(all_items)

    output = {
        "metadata": {
            "title": "NDIS Support Catalogue 2025-26",
            "version": "1.1",
            "source": "NDIS-Support Catalogue-2025-26 -v1.1.xlsx",
            "extracted": date.today().isoformat(),
        },
        "support_categories": categories,
        "registration_groups": reg_groups,
        "support_items": {
            "current": current_items,
            "legacy": legacy_items,
        },
        "counts": {
            "current": len(current_items),
            "legacy": len(legacy_items),
            "total": len(all_items),
        },
    }

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Written {len(current_items)} current + {len(legacy_items)} legacy items to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
