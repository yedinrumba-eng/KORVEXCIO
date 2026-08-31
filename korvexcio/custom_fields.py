import json
from pathlib import Path

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CUSTOM_DIR = Path(__file__).parent / "custom"


def sync_custom_fields():
    """Patron KSA: un archivo JSON por doctype bajo custom/, no
    bench export-fixtures. Se corre en cada bench migrate (after_migrate),
    asi que es seguro correrlo mas de una vez — create_custom_fields()
    ya es idempotente (actualiza si el campo existe, lo crea si no)."""
    for path in sorted(CUSTOM_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            fields = json.load(f)
        create_custom_fields(fields)

    frappe.db.commit()
