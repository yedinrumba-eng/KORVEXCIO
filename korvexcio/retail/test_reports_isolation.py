"""Integration test for the blueprint's real S3.5 criterion: "cada
reporte corrido como cajero de una Company no devuelve ni una fila de la
otra" -- the existing test_reports.py only unit-tested company_filter()
in isolation, never a real Cajero user against real data in two
Companies. Needs Sales Invoice permissions for Cajero roles, which were
missing entirely until this same slice (see korvexcio/roles.py)."""

import frappe
from frappe.tests import IntegrationTestCase

from korvexcio.retail.reports import daily_sales

COMPANY_A = "_Test Company KORVEXCIO A"
COMPANY_B = "_Test Company KORVEXCIO B"
ABBR_A = "_TCKA"
ABBR_B = "_TCKB"
CUSTOMER = "_Test Customer KORVEXCIO Reports"
ITEM = "_Test Item KORVEXCIO Reports"
CAJERO_A = "_test.reports.cajero.a@korvexdev.cc"


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


class TestReportsCompanyIsolation(IntegrationTestCase):
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

        if not frappe.db.exists("User", CAJERO_A):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": CAJERO_A,
                    "first_name": "Cajero Reports Isolation Test",
                    "user_type": "System User",
                    "send_welcome_email": 0,
                    "roles": [{"role": "Cajero VLJ"}],
                }
            ).insert()
        assign_company_user_permission(CAJERO_A, COMPANY_A)

        _ensure_secuencia(COMPANY_A, "E32")
        _ensure_secuencia(COMPANY_B, "E32")

        cls.invoice_a = cls._submit_invoice(COMPANY_A, ABBR_A, 1500)
        cls.invoice_b = cls._submit_invoice(COMPANY_B, ABBR_B, 2500)

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

    def test_cajero_of_company_a_sees_only_company_a_sales(self):
        frappe.set_user(CAJERO_A)

        own_company = daily_sales(COMPANY_A)
        self.assertEqual(own_company["invoice_count"], 1)
        self.assertEqual(own_company["gross_total"], self.invoice_a.grand_total)

        # Real bug found by this exact test, not by review (2026-09-01):
        # reports.py uses frappe.get_all(), which ignores permissions by
        # default (unlike frappe.get_list()) -- the explicit `company`
        # filter was never a real barrier, a Cajero could just request
        # another Company's data and get it back. Fixed with an explicit
        # User Permission check in reports.py -- it now throws loudly
        # instead of quietly returning zeroed-out data for a Company the
        # user has no business seeing.
        with self.assertRaises(frappe.PermissionError):
            daily_sales(COMPANY_B)

    def test_administrator_sees_both_companies(self):
        frappe.set_user("Administrator")
        self.assertEqual(daily_sales(COMPANY_A)["invoice_count"], 1)
        self.assertEqual(daily_sales(COMPANY_B)["invoice_count"], 1)
