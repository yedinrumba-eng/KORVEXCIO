"""Bulk catalog import from Excel/CSV for S5.1 — 500-1000 SKUs.

Creates Items with variants and Item Defaults per Company.
Idempotent: updates if exists (by item_code), no duplicates.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import frappe
from frappe import _
from openpyxl import load_workbook

from korvexcio.retail.site_config import is_vertical_enabled


# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)


# ──────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class ImportResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[dict[str, str]] = field(default_factory=list)

    def add_error(self, row_num: int, item_code: str, error: str):
        self.errors.append({"row": row_num, "item_code": item_code, "error": error})


@dataclass
class ItemRow:
    """Normalized row from Excel/CSV."""
    item_code: str
    item_name: str
    item_group: str
    stock_uom: str
    is_stock_item: int = 1
    company: str = ""
    warehouse: str = ""
    price_list: str = "Standard Selling"
    price_list_rate: float = 0.0
    valuation_rate: float = 0.0
    description: str = ""
    # Variant attributes (flattened: Sabor, Nicotina mg, Tamaño ml, Ohmiaje)
    variant_of: str = ""
    sabor: str = ""
    nicotina_mg: str = ""
    tamano_ml: str = ""
    ohmiaje: str = ""


# ──────────────────────────────────────────────────────────────────────────
# Excel/CSV parsing
# ──────────────────────────────────────────────────────────────────────────

def parse_excel(filepath: str, company: str) -> list[ItemRow]:
    """Parse Excel file (.xlsx) and return list of ItemRow objects."""
    path = Path(filepath)
    if not path.exists():
        frappe.throw(f"File not found: {filepath}")

    ext = path.suffix.lower()
    if ext == ".xlsx":
        return _parse_xlsx(filepath, company)
    elif ext == ".csv":
        return _parse_csv(filepath, company)
    else:
        frappe.throw(f"Unsupported file format: {ext}. Use .xlsx or .csv")


def _parse_xlsx(filepath: str, default_company: str) -> list[ItemRow]:
    wb = load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active
    if not ws:
        frappe.throw("Excel file has no active sheet")

    # Read header row
    headers = [str(cell.value).strip() if cell.value else "" for cell in next(ws.iter_rows(min_row=1, max_row=1))]
    headers_lower = [h.lower().replace(" ", "_").replace("-", "_") for h in headers]

    # Map expected columns to indices
    col_map = _build_column_map(headers_lower)

    rows: list[ItemRow] = []
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
        vals = [cell.value for cell in row]
        item_row = _row_to_itemrow(vals, col_map, row_idx, default_company)
        if item_row:
            rows.append(item_row)

    wb.close()
    logger.info(f"Parsed {len(rows)} rows from {filepath}")
    return rows


def _parse_csv(filepath: str, default_company: str) -> list[ItemRow]:
    rows: list[ItemRow] = []
    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader, [])
        headers_lower = [h.strip().lower().replace(" ", "_").replace("-", "_") for h in headers]
        col_map = _build_column_map(headers_lower)

        for row_idx, vals in enumerate(reader, start=2):
            item_row = _row_to_itemrow(vals, col_map, row_idx, default_company)
            if item_row:
                rows.append(item_row)

    logger.info(f"Parsed {len(rows)} rows from {filepath}")
    return rows


def _build_column_map(headers: list[str]) -> dict[str, int]:
    """Map expected column names to indices (case-insensitive, flexible)."""
    expected = {
        "item_code": ["item_code", "codigo", "code", "sku"],
        "item_name": ["item_name", "nombre", "name", "descripcion", "description"],
        "item_group": ["item_group", "grupo", "group", "categoria", "category"],
        "stock_uom": ["stock_uom", "uom", "unidad", "unidad_medida", "unit"],
        "is_stock_item": ["is_stock_item", "stock", "es_stock", "stock_item"],
        "company": ["company", "compania", "empresa"],
        "warehouse": ["warehouse", "almacen", "almacén", "store"],
        "price_list": ["price_list", "lista_precios", "price_list_name"],
        "price_list_rate": ["price_list_rate", "precio", "price", "rate", "venta"],
        "valuation_rate": ["valuation_rate", "costo", "cost", "valuation", "compra"],
        "description": ["description", "descripcion", "detalle", "notes"],
        "variant_of": ["variant_of", "template", "plantilla", "parent"],
        "sabor": ["sabor", "flavor", "sabor_nombre"],
        "nicotina_mg": ["nicotina_mg", "nicotina", "nicotine_mg", "nicotine", "mg"],
        "tamano_ml": ["tamano_ml", "tamaño_ml", "tamano", "tamaño", "size_ml", "ml"],
        "ohmiaje": ["ohmiaje", "ohmios", "resistencia", "ohm"],
    }

    col_map = {}
    for key, aliases in expected.items():
        for idx, header in enumerate(headers):
            if header in aliases:
                col_map[key] = idx
                break

    # Required columns check
    required = ["item_code", "item_name", "item_group", "stock_uom"]
    missing = [r for r in required if r not in col_map]
    if missing:
        frappe.throw(f"Missing required columns: {missing}. Found: {headers}")

    return col_map


def _get_val(vals: list, col_map: dict, key: str, default: Any = "") -> Any:
    idx = col_map.get(key)
    if idx is not None and idx < len(vals):
        val = vals[idx]
        return val if val is not None else default
    return default


def _row_to_itemrow(
    vals: list,
    col_map: dict,
    row_num: int,
    default_company: str,
) -> ItemRow | None:
    item_code = str(_get_val(vals, col_map, "item_code", "")).strip()
    if not item_code:
        logger.warning(f"Row {row_num}: empty item_code, skipping")
        return None

    return ItemRow(
        item_code=item_code,
        item_name=str(_get_val(vals, col_map, "item_name", item_code)).strip(),
        item_group=str(_get_val(vals, col_map, "item_group", "Products")).strip(),
        stock_uom=str(_get_val(vals, col_map, "stock_uom", "Nos")).strip(),
        is_stock_item=int(_get_val(vals, col_map, "is_stock_item", 1) or 0),
        company=str(_get_val(vals, col_map, "company", default_company)).strip(),
        warehouse=str(_get_val(vals, col_map, "warehouse", "")).strip(),
        price_list=str(_get_val(vals, col_map, "price_list", "Standard Selling")).strip(),
        price_list_rate=float(_get_val(vals, col_map, "price_list_rate", 0.0) or 0.0),
        valuation_rate=float(_get_val(vals, col_map, "valuation_rate", 0.0) or 0.0),
        description=str(_get_val(vals, col_map, "description", "")).strip(),
        variant_of=str(_get_val(vals, col_map, "variant_of", "")).strip(),
        sabor=str(_get_val(vals, col_map, "sabor", "")).strip(),
        nicotina_mg=str(_get_val(vals, col_map, "nicotina_mg", "")).strip(),
        tamano_ml=str(_get_val(vals, col_map, "tamano_ml", "")).strip(),
        ohmiaje=str(_get_val(vals, col_map, "ohmiaje", "")).strip(),
    )


# ──────────────────────────────────────────────────────────────────────────
# Item creation / update
# ──────────────────────────────────────────────────────────────────────────

def create_item_with_variants(item_row: ItemRow) -> tuple[str, bool]:
    """Create or update Item (template or variant). Returns (item_code, is_new)."""
    existing = frappe.db.exists("Item", item_row.item_code)
    if existing:
        item = frappe.get_doc("Item", item_code=item_row.item_code)
        _update_item(item, item_row)
        item.save()
        return item_row.item_code, False

    # New item
    if item_row.variant_of:
        # This is a variant
        return _create_variant(item_row)
    else:
        # This is a template (or standalone item)
        return _create_template(item_row)


def _create_template(item_row: ItemRow) -> tuple[str, bool]:
    """Create Item template (has_variants=1) or simple item."""
    from korvexcio.retail.item_attributes import _attribute_configs, _clean_text
    from korvexcio.retail.site_config import get_retail_config

    has_variants = bool(item_row.sabor or item_row.nicotina_mg or item_row.tamano_ml or item_row.ohmiaje)

    doc = frappe.get_doc({
        "doctype": "Item",
        "item_code": _clean_text(item_row.item_code, "item_code", 140),
        "item_name": _clean_text(item_row.item_name, "item_name", 140),
        "item_group": _clean_text(item_row.item_group, "item_group", 140),
        "stock_uom": _clean_text(item_row.stock_uom, "stock_uom", 140),
        "description": item_row.description,
        "is_stock_item": item_row.is_stock_item,
        "has_variants": 1 if has_variants else 0,
        "variant_based_on": "Item Attribute" if has_variants else "",
    })

    if has_variants:
        config = get_retail_config()
        attributes = _attribute_configs(config)
        attr_rows = []
        for attr in attributes:
            attr_name = _clean_text(attr.get("name"), "attribute name", 140)
            attr_rows.append({"attribute": attr_name})
        doc.set("attributes", attr_rows)

    doc.insert()
    logger.info(f"Created template: {doc.item_code}")
    return doc.item_code, True


def _create_variant(item_row: ItemRow) -> tuple[str, bool]:
    """Create variant using ERPNext's create_variant."""
    from erpnext.controllers.item_variant import create_variant
    from korvexcio.retail.item_attributes import _clean_text

    if not frappe.db.exists("Item", item_row.variant_of):
        frappe.throw(f"Template not found: {item_row.variant_of}")

    template = frappe.get_doc("Item", item_row.variant_of)

    # Build attributes dict for create_variant
    attributes = {}
    if item_row.sabor:
        attributes["Sabor"] = _clean_text(item_row.sabor, "Sabor", 140)
    if item_row.nicotina_mg:
        attributes["Nicotina mg"] = _clean_text(item_row.nicotina_mg, "Nicotina mg", 140)
    if item_row.tamano_ml:
        attributes["Tamaño ml"] = _clean_text(item_row.tamano_ml, "Tamaño ml", 140)
    if item_row.ohmiaje:
        attributes["Ohmiaje"] = _clean_text(item_row.ohmiaje, "Ohmiaje", 140)

    if not attributes:
        frappe.throw(f"Variant {item_row.item_code} has no attribute values")

    variant = create_variant(template.name, attributes)

    # Override generated item_code with our explicit one
    variant.item_code = _clean_text(item_row.item_code, "item_code", 140)
    variant.item_name = _clean_text(item_row.item_name, "item_name", 140)
    variant.description = item_row.description
    variant.is_stock_item = item_row.is_stock_item

    variant.insert()
    logger.info(f"Created variant: {variant.item_code}")
    return variant.item_code, True


