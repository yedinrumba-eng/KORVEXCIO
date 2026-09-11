"""Script S5.2 — Inventario inicial por almacén (Stock Entry Material Receipt).

Idempotente: si ya existe un Stock Entry para el mismo item/warehouse/qty,
no lo duplica. Con rollback: si algo falla, cancela y borra lo que creó.

Uso:
    bench --site korvexcio.korvexdev.cc run korvexcio.retail.stock_initial.run

El origen de datos es un JSON o CSV con columnas:
    item_code, warehouse, qty, basic_rate (opcional, default 1)
"""

import json
import sys
from pathlib import Path
from typing import Any

import frappe
from frappe.utils import flt, nowdate

DEFAULT_SOURCE = "korvexcio/retail/data/initial_stock.json"


def get_source_path() -> Path:
    """Ruta del archivo origen. Permite override por CLI o ENV."""
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    import os
    env_path = os.environ.get("KORVEXCIO_STOCK_SOURCE")
    if env_path:
        return Path(env_path)
    return Path(__file__).parent / "data" / "initial_stock.json"


def load_source(path: Path) -> list[dict[str, Any]]:
    """Carga items desde JSON o CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Archivo origen no encontrado: {path}")

    if path.suffix.lower() == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        if isinstance(data, list):
            return data
        raise ValueError("JSON debe ser lista de objetos o dict con clave 'items'")

    if path.suffix.lower() == ".csv":
        import csv
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    raise ValueError(f"Formato no soportado: {path.suffix}. Use .json o .csv")


def validate_row(row: dict[str, Any], idx: int) -> dict[str, Any]:
    """Valida y normaliza una fila de origen."""
    item_code = row.get("item_code")
    warehouse = row.get("warehouse")
    qty = row.get("qty")
    basic_rate = row.get("basic_rate", 1)

    if not item_code:
        raise ValueError(f"Fila {idx}: 'item_code' requerido")
    if not warehouse:
        raise ValueError(f"Fila {idx}: 'warehouse' requerido")
    if qty is None or qty == "":
        raise ValueError(f"Fila {idx}: 'qty' requerido")

    qty = flt(qty)
    basic_rate = flt(basic_rate)

    if qty <= 0:
        raise ValueError(f"Fila {idx}: qty debe ser > 0 (recibido {qty})")
    if basic_rate < 0:
        raise ValueError(f"Fila {idx}: basic_rate no puede ser negativo")

    if not frappe.db.exists("Item", item_code):
        raise ValueError(f"Fila {idx}: Item '{item_code}' no existe")
    if not frappe.db.exists("Warehouse", warehouse):
        raise ValueError(f"Fila {idx}: Warehouse '{warehouse}' no existe")

    # Verificar que el warehouse pertenece a una company válida
    company = frappe.db.get_value("Warehouse", warehouse, "company")
    if not company:
        raise ValueError(f"Fila {idx}: Warehouse '{warehouse}' sin company asignada")

    return {
        "item_code": item_code,
        "warehouse": warehouse,
        "qty": qty,
        "basic_rate": basic_rate,
        "company": company,
    }


def stock_entry_exists(item_code: str, warehouse: str, qty: float, company: str) -> str | None:
    """Verifica si ya existe un Stock Entry Material Receipt idéntico (idempotencia).

    Busca por item_code + warehouse + qty + company en Stock Entry Items
    de tipo 'Material Receipt' ya sometidos. Usa el ORM de Frappe (regla 10:
    nada de frappe.db.sql() crudo — filtra por company explícitamente).
    """
    matching_items = frappe.get_all(
        "Stock Entry Item",
        filters={
            "item_code": item_code,
            "t_warehouse": warehouse,
            "qty": qty,
        },
        pluck="parent",
    )
    if not matching_items:
        return None

    entries = frappe.get_all(
        "Stock Entry",
        filters={
            "name": ["in", matching_items],
            "docstatus": 1,
            "stock_entry_type": "Material Receipt",
            "company": company,
        },
        pluck="name",
        limit=1,
    )
    return entries[0] if entries else None


def create_material_receipt(
    item_code: str, warehouse: str, qty: float, basic_rate: float, company: str
) -> str:
    """Crea y somete un Stock Entry Material Receipt para un item."""
    entry = frappe.get_doc(
        {
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "company": company,
            "posting_date": nowdate(),
            "posting_time": "00:00:00",
            "items": [
                {
                    "item_code": item_code,
                    "qty": qty,
                    "t_warehouse": warehouse,
                    "basic_rate": basic_rate,
                    "cost_center": frappe.db.get_value("Company", company, "cost_center"),
                }
            ],
            "remarks": f"Inventario inicial S5.2 - {item_code} @ {warehouse}",
        }
    )
    entry.insert()
    entry.submit()
    return entry.name


def cancel_and_delete_stock_entry(name: str) -> None:
    """Cancela y borra un Stock Entry (para rollback)."""
    doc = frappe.get_doc("Stock Entry", name)
    if doc.docstatus == 1:
        doc.cancel()
    frappe.delete_doc("Stock Entry", name, force=True, ignore_permissions=True)


def run(source_path: str | None = None) -> dict[str, Any]:
    """Ejecuta la carga de inventario inicial.

    Estrategia "valida todo → crea todo o nada" (opción C): primero se validan
    las N filas (sin tocar la DB) y se decide qué toca crear y qué saltar por
    idempotencia. Si cualquier fila es inválida, se aborta ANTES de crear nada.
    Si la creación falla a mitad, se revierte lo ya creado.

    Returns:
        dict con claves: created, skipped, details. Lanza ValueError/RuntimeError
        si hay fila inválida o si la creación falla (nunca queda carga parcial).
    """
    frappe.set_user("Administrator")

    path = Path(source_path) if source_path else get_source_path()
    rows = load_source(path)

    results: dict[str, Any] = {
        "created": [],
        "skipped": [],
        "details": [],
    }

    # Fase 1 — validar todo y clasificar. Ninguna escritura a la DB todavía.
    to_create: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, 1):
        try:
            validated = validate_row(row, idx)
        except ValueError as e:
            raise ValueError(f"Fila {idx}: {e}") from e

        existing = stock_entry_exists(
            validated["item_code"],
            validated["warehouse"],
            validated["qty"],
            validated["company"],
        )
        if existing:
            results["skipped"].append(existing)
            results["details"].append(
                {
                    "row": idx,
                    "item_code": validated["item_code"],
                    "warehouse": validated["warehouse"],
                    "qty": validated["qty"],
                    "status": "skipped",
                    "stock_entry": existing,
                    "reason": "Ya existe Stock Entry idéntico (idempotente)",
                }
            )
            continue

        to_create.append({"idx": idx, "validated": validated})

    # Fase 2 — crear todo. Si algo falla, rollback de lo ya creado.
    created_entries: list[str] = []
    try:
        for item in to_create:
            validated = item["validated"]
            idx = item["idx"]
            se_name = create_material_receipt(
                validated["item_code"],
                validated["warehouse"],
                validated["qty"],
                validated["basic_rate"],
                validated["company"],
            )
            created_entries.append(se_name)
            results["created"].append(se_name)
            results["details"].append(
                {
                    "row": idx,
                    "item_code": validated["item_code"],
                    "warehouse": validated["warehouse"],
                    "qty": validated["qty"],
                    "basic_rate": validated["basic_rate"],
                    "status": "created",
                    "stock_entry": se_name,
                }
            )
    except frappe.ValidationError as e:
        for se_name in created_entries:
            try:
                cancel_and_delete_stock_entry(se_name)
            except (frappe.DoesNotExistError, frappe.ValidationError):
                pass  # Best effort
        frappe.db.rollback()
        raise RuntimeError(f"Fallo en carga inicial, rollback ejecutado: {e}") from e

    if results["created"]:
        frappe.db.commit()

    return results


if __name__ == "__main__":
    # Permite ejecución directa: python stock_initial.py [archivo_origen]
    # except Exception es intencional aquí (entry point de CLI): capturar todo,
    # imprimir, salir con código de error. No es un except en lógica de negocio.
    try:
        res = run()
        print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:  # noqa: BLE001 — entry point, captura y sale limpio
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
