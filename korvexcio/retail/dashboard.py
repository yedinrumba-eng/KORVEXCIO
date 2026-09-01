"""Server-backed consolidated owner dashboard."""

from __future__ import annotations

import frappe

from korvexcio.ecf.report.ecf_pendientes.ecf_pendientes import execute as pending_ecf
from korvexcio.retail.reports import daily_sales, expiring_stock


@frappe.whitelist()
def get_dashboard_data() -> dict[str, object]:
    """Return dashboard data only for the logged-in owner's permitted Companies."""
    if not frappe.has_role("Dueño"):
        frappe.throw("Only Dueño can open the consolidated dashboard", frappe.PermissionError)
    companies = [
        row.for_value
        for row in frappe.get_all(
            "User Permission",
            filters={"user": frappe.session.user, "allow": "Company", "for_value": ["is", "set"]},
            fields=["for_value"],
        )
    ]
    if not companies:
        return {"companies": [], "sales": {}, "expiring_stock": [], "pending_ecf": []}
    sales = {company: daily_sales(company) for company in companies}
    expiring = {company: expiring_stock(company) for company in companies}
    pending_rows = []
    for company in companies:
        _, rows = pending_ecf({"company": company})
        pending_rows.extend(rows)
    return {"companies": companies, "sales": sales, "expiring_stock": expiring, "pending_ecf": pending_rows}
