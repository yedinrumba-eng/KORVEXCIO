"""Thermal print utilities for 80mm receipts with e-CF QR code (S4.4).

FASE 4.8: Este archivo ahora es solo un re-export del módulo dividido.
Los módulos reales están en:
- thermal_receipt_builder.py: ThermalReceiptBuilder class + building logic
- thermal_print_api.py: Public API + constants + helpers
- test_helpers.py: Development helpers
"""

from __future__ import annotations

from .thermal_receipt_builder import ThermalReceiptBuilder
from .thermal_print_api import (
    DEFAULT_PRINTER_WIDTH_DOTS,
    DEFAULT_CHAR_WIDTH_DOTS,
    DEFAULT_CHAR_HEIGHT_DOTS,
    DEFAULT_MAX_CHARS_PER_LINE,
    _get_printer_constants,
    _format_currency,
    _format_qty,
    _get_ecf_data,
    generate_thermal_receipt_html,
    generate_thermal_receipt_escpos,
    save_receipt_for_test,
)
from .test_helpers import _dev_test_thermal_print


__all__ = [
    # Thermal printing (re-exported from thermal_receipt_builder)
    "ThermalReceiptBuilder",
    # Public API (re-exported from thermal_print_api)
    "generate_thermal_receipt_html",
    "generate_thermal_receipt_escpos",
    "save_receipt_for_test",
    "DEFAULT_PRINTER_WIDTH_DOTS",
    "DEFAULT_CHAR_WIDTH_DOTS",
    "DEFAULT_CHAR_HEIGHT_DOTS",
    "DEFAULT_MAX_CHARS_PER_LINE",
    # Dev helper
    "_dev_test_thermal_print",
]