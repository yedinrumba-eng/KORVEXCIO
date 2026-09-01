import frappe

TEST_COMPANIES = [
    {"company_name": "_Test Company KORVEXCIO A", "abbr": "_TCKA", "tax_id": "000-0000001-1"},
    {"company_name": "_Test Company KORVEXCIO B", "abbr": "_TCKB", "tax_id": "000-0000002-2"},
]


def before_tests():
    """Crea las Companies de prueba que necesita la suite de korvexcio.

    frappe.utils.install.before_tests() se sale sin hacer nada si hay mas de
    una app instalada (frappe+erpnext+korvexcio son 3), asi que korvexcio
    necesita su propio fixture. Dos Companies, no una: S1.8 prueba
    aislamiento ENTRE Companies (D19) y eso no se puede probar con una sola.
    """
    # frappe.local.lang no queda seteado fuera de un request HTTP (bug de
    # upstream en frappe/locale.py:get_locale_value); sin esto, cualquier
    # insert que dispare una Notification con condicion Jinja revienta con
    # UnboundLocalError. Ver "Lecciones ya pagadas" en HANDOFF.md.
    if not frappe.local.lang:
        frappe.local.lang = "en"

    if not frappe.db.exists("Fiscal Year", {"year": "_Test Fiscal Year 2026"}):
        frappe.get_doc(
            {
                "doctype": "Fiscal Year",
                "year": "_Test Fiscal Year 2026",
                "year_start_date": "2026-01-01",
                "year_end_date": "2026-12-31",
            }
        ).insert()

    for cfg in TEST_COMPANIES:
        ensure_test_company(**cfg)

    frappe.db.commit()


def sync_retail_item_attributes() -> None:
    """Sync opt-in retail attributes during migration for configured sites."""
    from korvexcio.retail.item_attributes import sync_item_attributes

    sync_item_attributes()


def sync_retail_cafe_catalog() -> None:
    """Sync opt-in counter-service cafe products during migration."""
    from korvexcio.retail.cafe import sync_cafe_catalog

    sync_cafe_catalog()


def ensure_test_company(company_name: str, abbr: str, tax_id: str) -> None:
    if frappe.db.exists("Company", company_name):
        return

    frappe.get_doc(
        {
            "doctype": "Company",
            "company_name": company_name,
            "abbr": abbr,
            "default_currency": "DOP",
            "country": "Dominican Republic",
            "tax_id": tax_id,
        }
    ).insert()
