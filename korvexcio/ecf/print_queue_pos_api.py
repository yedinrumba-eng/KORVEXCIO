"""POS API for print queue (S4.4).

FASE 4.8: Separado de print_queue.py.
Contiene: pos_queue_print, pos_get_print_status, pos_sync_offline_prints
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from .print_queue_server import PRINT_QUEUE_DOCTYPE, queue_print_job


@frappe.whitelist()
def pos_queue_print(invoice_name: str) -> dict[str, Any]:
    """API endpoint for POS to queue a print job.

    Called from POSNext when a sale is completed.
    Returns the queue status immediately.

    Args:
        invoice_name: Sales Invoice name

    Returns:
        Dict with queue info
    """
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    company = invoice.company

    # Verify user has access to this company's data
    if not frappe.has_permission("Sales Invoice", "read", invoice):
        frappe.throw("No permission to print this invoice")

    queue_name = queue_print_job(invoice_name, company)

    return {
        "success": True,
        "queue_name": queue_name,
        "invoice_name": invoice_name,
        "status": "queued",
    }


@frappe.whitelist()
def pos_get_print_status(invoice_name: str) -> dict[str, Any]:
    """Get print status for an invoice (for POS polling).

    Args:
        invoice_name: Sales Invoice name

    Returns:
        Status dict
    """
    queue = frappe.get_all(
        PRINT_QUEUE_DOCTYPE,
        filters={"invoice_name": invoice_name},
        fields=["name", "status", "attempts", "error_message", "created_at", "completed_at"],
        order_by="creation desc",
        limit=1,
    )

    if not queue:
        return {"status": "not_queued"}

    job = queue[0]
    return {
        "status": job.status.lower(),
        "attempts": job.attempts,
        "error": job.error_message,
        "queued_at": job.created_at,
        "completed_at": job.completed_at,
    }


# Offline queue sync (called when POS comes back online)
@frappe.whitelist()
def pos_sync_offline_prints(offline_prints: str) -> dict[str, Any]:
    """Sync offline print queue from POS when connection restored.

    Args:
        offline_prints: JSON string of offline print records

    Returns:
        Sync result
    """
    try:
        prints = json.loads(offline_prints)
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON"}

    synced = 0
    errors = []

    for print_record in prints:
        try:
            invoice_name = print_record.get("invoice_name")
            if not invoice_name:
                continue

            # Check if already processed
            existing = frappe.get_all(
                PRINT_QUEUE_DOCTYPE,
                filters={"invoice_name": invoice_name, "status": "Completed"},
                pluck="name",
                limit=1,
            )
            if existing:
                synced += 1
                continue

            # Queue for printing
            company = print_record.get("company") or frappe.get_value("Sales Invoice", invoice_name, "company")
            if company:
                queue_print_job(invoice_name, company)
                synced += 1

        except Exception as e:
            errors.append({"invoice": print_record.get("invoice_name"), "error": str(e)})

    return {"success": True, "synced": synced, "errors": errors}