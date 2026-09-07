"""Test helpers for thermal printing (development only).

FASE 4.8: Separado de thermal_print.py.
Contiene _dev_test_thermal_print() - función helper para testing manual en desarrollo.
NO es un test automatizado - no hereda de IntegrationTestCase, no usa assertions.
Los tests reales están en test_thermal_print.py (14 tests de integración).
"""

from __future__ import annotations

from typing import Any

import frappe


def _dev_test_thermal_print() -> dict[str, Any]:
    """Función helper para testing manual en desarrollo (NO es test automatizado).

    SEC-L02: Eliminado como test real - no hereda de IntegrationTestCase,
    devuelve dict, no usa assertions. Los tests reales están en
    test_thermal_print.py (14 tests de integración).
    """
    test_company = "_Test Company KORVEXCIO A"
    if not frappe.db.exists("Company", test_company):
        return {"error": "Test company not found. Run before_tests first."}

    # Find a submitted test invoice
    test_invoice = frappe.get_all(
        "Sales Invoice",
        filters={"company": test_company, "docstatus": 1},
        pluck="name",
        limit=1,
    )

    if not test_invoice:
        return {"error": "No submitted test invoice found"}

    from korvexcio.ecf.thermal_print_api import save_receipt_for_test

    result = save_receipt_for_test(test_invoice[0])
    result["invoice"] = test_invoice[0]
    return result


__all__ = ["_dev_test_thermal_print"]