"""Integration tests for S4.1: one POS Profile per Company, the cashier
lands on their own without picking anything, and can't read the other
Company's profile. `frappe.client.get` (not `frappe.get_doc`, which
skips read permission checks -- the S1.8 lesson) is what actually proves
the isolation."""

from unittest.mock import patch

import frappe
from erpnext.stock.get_item_details import get_pos_profile
from frappe.tests import IntegrationTestCase
from korvexcio.retail.pos_profile import sync_pos_profiles

COMPANY_A = "_Test Company KORVEXCIO A"
COMPANY_B = "_Test Company KORVEXCIO B"
ABBR_A = "_TCKA"
ABBR_B = "_TCKB"
CAJERO_A = "_test.posprofile.cajero.a@korvexdev.cc"


def test_disabled_site_does_not_create_profiles():
    with (
        patch("korvexcio.retail.pos_profile.is_vertical_enabled", return_value=False),
        patch("korvexcio.retail.pos_profile.get_retail_config", return_value={}),
    ):
        assert sync_pos_profiles() == []


class TestPosProfileCompanyIsolation(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests
        from korvexcio.roles import assign_company_user_permission, sync_roles

        before_tests()
        sync_roles()

        if not frappe.db.exists("User", CAJERO_A):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": CAJERO_A,
                    "first_name": "Cajero PosProfile Isolation Test",
                    "user_type": "System User",
                    "send_welcome_email": 0,
                    "roles": [{"role": "Cajero VLJ"}],
                }
            ).insert()
        assign_company_user_permission(CAJERO_A, COMPANY_A)

        config = {
            "enabled": True,
            "pos_profiles": [
                {
                    "company": COMPANY_A,
                    "name": "_Test POS A",
                    "warehouse": f"Stores - {ABBR_A}",
                    "cajero_users": [CAJERO_A],
                },
                {
                    "company": COMPANY_B,
                    "name": "_Test POS B",
                    "warehouse": f"Stores - {ABBR_B}",
                },
            ],
        }
        with (
            patch("korvexcio.retail.pos_profile.is_vertical_enabled", return_value=True),
            patch("korvexcio.retail.pos_profile.get_retail_config", return_value=config),
        ):
            sync_pos_profiles()

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_cajero_resolves_own_company_profile_without_choosing(self):
        frappe.set_user(CAJERO_A)
        profile = get_pos_profile(company=COMPANY_A, user=CAJERO_A)
        self.assertIsNotNone(profile)
        self.assertEqual(profile["name"], "_Test POS A")

    def test_cajero_cannot_read_other_companys_profile(self):
        frappe.set_user(CAJERO_A)
        with self.assertRaises(frappe.PermissionError):
            frappe.client.get("POS Profile", "_Test POS B")

    def test_cajero_can_read_own_companys_profile(self):
        frappe.set_user(CAJERO_A)
        doc = frappe.client.get("POS Profile", "_Test POS A")
        self.assertEqual(doc["company"], COMPANY_A)
