"""Item Defaults and Price handling for bulk import (S5.1).

FASE 4.8: Separado de bulk_import.py.
Contiene: _upsert_item_price, _get_default_warehouse
"""

from __future__ import annotations

import frappe
from frappe import _


def _upsert_item_price(item_code: str, price_list: str, rate: float, buying_selling: str, company: str = ""):
    """Create or update Item Price.

    SEC-M07: Valida que Price List exista para la company antes de insertar
    para evitar prices huérfanos referenciando Price Lists inexistentes.
    """
    # Validar Price List existe para esta company (si se proporciona company)
    if company:
        pl_exists = frappe.db.exists("Price List", {"name": price_list, "company": company})
        if not pl_exists:
            # Fallback: Price List global (sin company) o Standard
            pl_global = frappe.db.exists("Price List", {"name": price_list, "company": ["in", ["", None]]})
            if not pl_global:
                frappe.throw(
                    _("Price List '{0}' no existe para Company '{1}' ni globalmente").format(price_list, company)
                )

    existing = frappe.db.get_value(
        "Item Price",
        {"item_code": item_code, "price_list": price_list},
        "name"
    )
    if existing:
        price_doc = frappe.get_doc("Item Price", existing)
        price_doc.price_list_rate = rate
        price_doc.save()
    else:
        frappe.get_doc({
            "doctype": "Item Price",
            "item_code": item_code,
            "price_list": price_list,
            "price_list_rate": rate,
            "buying": 1 if buying_selling == "Buying" else 0,
            "selling": 1 if buying_selling == "Selling" else 0,
            "currency": "DOP",
        }).insert()


def _get_default_warehouse(company: str) -> str:
    """Get default warehouse for company (first Stores warehouse)."""
    warehouses = frappe.get_all(
        "Warehouse",
        filters={"company": company, "warehouse_name": ["like", "%Stores%"]},
        fields=["name"],
        limit=1,
    )
    if warehouses:
        return warehouses[0].name

    # Fallback: any warehouse for company
    warehouses = frappe.get_all(
        "Warehouse",
        filters={"company": company},
        fields=["name"],
        limit=1,
    )
    if warehouses:
        return warehouses[0].name

    frappe.throw(_("No hay almacén configurado para la Company {0}").format(company))


__all__ = [
    "_upsert_item_price",
    "_get_default_warehouse",
]