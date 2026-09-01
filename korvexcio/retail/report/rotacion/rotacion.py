import frappe

from korvexcio.retail.reports import company_filter, turnover


def execute(filters=None):
    filters = frappe._dict(filters or {})
    return [
        {"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item"},
        {"label": "Qty Sold", "fieldname": "qty_sold", "fieldtype": "Float"},
        {"label": "Sales", "fieldname": "sales", "fieldtype": "Currency"},
    ], turnover(company_filter(filters), filters.get("from_date"))
