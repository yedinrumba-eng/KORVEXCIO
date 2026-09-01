"""Company-scoped data functions used by Retail reports and dashboard."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import today

_RD_TZ = ZoneInfo("America/Santo_Domingo")


def _rd_today() -> date:
    return datetime.now(tz=_RD_TZ).date()


def company_filter(filters: dict[str, Any]) -> str:
    """Real bug found by an isolation test, not by review (2026-09-01):
    every function below uses frappe.get_all(), which -- unlike
    frappe.get_list() -- IGNORES PERMISSIONS BY DEFAULT. The explicit
    `company` filter was never a real barrier: a Cajero restricted to
    Company A could just type Company B into the report's own filter and
    see B's real sales. Regla 12b exists for exactly this: never trust
    the ORM's own filtering, check explicitly. This is the one place
    every report and the dashboard funnel through, so the check lives
    here once, not duplicated four times."""
    company = filters.get("company")
    if not isinstance(company, str) or not company.strip():
        frappe.throw("Company is required")
    company = company.strip()
    _assert_user_may_view_company(company)
    return company


def _assert_user_may_view_company(company: str) -> None:
    if "System Manager" in frappe.get_roles():
        return
    allowed_companies = frappe.get_all(
        "User Permission",
        filters={"user": frappe.session.user, "allow": "Company"},
        pluck="for_value",
    )
    # Sin ninguna fila de User Permission sobre Company, el usuario no
    # esta acotado por diseno (p.ej. sesiones de servicio) -- no negar
    # por ausencia, solo cuando SI esta acotado a otra cosa distinta.
    if allowed_companies and company not in allowed_companies:
        frappe.throw(
            frappe._("No tienes acceso a los datos de {0}.").format(company),
            frappe.PermissionError,
        )


def sold_invoice_names(company: str, from_date: str | None = None) -> list[str]:
    filters: dict[str, Any] = {"company": company, "docstatus": 1}
    if from_date:
        filters["posting_date"] = [">=", from_date]
    return [row.name for row in frappe.get_all("Sales Invoice", filters=filters, fields=["name"])]


def daily_sales(company: str, target_date: str | None = None) -> dict[str, float]:
    _assert_user_may_view_company(company)
    posting_date = target_date or today()
    rows = frappe.get_all(
        "Sales Invoice",
        filters={"company": company, "docstatus": 1, "posting_date": posting_date},
        fields=["base_grand_total", "base_net_total"],
    )
    return {
        "invoice_count": len(rows),
        "gross_total": sum(float(row.base_grand_total or 0) for row in rows),
        "net_total": sum(float(row.base_net_total or 0) for row in rows),
    }


def stock_dead(company: str, days: int = 90) -> list[dict[str, Any]]:
    _assert_user_may_view_company(company)
    cutoff = (_rd_today() - timedelta(days=days)).isoformat()
    invoice_names = sold_invoice_names(company, cutoff)
    sold_codes = {
        row.item_code
        for row in frappe.get_all(
            "Sales Invoice Item",
            filters={"parent": ["in", invoice_names]} if invoice_names else {"name": "__none__"},
            fields=["item_code"],
        )
    }
    rows = frappe.get_all(
        "Bin",
        filters={"actual_qty": [">", 0]},
        fields=["item_code", "warehouse", "actual_qty", "valuation_rate"],
    )
    warehouses = {
        row.name
        for row in frappe.get_all("Warehouse", filters={"company": company}, fields=["name"])
    }
    return [row for row in rows if row.warehouse in warehouses and row.item_code not in sold_codes]


def margin_by_category(company: str, from_date: str | None = None) -> list[dict[str, Any]]:
    _assert_user_may_view_company(company)
    names = sold_invoice_names(company, from_date)
    if not names:
        return []
    rows = frappe.get_all(
        "Sales Invoice Item",
        filters={"parent": ["in", names]},
        fields=["item_code", "item_group", "amount", "stock_qty", "incoming_rate"],
    )
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        group = row.item_group or "Uncategorized"
        result = grouped.setdefault(group, {"item_group": group, "sales": 0.0, "cost": 0.0})
        result["sales"] += float(row.amount or 0)
        result["cost"] += float(row.stock_qty or 0) * float(row.incoming_rate or 0)
    for result in grouped.values():
        result["margin"] = result["sales"] - result["cost"]
    return list(grouped.values())


def turnover(company: str, from_date: str | None = None) -> list[dict[str, Any]]:
    _assert_user_may_view_company(company)
    names = sold_invoice_names(company, from_date)
    if not names:
        return []
    rows = frappe.get_all(
        "Sales Invoice Item",
        filters={"parent": ["in", names]},
        fields=["item_code", "qty", "amount"],
    )
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        result = grouped.setdefault(row.item_code, {"item_code": row.item_code, "qty_sold": 0.0, "sales": 0.0})
        result["qty_sold"] += float(row.qty or 0)
        result["sales"] += float(row.amount or 0)
    return list(grouped.values())


def expiring_stock(company: str, days: int = 90) -> list[dict[str, Any]]:
    _assert_user_may_view_company(company)
    warehouses = {
        row.name
        for row in frappe.get_all("Warehouse", filters={"company": company}, fields=["name"])
    }
    if not warehouses:
        return []
    batch_names = {
        row.batch_no
        for row in frappe.get_all(
            "Stock Ledger Entry",
            filters={"warehouse": ["in", list(warehouses)], "batch_no": ["is", "set"], "actual_qty": [">", 0]},
            fields=["batch_no"],
        )
    }
    if not batch_names:
        return []
    # Bug real de paso: el limite inferior usaba frappe.utils.today() (fecha
    # del site) y el superior date.today() sin tz -- podian desalinearse un
    # dia cerca de medianoche si el timezone del servidor no coincide con el
    # del site. Un solo _rd_today() para los dos limites.
    start = _rd_today()
    return frappe.get_all(
        "Batch",
        filters={
            "name": ["in", list(batch_names)],
            "expiry_date": ["between", [start.isoformat(), (start + timedelta(days=days)).isoformat()]],
        },
        fields=["name", "item", "expiry_date"],
    )
