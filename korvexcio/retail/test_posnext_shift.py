"""S4.2: POSNext (pos_next app) does NOT use ERPNext's native POS
Opening/Closing Entry -- it ships its own "POS Opening Shift" / "POS
Closing Shift" doctypes with the same `company` field. This is what the
real cashier screen actually creates, so it needs the same D19
isolation and role wiring as korvexcio/retail/test_cash_shift.py
covers for the ERPNext-native pair. Skips cleanly if pos_next isn't
installed on the site running the suite."""

import unittest

import frappe
from frappe.tests import IntegrationTestCase

COMPANY_A = "_Test Company KORVEXCIO A"
COMPANY_B = "_Test Company KORVEXCIO B"
ABBR_A = "_TCKA"
ABBR_B = "_TCKB"
CAJERO_A = "_test.posnextshift.cajero.a@korvexdev.cc"


def _pos_next_installed() -> bool:
    return "pos_next" in frappe.get_installed_apps()


class TestPosNextShiftCompanyIsolation(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not _pos_next_installed():
            raise unittest.SkipTest("pos_next no esta instalado en este site")
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests
        from korvexcio.roles import assign_company_user_permission, sync_roles

        before_tests()
        sync_roles()

        for company, abbr in ((COMPANY_A, ABBR_A), (COMPANY_B, ABBR_B)):
            mop = frappe.get_doc("Mode of Payment", "Cash")
            if not any(row.company == company for row in mop.accounts):
                mop.append(
                    "accounts", {"company": company, "default_account": f"Cash - {abbr}"}
                )
                mop.save()

        if not frappe.db.exists("User", CAJERO_A):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": CAJERO_A,
                    "first_name": "Cajero PosNextShift Test",
                    "user_type": "System User",
                    "send_welcome_email": 0,
                    "roles": [{"role": "Cajero VLJ"}],
                }
            ).insert()
        assign_company_user_permission(CAJERO_A, COMPANY_A)

        for company, abbr, profile in (
            (COMPANY_A, ABBR_A, "_Test PosNext Shift A"),
            (COMPANY_B, ABBR_B, "_Test PosNext Shift B"),
        ):
            if not frappe.db.exists("POS Profile", profile):
                company_doc = frappe.get_cached_doc("Company", company)
                doc = frappe.new_doc("POS Profile")
                doc.name = profile
                doc.company = company
                doc.warehouse = f"Stores - {abbr}"
                doc.currency = company_doc.default_currency
                doc.write_off_account = company_doc.write_off_account
                doc.write_off_cost_center = company_doc.cost_center
                doc.append("payments", {"mode_of_payment": "Cash", "default": 1})
                doc.insert()

        cls.profile_a = "_Test PosNext Shift A"
        cls.profile_b = "_Test PosNext Shift B"

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    @staticmethod
    def _open(company: str, profile: str) -> str:
        doc = frappe.new_doc("POS Opening Shift")
        doc.company = company
        doc.pos_profile = profile
        doc.user = frappe.session.user
        doc.period_start_date = frappe.utils.now_datetime()
        doc.append("balance_details", {"mode_of_payment": "Cash", "amount": 0})
        doc.insert()
        doc.submit()
        return doc.name

    def test_cajero_can_open_a_shift_on_own_companys_profile(self):
        frappe.set_user(CAJERO_A)
        name = self._open(COMPANY_A, self.profile_a)
        self.assertTrue(frappe.db.exists("POS Opening Shift", name))

    def test_cajero_cannot_open_a_shift_naming_another_companys_profile(self):
        frappe.set_user(CAJERO_A)
        with self.assertRaises(frappe.PermissionError):
            self._open(COMPANY_B, self.profile_b)

    def test_cajero_cannot_read_other_companys_shift(self):
        frappe.set_user("Administrator")
        name_b = self._open(COMPANY_B, self.profile_b)

        frappe.set_user(CAJERO_A)
        with self.assertRaises(frappe.PermissionError):
            frappe.client.get("POS Opening Shift", name_b)
