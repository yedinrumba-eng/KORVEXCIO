"""Site-configured item attributes and ERPNext variants for retail."""

from __future__ import annotations

from typing import Any

import frappe

from korvexcio.retail.site_config import get_retail_config, is_vertical_enabled


def sync_item_attributes() -> list[str]:
    """Create configured Item Attributes without enabling anything by default."""
    if not is_vertical_enabled():
        return []

    created_or_updated: list[str] = []
    for config in _attribute_configs(get_retail_config()):
        name = _clean_text(config.get("name"), "attribute name", 140)
        values = config.get("values", [])
        is_numeric = config.get("numeric") is True
        if not isinstance(values, list) or (not is_numeric and not values):
            frappe.throw(f"Retail attribute {name} must define at least one value")

        attribute = frappe.db.exists("Item Attribute", name)
        doc = frappe.get_doc("Item Attribute", attribute) if attribute else frappe.new_doc("Item Attribute")
        doc.attribute_name = name
        doc.numeric_values = 1 if is_numeric else 0
        if is_numeric:
            doc.from_range = config.get("from_range", 0)
            doc.to_range = config.get("to_range", 100)
            doc.increment = config.get("increment", 1)
            doc.set("item_attribute_values", [])
        else:
            existing_values = {row.attribute_value for row in doc.item_attribute_values}
            for raw_value in values:
                value, abbr = _attribute_value(raw_value)
                if value not in existing_values:
                    doc.append("item_attribute_values", {"attribute_value": value, "abbr": abbr})
                    existing_values.add(value)

        if doc.is_new():
            doc.insert()
        else:
            doc.save()
        created_or_updated.append(doc.name)
    frappe.db.commit()
    return created_or_updated


def create_item_template_and_variants(
    template: dict[str, Any], variants: list[dict[str, str]]
) -> list[str]:
    """Create one Item template and standard ERPNext variants from config data."""
    if not is_vertical_enabled():
        frappe.throw("Retail vertical is disabled for this site")
    template_name = _clean_text(template.get("item_code"), "template item_code", 140)
    configured_attributes = _attribute_configs(get_retail_config())
    attribute_rows = [
        {"attribute": _clean_text(config.get("name"), "attribute name", 140)}
        for config in configured_attributes
    ]
    if frappe.db.exists("Item", template_name):
        item_template = frappe.get_doc("Item", template_name)
    else:
        item_template = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": template_name,
                "item_name": _clean_text(template.get("item_name"), "template item_name", 140),
                "item_group": _clean_text(template.get("item_group"), "template item_group", 140),
                "stock_uom": _clean_text(template.get("stock_uom"), "template stock_uom", 140),
                "is_stock_item": 0,
                "has_variants": 1,
                "variant_based_on": "Item Attribute",
                "attributes": attribute_rows,
            }
        ).insert()

    item_template.set("attributes", attribute_rows)
    item_template.save()

    from erpnext.controllers.item_variant import create_variant

    variant_names: list[str] = []
    for attributes in variants:
        if not isinstance(attributes, dict) or not attributes:
            frappe.throw("Each retail variant must be a non-empty attribute object")
        variant = create_variant(item_template.name, attributes)
        if not variant.item_code:
            frappe.throw("ERPNext did not generate an item code for the retail variant")
        if not frappe.db.exists("Item", variant.item_code):
            variant.insert()
        variant_names.append(variant.item_code)
    frappe.db.commit()
    return variant_names


def _attribute_configs(config: dict[str, Any]) -> list[dict[str, Any]]:
    attributes = config.get("attributes", [])
    if not isinstance(attributes, list):
        frappe.throw("korvexcio_retail.attributes must be a list")
    return [item for item in attributes if isinstance(item, dict)]


def _attribute_value(raw_value: Any) -> tuple[str, str]:
    if isinstance(raw_value, str):
        value = _clean_text(raw_value, "attribute value", 140)
        return value, value[:10]
    if isinstance(raw_value, dict):
        value = _clean_text(raw_value.get("value"), "attribute value", 140)
        abbr = _clean_text(raw_value.get("abbr", value[:10]), "attribute abbreviation", 10)
        return value, abbr
    frappe.throw("Retail attribute values must be strings or objects")


def _clean_text(value: Any, label: str, max_length: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > max_length:
        frappe.throw(f"Invalid {label}")
    return value.strip()
