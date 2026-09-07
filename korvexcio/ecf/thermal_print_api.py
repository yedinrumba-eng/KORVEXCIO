"""Thermal print API - Public entry points and shared constants.

FASE 4.8: Separado de thermal_print.py.
Este módulo contiene:
- Constantes por defecto
- _get_printer_constants()
- _format_currency(), _format_qty()
- Funciones de API pública: generate_thermal_receipt_html, generate_thermal_receipt_escpos, save_receipt_for_test
"""

from __future__ import annotations

import base64
import os
from typing import Any

import frappe

from korvexcio.ecf.thermal_receipt_builder import ThermalReceiptBuilder


# Default constants (used when no ECF Print Settings exists for company)
DEFAULT_PRINTER_WIDTH_DOTS = 576
DEFAULT_CHAR_WIDTH_DOTS = 12
DEFAULT_CHAR_HEIGHT_DOTS = 24
DEFAULT_MAX_CHARS_PER_LINE = DEFAULT_PRINTER_WIDTH_DOTS // DEFAULT_CHAR_WIDTH_DOTS  # 48 chars


def _get_printer_constants(company: str) -> dict:
    """Obtiene constantes de impresora desde ECF Print Settings o defaults.

    FASE 4.4: Constantes impresora en DocType ECF Print Settings / POS Profile.
    """
    if not company or not frappe.db.exists("ECF Print Settings", company):
        return {
            "width_dots": DEFAULT_PRINTER_WIDTH_DOTS,
            "char_width": DEFAULT_CHAR_WIDTH_DOTS,
            "char_height": DEFAULT_CHAR_HEIGHT_DOTS,
            "max_chars_per_line": DEFAULT_MAX_CHARS_PER_LINE,
            "qr_module_size": 4,
            "qr_error_correction": "M",
            "cut_paper": "Full cut (Guillotina)",
            "header_text": "",
            "footer_text": "¡Gracias por su compra!",
        }

    settings = frappe.get_doc("ECF Print Settings", company)
    return settings.get_printer_constants()


def _format_currency(amount: float | int | None) -> str:
    """Format currency for Dominican Republic (DOP)."""
    if amount is None:
        return "0.00"
    return f"{float(amount):,.2f}"


def _format_qty(qty: float | int | None) -> str:
    """Format quantity without decimals if whole number."""
    if qty is None:
        return "0"
    q = float(qty)
    return str(int(q)) if q == int(q) else f"{q:.2f}"


def _get_ecf_data(invoice_name: str) -> dict[str, Any] | None:
    """Obtiene datos del ECF vinculado a una Sales Invoice.

    Helper centralizado para evitar duplicación entre
    generate_thermal_receipt_html y generate_thermal_receipt_escpos (FASE 4.5).

    Args:
        invoice_name: Nombre del Sales Invoice

    Returns:
        Dict con encf, qr_url, track_id, codigo_seguridad, estado o None si no hay ECF
    """
    ecf_name = frappe.get_all(
        "ECF",
        filters={"reference_doctype": "Sales Invoice", "reference_name": invoice_name},
        pluck="name",
        limit=1,
    )
    if not ecf_name:
        return None
    ecf_doc = frappe.get_doc("ECF", ecf_name[0])
    return {
        "encf": ecf_doc.encf,
        "qr_url": ecf_doc.qr_url,
        "track_id": ecf_doc.track_id,
        "codigo_seguridad": ecf_doc.codigo_seguridad,
        "estado": ecf_doc.estado,
    }


def generate_thermal_receipt_html(invoice_name: str) -> str:
    """Generate HTML thermal receipt for a Sales Invoice.

    This is the main entry point for the print queue system.
    Can be called from background job or directly for testing.

    Args:
        invoice_name: Name of the Sales Invoice document

    Returns:
        HTML string ready for browser printing
    """
    invoice = frappe.get_doc("Sales Invoice", invoice_name).as_dict()
    ecf = _get_ecf_data(invoice_name)

    builder = ThermalReceiptBuilder(invoice, ecf)
    return builder.build_html()


def generate_thermal_receipt_escpos(invoice_name: str) -> bytes:
    """Generate ESC/POS binary for a Sales Invoice.

    For direct thermal printer sending via serial/USB/Bluetooth.

    Args:
        invoice_name: Name of the Sales Invoice document

    Returns:
        ESC/POS command bytes
    """
    invoice = frappe.get_doc("Sales Invoice", invoice_name).as_dict()
    ecf = _get_ecf_data(invoice_name)

    builder = ThermalReceiptBuilder(invoice, ecf)
    return builder.build_escpos()


def save_receipt_for_test(invoice_name: str, output_dir: str = "/tmp/korvexcio_thermal_test") -> dict[str, str]:
    """Save both HTML and ESC/POS receipt for testing without hardware.

    Args:
        invoice_name: Name of the Sales Invoice
        output_dir: Directory to save test files

    Returns:
        Dict with paths to saved files
    """
    os.makedirs(output_dir, exist_ok=True)

    html = generate_thermal_receipt_html(invoice_name)
    escpos = generate_thermal_receipt_escpos(invoice_name)

    safe_name = invoice_name.replace("/", "_").replace("\\", "_")
    html_path = os.path.join(output_dir, f"{safe_name}.html")
    escpos_path = os.path.join(output_dir, f"{safe_name}.escpos")
    escpos_b64_path = os.path.join(output_dir, f"{safe_name}.escpos.b64")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    with open(escpos_path, "wb") as f:
        f.write(escpos)

    with open(escpos_b64_path, "w") as f:
        f.write(base64.b64encode(escpos).decode())

    return {
        "html": html_path,
        "escpos": escpos_path,
        "escpos_b64": escpos_b64_path,
    }


__all__ = [
    # Constants
    "DEFAULT_PRINTER_WIDTH_DOTS",
    "DEFAULT_CHAR_WIDTH_DOTS",
    "DEFAULT_CHAR_HEIGHT_DOTS",
    "DEFAULT_MAX_CHARS_PER_LINE",
    # Internal helpers
    "_get_printer_constants",
    "_format_currency",
    "_format_qty",
    "_get_ecf_data",
    # Public API
    "generate_thermal_receipt_html",
    "generate_thermal_receipt_escpos",
    "save_receipt_for_test",
    # Re-export builder
    "ThermalReceiptBuilder",
]