import frappe

from korvexcio.retail.reports import company_filter, daily_sales


def execute(filters=None):
    filters = frappe._dict(filters or {})
    return [
        {"label": "Invoices", "fieldname": "invoice_count", "fieldtype": "Int"},
        {"label": "Gross Total", "fieldname": "gross_total", "fieldtype": "Currency"},
        {"label": "Net Total", "fieldname": "net_total", "fieldtype": "Currency"},
    ], [daily_sales(company_filter(filters), filters.get("posting_date"))]
