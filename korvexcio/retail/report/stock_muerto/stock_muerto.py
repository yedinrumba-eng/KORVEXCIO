import frappe

from korvexcio.retail.reports import company_filter, stock_dead


def execute(filters=None):
    company = company_filter(frappe._dict(filters or {}))
    return [
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item"},
        {"label": "Warehouse", "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse"},
        {"label": "Qty", "fieldname": "actual_qty", "fieldtype": "Float"},
        {"label": "Valuation Rate", "fieldname": "valuation_rate", "fieldtype": "Currency"},
    ], stock_dead(company)
