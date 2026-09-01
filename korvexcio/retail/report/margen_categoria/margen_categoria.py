import frappe

from korvexcio.retail.reports import company_filter, margin_by_category


def execute(filters=None):
    company = company_filter(frappe._dict(filters or {}))
    return [
        {"label": "Item Group", "fieldname": "item_group", "fieldtype": "Data"},
        {"label": "Sales", "fieldname": "sales", "fieldtype": "Currency"},
        {"label": "Cost", "fieldname": "cost", "fieldtype": "Currency"},
        {"label": "Margin", "fieldname": "margin", "fieldtype": "Currency"},
    ], margin_by_category(company, frappe._dict(filters or {}).get("from_date"))