def _update_item(item: frappe.model.document.Document, item_row: ItemRow):
    """Update existing Item with new data."""
    item.item_name = item_row.item_name
    item.item_group = item_row.item_group
    item.stock_uom = item_row.stock_uom
    item.description = item_row.description
    item.is_stock_item = item_row.is_stock_item
    logger.info(f"Updated item: {item.item_code}")


def create_item_defaults(item_code: str, item_row: ItemRow) -> tuple[int, int]:
    """Create or update Item Defaults for the item's company/warehouse.
    Returns (created_count, updated_count)."""
    if not item_row.company:
        return 0, 0

    company = item_row.company
    warehouse = item_row.warehouse or _get_default_warehouse(company)
    price_list = item_row.price_list

    created = updated = 0

    # 1. Default Warehouse (in Item Defaults table)
    existing_default = frappe.db.exists("Item Default", {"parent": item_code, "company": company})
    if existing_default:
        default_doc = frappe.get_doc("Item Default", existing_default)
        default_doc.default_warehouse = warehouse
        default_doc.default_price_list = price_list
        default_doc.save()
        updated += 1
    else:
        item_doc = frappe.get_doc("Item", item_code)
        item_doc.append("item_defaults", {
            "company": company,
            "default_warehouse": warehouse,
            "default_price_list": price_list,
            "default_supplier": "",
        })
        item_doc.save()
        created += 1

    # 2. Item Price (selling)
    if item_row.price_list_rate > 0:
        _upsert_item_price(item_code, price_list, item_row.price_list_rate, "Selling", company)

    # 3. Item Price (buying / valuation)
    if item_row.valuation_rate > 0:
        _upsert_item_price(item_code, "Standard Buying", item_row.valuation_rate, "Buying", company)

    return created, updated


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
        filters={"company": company, "warehouse_type": "Stores", "disabled": 0},
        fields=["name"],
        limit=1,
        order_by="name",
    )
    if warehouses:
        return warehouses[0].name
    # Fallback: any warehouse
    warehouses = frappe.get_all(
        "Warehouse",
        filters={"company": company, "disabled": 0},
        fields=["name"],
        limit=1,
        order_by="name",
    )
    return warehouses[0].name if warehouses else ""


