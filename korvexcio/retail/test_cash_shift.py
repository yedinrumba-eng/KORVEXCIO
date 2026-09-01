"""Integration tests for S4.5: cash shift open/close reconciles by
payment method using ERPNext's own math (make_closing_entry_from_opening
sums real submitted invoices; this module only fills in the opening
float and what the cashier counted), and a Cajero of one Company can't
read the other's POS Closing Entry -- the D19 isolation extended to the
two new company-scoped doctypes."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from korvexcio.retail.cash_shift import close_shift, open_shift
from korvexcio.retail.pos_profile import sync_pos_profiles

COMPANY_A = "_Test Company KORVEXCIO A"
COMPANY_B = "_Test Company KORVEXCIO B"
ABBR_A = "_TCKA"
ABBR_B = "_TCKB"
CUSTOMER = "_Test Customer KORVEXCIO S4.5"
ITEM = "_Test Item KORVEXCIO S4.5"
CAJERO_A = "_test.cashshift.cajero.a@korvexdev.cc"


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


class TestCashShiftReconciliation(IntegrationTestCase):
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
                    "first_name": "Cajero CashShift Test",
                    "user_type": "System User",
                    "send_welcome_email": 0,
                    "roles": [{"role": "Cajero VLJ"}],
                }
            ).insert()
        assign_company_user_permission(CAJERO_A, COMPANY_A)

        _ensure_secuencia(COMPANY_A, "E32")
        _ensure_secuencia(COMPANY_B, "E32")

        config = {
            "enabled": True,
            "pos_profiles": [
                {
                    "company": COMPANY_A,
                    "name": "_Test POS Shift A",
                    "warehouse": f"Stores - {ABBR_A}",
                    "cajero_users": [CAJERO_A],
                },
                {
                    "company": COMPANY_B,
                    "name": "_Test POS Shift B",
                    "warehouse": f"Stores - {ABBR_B}",
                },
            ],
        }
        with (
            patch("korvexcio.retail.pos_profile.is_vertical_enabled", return_value=True),
            patch("korvexcio.retail.pos_profile.get_retail_config", return_value=config),
        ):
            sync_pos_profiles()

        cls.profile_a = "_Test POS Shift A"
        cls.profile_b = "_Test POS Shift B"

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    @staticmethod
    def _sell(company: str, abbr: str, profile: str, amount: float, mode: str = "Cash"):
        si = frappe.new_doc("Sales Invoice")
        si.company = company
        si.customer = CUSTOMER
        si.currency = "DOP"
        si.conversion_rate = 1
        si.is_pos = 1
        si.is_created_using_pos = 1
        si.pos_profile = profile
        si.append(
            "items",
            {
                "item_code": ITEM,
                "qty": 1,
                "rate": amount,
                "income_account": f"Sales - {abbr}",
                "cost_center": f"Main - {abbr}",
            },
        )
        si.append("payments", {"mode_of_payment": mode, "amount": amount})
        si.insert()
        si.submit()
        return si

    def test_shift_reconciles_when_counted_matches_sales(self):
        frappe.set_user(CAJERO_A)
        opening = open_shift(self.profile_a, {"Cash": 500})
        self._sell(COMPANY_A, ABBR_A, self.profile_a, 1000)

        closing_name = close_shift(opening, {"Cash": 1500})
        closing = frappe.get_doc("POS Closing Entry", closing_name)
        cash_row = next(r for r in closing.payment_reconciliation if r.mode_of_payment == "Cash")

        self.assertEqual(cash_row.opening_amount, 500)
        self.assertEqual(cash_row.expected_amount, 1500)
        self.assertEqual(cash_row.closing_amount, 1500)
        self.assertEqual(cash_row.difference, 0)

    def test_shift_flags_a_shortfall(self):
        frappe.set_user(CAJERO_A)
        opening = open_shift(self.profile_a, {"Cash": 0})
        self._sell(COMPANY_A, ABBR_A, self.profile_a, 1000)

        closing_name = close_shift(opening, {"Cash": 900})
        closing = frappe.get_doc("POS Closing Entry", closing_name)
        cash_row = next(r for r in closing.payment_reconciliation if r.mode_of_payment == "Cash")

        self.assertEqual(cash_row.difference, -100)

    def test_cajero_cannot_read_other_companys_closing_entry(self):
        frappe.set_user(CAJERO_A)
        opening_a = open_shift(self.profile_a, {"Cash": 0})
        self._sell(COMPANY_A, ABBR_A, self.profile_a, 500)
        close_shift(opening_a, {"Cash": 500})

        frappe.set_user("Administrator")
        opening_b = open_shift(self.profile_b, {"Cash": 0})
        self._sell(COMPANY_B, ABBR_B, self.profile_b, 700)
        closing_b_name = close_shift(opening_b, {"Cash": 700})

        frappe.set_user(CAJERO_A)
        with self.assertRaises(frappe.PermissionError):
            frappe.client.get("POS Closing Entry", closing_b_name)

    def test_cajero_cannot_open_or_close_a_shift_naming_another_companys_profile(self):
        """frappe.get_doc() (used internally to resolve pos_profile /
        pos_opening_entry) does not check read permission on its own --
        the S1.8 lesson. open_shift/close_shift must reject a foreign
        Company's names explicitly, before touching their real data."""
        frappe.set_user("Administrator")
        opening_b = open_shift(self.profile_b, {"Cash": 0})
        self._sell(COMPANY_B, ABBR_B, self.profile_b, 700)

        frappe.set_user(CAJERO_A)
        with self.assertRaises(frappe.PermissionError):
            open_shift(self.profile_b, {"Cash": 0})
        with self.assertRaises(frappe.PermissionError):
            close_shift(opening_b, {"Cash": 700})

        # Neither denied call closed B's shift -- close it for real so it
        # doesn't collide with the other tests' own opening of profile_b.
        frappe.set_user("Administrator")
        close_shift(opening_b, {"Cash": 700})
