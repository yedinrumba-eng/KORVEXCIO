"""Print queue for thermal receipts - offline (IndexedDB) + online (S4.4).

Integrates with POSNext's offline queue system. When online, prints directly.
When offline, queues to IndexedDB for later printing.
"""

from __future__ import annotations

import json
import time
from typing import Any

import frappe


# Print queue DocType for server-side persistence (optional, for multi-device)
PRINT_QUEUE_DOCTYPE = "ECF Print Queue"


def _get_print_queue_doctype() -> str:
    """Get or create the print queue DocType."""
    return PRINT_QUEUE_DOCTYPE


def queue_print_job(invoice_name: str, company: str, priority: int = 1) -> str:
    """Queue a print job for an invoice.

    Creates a server-side print queue record for persistence across devices
    and for the background worker to pick up.

    Args:
        invoice_name: Sales Invoice name
        company: Company name (for multi-tenant isolation)
        priority: 1=high (immediate), 5=normal, 10=low

    Returns:
        Print queue record name
    """
    # Check if already queued
    existing = frappe.get_all(
        PRINT_QUEUE_DOCTYPE,
        filters={"invoice_name": invoice_name, "status": ["in", ["Pending", "Printing"]]},
        pluck="name",
        limit=1,
    )
    if existing:
        return existing[0]

    queue_doc = frappe.get_doc({
        "doctype": PRINT_QUEUE_DOCTYPE,
        "invoice_name": invoice_name,
        "company": company,
        "status": "Pending",
        "priority": priority,
        "attempts": 0,
        "created_at": frappe.utils.now(),
    })
    queue_doc.insert(ignore_permissions=True)
    return queue_doc.name


def process_print_queue(limit: int = 10) -> dict[str, int]:
    """Process pending print jobs (called by background worker).

    Args:
        limit: Max jobs to process per run

    Returns:
        Dict with processed, failed, skipped counts
    """
    pending = frappe.get_all(
        PRINT_QUEUE_DOCTYPE,
        filters={"status": "Pending"},
        fields=["name", "invoice_name", "company", "priority", "attempts"],
        order_by="priority asc, creation asc",
        limit=limit,
    )

    result = {"processed": 0, "failed": 0, "skipped": 0}

    for job in pending:
        try:
            # Mark as printing
            frappe.db.set_value(PRINT_QUEUE_DOCTYPE, job.name, "status", "Printing")
            frappe.db.set_value(PRINT_QUEUE_DOCTYPE, job.name, "attempts", job.attempts + 1)
            frappe.db.commit()

            # Generate and send to printer
            from korvexcio.ecf.thermal_print import generate_thermal_receipt_escpos
            escpos_data = generate_thermal_receipt_escpos(job.invoice_name)

            # Send to printer (implementation depends on printer setup)
            _send_to_printer(escpos_data, job.company)

            # Mark complete
            frappe.db.set_value(PRINT_QUEUE_DOCTYPE, job.name, "status", "Completed")
            frappe.db.set_value(PRINT_QUEUE_DOCTYPE, job.name, "completed_at", frappe.utils.now())
            frappe.db.commit()

            result["processed"] += 1

        except Exception as e:
            frappe.log_error(f"Print queue error for {job.invoice_name}: {e}")
            new_attempts = job.attempts + 1
            if new_attempts >= 3:
                frappe.db.set_value(PRINT_QUEUE_DOCTYPE, job.name, "status", "Failed")
                frappe.db.set_value(PRINT_QUEUE_DOCTYPE, job.name, "error_message", str(e)[:500])
            else:
                frappe.db.set_value(PRINT_QUEUE_DOCTYPE, job.name, "status", "Pending")
            frappe.db.commit()
            result["failed"] += 1

    return result


def _send_to_printer(escpos_data: bytes, company: str) -> None:
    """Send ESC/POS data to thermal printer.

    In production, this connects to a local print server (e.g., via CUPS,
    network printer, or USB/serial). For development, saves to file.

    Args:
        escpos_data: ESC/POS command bytes
        company: Company for printer config lookup
    """
    # Check for printer configuration
    printer_config = frappe.get_value("POS Profile", {"company": company}, ["printer_port", "printer_baudrate"], as_dict=True)

    if printer_config and printer_config.get("printer_port"):
        # Production: send to actual printer
        # Could use pyserial for USB/Serial, or socket for network printer
        import serial
        with serial.Serial(printer_config.printer_port, printer_config.printer_baudrate or 9600, timeout=2) as ser:
            ser.write(escpos_data)
    else:
        # Development: save to file for inspection
        import os
        test_dir = "/tmp/korvexcio_print_jobs"
        os.makedirs(test_dir, exist_ok=True)
        filename = f"print_{company}_{int(time.time())}.escpos"
        filepath = os.path.join(test_dir, filename)
        with open(filepath, "wb") as f:
            f.write(escpos_data)
        frappe.logger().info(f"Development: Saved print job to {filepath}")


def get_pending_print_count(company: str | None = None) -> int:
    """Get count of pending print jobs for a company.

    Args:
        company: Filter by company, or None for all

    Returns:
        Count of pending jobs
    """
    filters = {"status": "Pending"}
    if company:
        filters["company"] = company
    return frappe.db.count(PRINT_QUEUE_DOCTYPE, filters=filters)


def requeue_failed_prints(company: str | None = None) -> int:
    """Requeue failed print jobs for retry.

    Args:
        company: Filter by company, or None for all

    Returns:
        Number of jobs requeued
    """
    filters = {"status": "Failed"}
    if company:
        filters["company"] = company

    failed = frappe.get_all(PRINT_QUEUE_DOCTYPE, filters=filters, pluck="name")
    for name in failed:
        frappe.db.set_value(PRINT_QUEUE_DOCTYPE, name, "status", "Pending")
        frappe.db.set_value(PRINT_QUEUE_DOCTYPE, name, "attempts", 0)
        frappe.db.set_value(PRINT_QUEUE_DOCTYPE, name, "error_message", "")

    frappe.db.commit()
    return len(failed)


# Client-side (POSNext) integration - JavaScript module
# This would be exposed via a Frappe whitelisted method for the POS to call

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