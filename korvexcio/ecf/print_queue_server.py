"""Server-side print queue processing (S4.4).

FASE 4.8: Separado de print_queue.py.
Contiene: queue_print_job, process_print_queue, get_pending_print_count, requeue_failed_prints, _send_to_printer
"""

from __future__ import annotations

import json
import time
from typing import Any

import frappe


# Print queue DocType for server-side persistence
PRINT_QUEUE_DOCTYPE = "ECF Print Queue"


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
            from korvexcio.ecf.thermal_print_api import generate_thermal_receipt_escpos
            escpos_data = generate_thermal_receipt_escpos(job.invoice_name)

            # Send to printer
            _send_to_printer(escpos_data, job.company)

            # Mark complete
            frappe.db.set_value(PRINT_QUEUE_DOCTYPE, job.name, "status", "Completed")
            frappe.db.set_value(PRINT_QUEUE_DOCTYPE, job.name, "completed_at", frappe.utils.now())
            frappe.db.commit()

            result["processed"] += 1

        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
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
        try:
            with serial.Serial(printer_config.printer_port, printer_config.printer_baudrate or 9600, timeout=2) as ser:
                ser.write(escpos_data)
        except (serial.SerialException, OSError, TimeoutError) as e:
            frappe.log_error(f"Printer error for {company}: {e}")
            raise
    else:
        # Development: save to file for inspection
        import os
        test_dir = "/tmp/korvexcio_print_jobs"
        os.makedirs(test_dir, exist_ok=True)
        filename = f"print_{company}_{int(time.time())}.escpos"
        filepath = os.path.join(test_dir, filename)
        try:
            with open(filepath, "wb") as f:
                f.write(escpos_data)
            frappe.logger().info(f"Development: Saved print job to {filepath}")
        except (OSError, IOError) as e:
            frappe.log_error(f"Failed to save print job for {company}: {e}")
            raise


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