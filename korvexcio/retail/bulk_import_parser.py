"""Excel/CSV parsing for bulk import (S5.1).

FASE 4.8: Separado de bulk_import.py.
Contiene: parse_excel, parse_csv, normalize_headers, validate_required_fields
"""

from __future__ import annotations

import csv
from io import BytesIO, StringIO
from typing import Any

import frappe
from frappe import _


# Aliases de columnas soportados (ES/EN)
COLUMN_ALIASES = {
    # Identificadores
    "item_code": ["item_code", "sku", "codigo", "código", "code"],
    "item_name": ["item_name", "nombre", "name", "producto", "product"],
    "item_group": ["item_group", "grupo", "grupo_item", "category", "categoria", "categoría"],

    # Variant attributes
    "variant_of": ["variant_of", "template", "plantilla", "base_item"],
    "sabor": ["sabor", "flavor", "sabor_nic", "sabor_nicotina"],
    "nicotina_mg": ["nicotina_mg", "nicotina", "nicotine", "nic_mg", "mg"],
    "tamano_ml": ["tamano_ml", "tamaño_ml", "size_ml", "ml", "capacidad"],
    "ohmiaje": ["ohmiaje", "ohm", "resistencia", "coil_ohm", "resistance"],

    # Pricing
    "standard_rate": ["standard_rate", "precio_venta", "price", "precio", "venta"],
    "valuation_rate": ["valuation_rate", "costo", "cost", "precio_costo", "costo_promedio"],

    # Stock
    "opening_qty": ["opening_qty", "stock_inicial", "qty_inicial", "initial_qty", "stock"],
    "warehouse": ["warehouse", "almacen", "almacén", "bodega"],

    # Company (opcional, se infiere si no viene)
    "company": ["company", "empresa", "compañía"],
}

# Columnas requeridas mínimas
REQUIRED_COLUMNS = ["item_code", "item_name", "item_group"]


def normalize_headers(headers: list[str]) -> dict[str, str]:
    """Normaliza headers de CSV/Excel a nombres internos estándar.

    Args:
        headers: Lista de headers del archivo

    Returns:
        Dict mapeando header_original -> nombre_interno
    """
    mapping = {}
    for header in headers:
        header_clean = header.strip().lower().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")

        for internal_name, aliases in COLUMN_ALIASES.items():
            if header_clean in [a.lower().replace(" ", "_") for a in aliases]:
                mapping[header] = internal_name
                break
        else:
            # No match: usar header limpio como nombre interno
            mapping[header] = header_clean

    return mapping


def validate_required_fields(row: dict[str, Any], row_num: int) -> list[str]:
    """Valida que una fila tenga las columnas requeridas.

    Args:
        row: Dict con datos de la fila
        row_num: Número de fila (para mensajes de error)

    Returns:
        Lista de errores (vacía si OK)
    """
    errors = []
    for col in REQUIRED_COLUMNS:
        if not row.get(col) or str(row[col]).strip() == "":
            errors.append(f"Fila {row_num}: columna requerida '{col}' vacía")
    return errors


def parse_excel(file_content: bytes) -> list[dict[str, Any]]:
    """Parsea archivo Excel (.xlsx/.xls) a lista de dicts.

    Args:
        file_content: Contenido binario del archivo

    Returns:
        Lista de dicts con datos normalizados
    """
    try:
        import openpyxl
    except ImportError:
        frappe.throw(_("openpyxl no está instalado. Necesario para leer archivos Excel."))

    workbook = openpyxl.load_workbook(BytesIO(file_content), read_only=True)
    sheet = workbook.active

    rows = []
    headers = None

    for row_num, row in enumerate(sheet.iter_rows(values_only=True), 1):
        if row_num == 1:
            headers = [str(cell).strip() if cell else f"col_{i}" for i, cell in enumerate(row)]
            header_map = normalize_headers(headers)
            continue

        # Saltar filas completamente vacías
        if all(cell is None or str(cell).strip() == "" for cell in row):
            continue

        row_data = {}
        for i, cell in enumerate(row):
            if i < len(headers):
                internal_name = header_map.get(headers[i], headers[i])
                row_data[internal_name] = cell if cell is not None else ""

        # Validar requeridos
        errors = validate_required_fields(row_data, row_num)
        if errors:
            frappe.log_error(f"Bulk import validation errors row {row_num}: {errors}")
            continue

        rows.append(row_data)

    workbook.close()
    return rows


def parse_csv(file_content: str | bytes) -> list[dict[str, Any]]:
    """Parsea archivo CSV a lista de dicts.

    Args:
        file_content: Contenido del archivo (string o bytes)

    Returns:
        Lista de dicts con datos normalizados
    """
    if isinstance(file_content, bytes):
        file_content = file_content.decode("utf-8")

    reader = csv.DictReader(StringIO(file_content))
    if not reader.fieldnames:
        return []

    header_map = normalize_headers(reader.fieldnames)

    rows = []
    for row_num, row in enumerate(reader, 2):  # empieza en 2 (1 = header)
        # Normalizar nombres de campos
        row_data = {}
        for header, value in row.items():
            internal_name = header_map.get(header, header)
            row_data[internal_name] = value.strip() if value else ""

        # Validar requeridos
        errors = validate_required_fields(row_data, row_num)
        if errors:
            frappe.log_error(f"Bulk import validation errors row {row_num}: {errors}")
            continue

        rows.append(row_data)

    return rows


def parse_file(file_content: str | bytes, filename: str) -> list[dict[str, Any]]:
    """Parsea archivo según extensión.

    Args:
        file_content: Contenido del archivo
        filename: Nombre del archivo (para detectar tipo)

    Returns:
        Lista de dicts con datos normalizados
    """
    filename_lower = filename.lower()
    if filename_lower.endswith((".xlsx", ".xls")):
        if isinstance(file_content, str):
            file_content = file_content.encode("utf-8")
        return parse_excel(file_content)
    elif filename_lower.endswith(".csv"):
        return parse_csv(file_content)
    else:
        frappe.throw(_("Formato de archivo no soportado: {0}. Use .xlsx, .xls o .csv").format(filename))


__all__ = [
    "normalize_headers",
    "validate_required_fields",
    "parse_excel",
    "parse_csv",
    "parse_file",
    "COLUMN_ALIASES",
    "REQUIRED_COLUMNS",
]