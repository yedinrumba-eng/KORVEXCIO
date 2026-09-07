"""Item creation and variant building for bulk import (S5.1).

FASE 4.8: Separado de bulk_import.py.
Contiene: create_item_with_variants, _create_variant, _create_template
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from .bulk_import_defaults import _upsert_item_price, _get_default_warehouse


def _create_template(item_row: Any, company: str) -> str:
    """Crea el Item template (parent) si no existe.

    Args:
        item_row: Objeto con datos del item (puede ser dict o namedtuple)
        company: Company para Item Default

    Returns:
        item_code del template creado
    """
    item_code = getattr(item_row, "item_code", None) or item_row.get("item_code")
    item_name = getattr(item_row, "item_name", None) or item_row.get("item_name")
    item_group = getattr(item_row, "item_group", None) or item_row.get("item_group")

    # Verificar si ya existe
    if frappe.db.exists("Item", item_code):
        return item_code

    # Determinar si tiene variantes
    has_variants = any([
        getattr(item_row, "sabor", None) or item_row.get("sabor"),
        getattr(item_row, "nicotina_mg", None) or item_row.get("nicotina_mg"),
        getattr(item_row, "tamano_ml", None) or item_row.get("tamano_ml"),
        getattr(item_row, "ohmiaje", None) or item_row.get("ohmiaje"),
    ])

    template = frappe.get_doc({
        "doctype": "Item",
        "item_code": item_code,
        "item_name": item_name,
        "item_group": item_group,
        "stock_uom": "Unidad",
        "is_stock_item": 1,
        "has_variants": 1 if has_variants else 0,
        "variant_based_on": "Item Attribute" if has_variants else "",
        "valuation_rate": float(getattr(item_row, "valuation_rate", 0) or item_row.get("valuation_rate", 0) or 0),
    })

    # Agregar atributos de variante si tiene
    if has_variants:
        if getattr(item_row, "sabor", None) or item_row.get("sabor"):
            template.append("attributes", {"attribute": "Sabor"})
        if getattr(item_row, "nicotina_mg", None) or item_row.get("nicotina_mg"):
            template.append("attributes", {"attribute": "Nicotina mg"})
        if getattr(item_row, "tamano_ml", None) or item_row.get("tamano_ml"):
            template.append("attributes", {"attribute": "Tamaño ml"})
        if getattr(item_row, "ohmiaje", None) or item_row.get("ohmiaje"):
            template.append("attributes", {"attribute": "Ohmiaje"})

    template.insert()
    _create_item_defaults(template.name, company)
    return template.name


def _create_variant(template_name: str, item_row: Any, company: str) -> str:
    """Crea una variante del template.

    Args:
        template_name: Nombre del template (item_code)
        item_row: Datos del item con atributos de variante
        company: Company para Item Default

    Returns:
        item_code de la variante creada
    """
    from erpnext.controllers.item_variant import create_variant

    # Construir args de variante
    args = {}
    if getattr(item_row, "sabor", None) or item_row.get("sabor"):
        args["Sabor"] = getattr(item_row, "sabor", None) or item_row.get("sabor")
    if getattr(item_row, "nicotina_mg", None) or item_row.get("nicotina_mg"):
        args["Nicotina mg"] = str(getattr(item_row, "nicotina_mg", None) or item_row.get("nicotina_mg"))
    if getattr(item_row, "tamano_ml", None) or item_row.get("tamano_ml"):
        args["Tamaño ml"] = str(getattr(item_row, "tamano_ml", None) or item_row.get("tamano_ml"))
    if getattr(item_row, "ohmiaje", None) or item_row.get("ohmiaje"):
        args["Ohmiaje"] = str(getattr(item_row, "ohmiaje", None) or item_row.get("ohmiaje"))

    if not args:
        # No hay atributos de variante, usar template como item único
        return template_name

    # create_variant genera item_code automático; luego lo sobreescribimos
    variant = create_variant(template_name, args=args)
    variant_doc = frappe.get_doc("Item", variant)

    # Sobreescribir item_code con uno basado en atributos
    variant_code_parts = [template_name]
    if "Sabor" in args:
        variant_code_parts.append(str(args["Sabor"]).upper()[:3])
    if "Nicotina mg" in args:
        variant_code_parts.append(f"{args['Nicotina mg']}mg")
    if "Tamaño ml" in args:
        variant_code_parts.append(f"{args['Tamaño ml']}ml")
    if "Ohmiaje" in args:
        variant_code_parts.append(f"{args['Ohmiaje']}ohm")

    new_item_code = "-".join(variant_code_parts)

    # Verificar si ya existe con ese código
    if frappe.db.exists("Item", new_item_code):
        # Si existe, actualizar el existente
        existing = frappe.get_doc("Item", new_item_code)
        # Actualizar campos si cambió algo
        existing.valuation_rate = float(getattr(item_row, "valuation_rate", 0) or item_row.get("valuation_rate", 0) or 0)
        existing.save()
        _create_item_defaults(new_item_code, company)
        return new_item_code

    variant_doc.item_code = new_item_code
    variant_doc.item_name = f"{variant_doc.item_name} ({', '.join(args.values())})"
    variant_doc.valuation_rate = float(getattr(item_row, "valuation_rate", 0) or item_row.get("valuation_rate", 0) or 0)
    variant_doc.save()

    _create_item_defaults(new_item_code, company)
    return new_item_code


def _create_item_defaults(item_code: str, company: str) -> None:
    """Crea Item Default + Item Price para una Company.

    Args:
        item_code: Código del item
        company: Company
    """
    warehouse = _get_default_warehouse(company)

    # Item Default
    if not frappe.db.exists("Item Default", {"parent": item_code, "company": company}):
        frappe.get_doc({
            "doctype": "Item Default",
            "parent": item_code,
            "parenttype": "Item",
            "parentfield": "item_defaults",
            "company": company,
            "default_warehouse": warehouse,
            "default_price_list": "Standard Selling",
            "default_buying_price_list": "Standard Buying",
        }).insert()

    # Item Price (Selling)
    standard_rate = frappe.db.get_value("Item", item_code, "standard_rate") or 0
    if standard_rate:
        _upsert_item_price(item_code, "Standard Selling", standard_rate, "Selling", company)

    # Item Price (Buying) - valuation_rate
    valuation_rate = frappe.db.get_value("Item", item_code, "valuation_rate") or 0
    if valuation_rate:
        _upsert_item_price(item_code, "Standard Buying", valuation_rate, "Buying", company)


def create_item_with_variants(item_row: Any, company: str) -> tuple[str, bool]:
    """Crea item (template + variantes) o item único desde fila de importación.

    Args:
        item_row: Datos del item (dict o namedtuple)
        company: Company destino

    Returns:
        Tuple (item_code_principal, es_nuevo_template)
    """
    item_code = getattr(item_row, "item_code", None) or item_row.get("item_code")

    # Verificar si ya existe
    if frappe.db.exists("Item", item_code):
        # Actualizar si es template con variantes nuevas
        existing = frappe.get_doc("Item", item_code)
        if existing.has_variants:
            # Podría tener nuevas variantes - delegar a lógica de variante
            variant_code = _create_variant(item_code, item_row, company)
            return (variant_code, False)
        return (item_code, False)

    # Crear template
    template_name = _create_template(item_row, company)

    # Si tiene atributos de variante, crear la variante específica
    has_attrs = any([
        getattr(item_row, "sabor", None) or item_row.get("sabor"),
        getattr(item_row, "nicotina_mg", None) or item_row.get("nicotina_mg"),
        getattr(item_row, "tamano_ml", None) or item_row.get("tamano_ml"),
        getattr(item_row, "ohmiaje", None) or item_row.get("ohmiaje"),
    ])

    if has_attrs:
        variant_code = _create_variant(template_name, item_row, company)
        return (variant_code, True)

    return (template_name, True)


__all__ = [
    "create_item_with_variants",
    "_create_template",
    "_create_variant",
    "_create_item_defaults",
]