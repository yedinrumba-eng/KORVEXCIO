"""Opt-in counter-service cafe catalog and BOM helpers."""

from __future__ import annotations

from typing import Any

import frappe

from korvexcio.retail.site_config import get_retail_config, is_vertical_enabled


def sync_cafe_catalog() -> list[str]:
    """Create configured cafe Items and BOMs; do nothing when cafe is disabled."""
    config = get_retail_config()
    if not is_vertical_enabled() or config.get("cafe", {}).get("enabled") is not True:
        return []
    cafe = config.get("cafe", {})
    created: list[str] = []
    for product in cafe.get("products", []):
        finished = _ensure_item(product["item_code"], product["item_name"], product.get("item_group", "Products"))
        for ingredient in product.get("ingredients", []):
            _ensure_item(ingredient["item_code"], ingredient["item_name"], ingredient.get("item_group", "Raw Material"))
        bom_name = frappe.db.exists("BOM", {"item": finished, "is_active": 1, "is_default": 1})
        if not bom_name:
            bom = frappe.get_doc(
                {
                    "doctype": "BOM",
                    "item": finished,
                    "quantity": product.get("quantity", 1),
                    "is_active": 1,
                    "is_default": 1,
                    "items": [
                        {"item_code": ingredient["item_code"], "qty": ingredient["qty"]}
                        for ingredient in product.get("ingredients", [])
                    ],
                }
            ).insert()
            bom.submit()
        created.append(finished)
    frappe.db.commit()
    return created


def _ensure_item(item_code: str, item_name: str, item_group: str) -> str:
    if frappe.db.exists("Item", item_code):
        return item_code
    frappe.get_doc(
        {
            "doctype": "Item",
            "item_code": item_code,
            "item_name": item_name,
            "item_group": item_group,
            "stock_uom": "Nos",
            "is_stock_item": 1,
        }
    ).insert()
    return item_code
