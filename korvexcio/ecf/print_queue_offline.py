"""Offline print queue utilities for POSNext IndexedDB sync.

FASE 4.8: Separado de print_queue.py.
Contiene utilidades para sincronización offline.
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from .print_queue_server import queue_print_job


def build_offline_queue_payload(company: str, max_items: int = 50) -> str:
    """Construye payload JSON para que el POS descargue su cola offline.

    Args:
        company: Company del POS
        max_items: Máximo items a incluir en el payload

    Returns:
        JSON string con print jobs pendientes
    """
    pending = frappe.get_all(
        "ECF Print Queue",
        filters={"company": company, "status": "Pending"},
        fields=["name", "invoice_name", "priority", "attempts", "created_at"],
        order_by="priority asc, creation asc",
        limit=max_items,
    )

    return json.dumps([
        {
            "queue_name": job.name,
            "invoice_name": job.invoice_name,
            "priority": job.priority,
            "attempts": job.attempts,
            "created_at": str(job.created_at),
        }
        for job in pending
    ])


def resolve_offline_conflicts(local_prints: list[dict], server_prints: list[dict]) -> dict[str, Any]:
    """Resuelve conflictos entre cola offline local y cola del servidor.

    Estrategia: server wins para jobs completados; merge para pendientes.

    Args:
        local_prints: Lista de print records del IndexedDB del POS
        server_prints: Lista de print records del servidor

    Returns:
        Dict con: to_print (lista de invoices a encolar), conflicts (lista de conflictos)
    """
    local_invoices = {p.get("invoice_name") for p in local_prints if p.get("invoice_name")}
    server_completed = {p.get("invoice_name") for p in server_prints if p.get("status") == "Completed"}

    to_print = []
    conflicts = []

    for print_record in local_prints:
        invoice_name = print_record.get("invoice_name")
        if not invoice_name:
            continue

        # Si ya completado en servidor, no re-imprimir
        if invoice_name in server_completed:
            conflicts.append({"invoice": invoice_name, "reason": "already_completed_on_server"})
            continue

        to_print.append(print_record)

    return {
        "to_print": to_print,
        "conflicts": conflicts,
    }


def sync_offline_to_server(offline_prints: str, company: str) -> dict[str, Any]:
    """Sincroniza cola offline del POS al servidor (versión simplificada).

    Wrapper sobre pos_sync_offline_prints con lógica de conflictos.

    Args:
        offline_prints: JSON string del POS
        company: Company para validación

    Returns:
        Resultado de sincronización
    """
    try:
        prints = json.loads(offline_prints)
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON"}

    # Obtener estado actual en servidor
    server_prints = frappe.get_all(
        "ECF Print Queue",
        filters={"company": company},
        fields=["invoice_name", "status"],
    )

    # Resolver conflictos
    resolution = resolve_offline_conflicts(prints, server_prints)

    synced = 0
    errors = []

    for print_record in resolution["to_print"]:
        try:
            invoice_name = print_record.get("invoice_name")
            if not invoice_name:
                continue

            queue_print_job(invoice_name, company)
            synced += 1

        except (frappe.DoesNotExistError, frappe.ValidationError, ValueError, KeyError) as e:
            errors.append({"invoice": print_record.get("invoice_name"), "error": str(e)})

    return {
        "success": True,
        "synced": synced,
        "conflicts": resolution["conflicts"],
        "errors": errors,
    }