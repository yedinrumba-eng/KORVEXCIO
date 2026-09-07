"""CLI entry point for bulk import (S5.1).

FASE 4.8: Separado de bulk_import.py.
Contiene: ImportResult, bulk_import_cmd
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import frappe
from frappe import _

from .bulk_import_parser import parse_file
from .bulk_import_builder import create_item_with_variants


@dataclass
class ImportResult:
    """Resultado de la importación masiva."""
    creados: int = 0
    actualizados: int = 0
    errores: int = 0
    detalles: list[str] = None

    def __post_init__(self):
        if self.detalles is None:
            self.detalles = []

    def add_error(self, msg: str):
        self.errores += 1
        self.detalles.append(f"ERROR: {msg}")

    def add_created(self, item_code: str):
        self.creados += 1
        self.detalles.append(f"CREADO: {item_code}")

    def add_updated(self, item_code: str):
        self.actualizados += 1
        self.detalles.append(f"ACTUALIZADO: {item_code}")

    def resumen(self) -> str:
        return f"Importación: {self.creados} creados, {self.actualizados} actualizados, {self.errores} errores"


def bulk_import_cmd(
    file_content: str | bytes,
    filename: str,
    company: str | None = None,
) -> ImportResult:
    """Ejecuta importación masiva desde archivo.

    Args:
        file_content: Contenido del archivo (string o bytes)
        filename: Nombre del archivo (para detectar tipo)
        company: Company destino (opcional, se infiere si no se da)

    Returns:
        ImportResult con estadísticas
    """
    result = ImportResult()

    # Parsear archivo
    try:
        rows = parse_file(file_content, filename)
    except (ValueError, KeyError, TypeError, OSError, IOError) as e:
        result.add_error(f"Error parseando archivo: {e}")
        return result

    if not rows:
        result.add_error("Archivo vacío o sin datos válidos")
        return result

    # Determinar company si no se dio
    target_company = company
    if not target_company:
        # Intentar inferir de la primera fila
        for row in rows:
            if row.get("company"):
                target_company = row["company"]
                break

    if not target_company:
        result.add_error("No se pudo determinar Company. Especifique --company o incluya columna 'company' en el archivo.")
        return result

    # Validar company
    if not frappe.db.exists("Company", target_company):
        result.add_error(f"Company '{target_company}' no existe")
        return result

    # Procesar cada fila
    for row in rows:
        try:
            item_code, es_nuevo = create_item_with_variants(row, target_company)
            if es_nuevo:
                result.add_created(item_code)
            else:
                result.add_updated(item_code)
        except (ValueError, KeyError, TypeError, frappe.ValidationError, frappe.DoesNotExistError) as e:
            item_code = row.get("item_code", "desconocido")
            result.add_error(f"{item_code}: {e}")

    frappe.db.commit()
    return result


__all__ = [
    "ImportResult",
    "bulk_import_cmd",
]