# ──────────────────────────────────────────────────────────────────────────
# Main import function
# ──────────────────────────────────────────────────────────────────────────

def execute_import(filepath: str, company: str = "") -> ImportResult:
    """Main import function — idempotent, company-filtered."""
    if not is_vertical_enabled():
        frappe.throw("Retail vertical is disabled for this site")

    if not company:
        companies = frappe.get_all("Company", pluck="name")
        if len(companies) == 1:
            company = companies[0]
        else:
            frappe.throw("Multiple companies exist — specify --company")

    logger.info(f"Starting import from {filepath} for company {company}")
    result = ImportResult()

    rows = parse_excel(filepath, company)

    # Group rows by variant_of to handle templates first
    templates: list[ItemRow] = []
    variants: list[ItemRow] = []
    for row in rows:
        if row.variant_of:
            variants.append(row)
        else:
            templates.append(row)

    # Process templates first
    for idx, row in enumerate(templates, 1):
        try:
            logger.info(f"[{idx}/{len(templates)}] Processing template: {row.item_code}")
            item_code, is_new = create_item_with_variants(row)
            if is_new:
                result.created += 1
            else:
                result.updated += 1

            # Create item defaults for template
            c, u = create_item_defaults(item_code, row)
            result.created += c
            result.updated += u

        except Exception as e:
            result.add_error(idx, row.item_code, str(e))
            logger.exception(f"Error processing template {row.item_code}")

    # Then process variants
    for idx, row in enumerate(variants, 1):
        try:
            logger.info(f"[{idx}/{len(variants)}] Processing variant: {row.item_code}")
            item_code, is_new = create_item_with_variants(row)
            if is_new:
                result.created += 1
            else:
                result.updated += 1

            # Create item defaults for variant
            c, u = create_item_defaults(item_code, row)
            result.created += c
            result.updated += u

        except Exception as e:
            result.add_error(len(templates) + idx, row.item_code, str(e))
            logger.exception(f"Error processing variant {row.item_code}")

    frappe.db.commit()
    _log_summary(result, company)
    return result


def _log_summary(result: ImportResult, company: str):
    logger.info("=" * 50)
    logger.info(f"IMPORT SUMMARY — Company: {company}")
    logger.info(f"  Items created:  {result.created}")
    logger.info(f"  Items updated:  {result.updated}")
    logger.info(f"  Items skipped:  {result.skipped}")
    logger.info(f"  Errors:         {len(result.errors)}")
    if result.errors:
        logger.error("ERRORS:")
        for err in result.errors:
            logger.error(f"  Row {err['row']} | {err['item_code']} | {err['error']}")
    logger.info("=" * 50)


# ──────────────────────────────────────────────────────────────────────────
# CLI entry point for `bench run-script`
# ──────────────────────────────────────────────────────────────────────────

def execute(filepath: str = "", company: str = ""):
    """CLI entry: bench --site <site> run-script korvexcio.retail.bulk_import --file <path> [--company <name>]"""
    if not filepath:
        frappe.throw("Usage: bench --site <site> run-script korvexcio.retail.bulk_import --file /path/to/catalog.xlsx [--company 'Company Name']")

    execute_import(filepath, company)
