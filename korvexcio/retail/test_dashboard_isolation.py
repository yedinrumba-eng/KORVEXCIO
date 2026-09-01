"""Integration test for the blueprint's real S3.6 criterion: "el dueño
lo abre y ve las dos [Companies]" -- the existing test_dashboard.py only
unit-tested the non-owner rejection with a mock, never confirmed a real
Dueño with access to both Companies actually gets consolidated data."""

import frappe
from frappe.tests import IntegrationTestCase

from korvexcio.retail.dashboard import get_dashboard_data

COMPANY_A = "_Test Company KORVEXCIO A"
COMPANY_B = "_Test Company KORVEXCIO B"
ABBR_A = "_TCKA"
ABBR_B = "_TCKB"
CUSTOMER = "_Test Customer KORVEXCIO Dashboard"
ITEM = "_Test Item KORVEXCIO Dashboard"
DUENO_BOTH = "_test.dashboard.dueno.both@korvexdev.cc"


def _ensure_secuencia(company: str, tipo_ecf: str) -> None:
    name = f"{company}-{tipo_ecf}"
    if frappe.db.exists("Secuencia eNCF", name):
        return
    frappe.get_doc(
        {
            "doctype": "Secuencia eNCF",
            "company": company,
            "tipo_ecf": tipo_ecf,
            "desde": 1,
            "hasta": 999999,
            "siguiente": 1,
            "fecha_vencimiento": "2027-12-31",
        }
    ).insert()


class TestDashboardConsolidation(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests
        from korvexcio.roles import assign_company_user_permission, sync_roles

        before_tests()
        sync_roles()

        if not frappe.db.exists("Customer", CUSTOMER):
            frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": CUSTOMER,
                    "customer_group": "Commercial",
                    "territory": "All Territories",
                }
            ).insert()

        if not frappe.db.exists("Item", ITEM):
            frappe.get_doc(
                {
                    "doctype": "Item",
                    "item_code": ITEM,
                    "item_name": ITEM,
                    "item_group": "All Item Groups",
                    "is_stock_item": 0,
                    "stock_uom": "Nos",
                }
            ).insert()

        if not frappe.db.exists("User", DUENO_BOTH):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": DUENO_BOTH,
                    "first_name": "Dueno Dashboard Isolation Test",
                    "user_type": "System User",
                    "send_welcome_email": 0,
                    "roles": [{"role": "Dueño"}],
                }
            ).insert()
        # El dueño real ve las dos Companies -- dos User Permission, una
        # por cada una, nunca una tercera sin permiso explicito (D19).
        assign_company_user_permission(DUENO_BOTH, COMPANY_A)
        assign_company_user_permission(DUENO_BOTH, COMPANY_B)

        _ensure_secuencia(COMPANY_A, "E32")
        _ensure_secuencia(COMPANY_B, "E32")

        cls._submit_invoice(COMPANY_A, ABBR_A, 1500)
        cls._submit_invoice(COMPANY_B, ABBR_B, 2500)

    @classmethod
    def _submit_invoice(cls, company, abbr, rate):
        si = frappe.new_doc("Sales Invoice")
        si.company = company
        si.customer = CUSTOMER
        si.currency = "DOP"
        si.conversion_rate = 1
        si.append(
            "items",
            {
                "item_code": ITEM,
                "qty": 1,
                "rate": rate,
                "income_account": f"Sales - {abbr}",
                "cost_center": f"Main - {abbr}",
            },
        )
        si.insert()
        si.submit()
        return si

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_owner_with_both_companies_sees_both_consolidated(self):
        frappe.set_user(DUENO_BOTH)
        data = get_dashboard_data()

        self.assertEqual(set(data["companies"]), {COMPANY_A, COMPANY_B})
        self.assertEqual(data["sales"][COMPANY_A]["invoice_count"], 1)
        self.assertEqual(data["sales"][COMPANY_B]["invoice_count"], 1)
