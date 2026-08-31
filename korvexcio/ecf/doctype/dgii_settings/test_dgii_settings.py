"""Integration tests for the company-scoped DGII Settings DocType."""

import frappe
from frappe.tests import IntegrationTestCase


IGNORE_TEST_RECORD_DEPENDENCIES = ["Company"]

COMPANY_A = "_Test Company KORVEXCIO A"
COMPANY_B = "_Test Company KORVEXCIO B"


class TestDGIISettings(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests

        before_tests()
        cls._ensure_settings(COMPANY_A, "TesteCF", "Alanube")
        cls._ensure_settings(COMPANY_B, "CerteCF", "ECF SSD")

    @staticmethod
    def _ensure_settings(company: str, ambiente: str, provider: str) -> None:
        if frappe.db.exists("DGII Settings", company):
            return
        frappe.get_doc(
            {
                "doctype": "DGII Settings",
                "company": company,
                "ambiente": ambiente,
                "provider": provider,
                "connect_timeout_seconds": 10,
                "read_timeout_seconds": 30,
                "live_sync": 0,
            }
        ).insert()

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_each_company_resolves_its_own_settings(self):
        settings_a = frappe.get_doc("DGII Settings", COMPANY_A)
        settings_b = frappe.get_doc("DGII Settings", COMPANY_B)

        self.assertEqual(settings_a.company, COMPANY_A)
        self.assertEqual(settings_a.ambiente, "TesteCF")
        self.assertEqual(settings_a.provider, "Alanube")
        self.assertEqual(settings_b.company, COMPANY_B)
        self.assertEqual(settings_b.ambiente, "CerteCF")
        self.assertEqual(settings_b.provider, "ECF SSD")

    def test_duplicate_company_is_rejected(self):
        duplicate = frappe.get_doc(
            {
                "doctype": "DGII Settings",
                "company": COMPANY_A,
                "ambiente": "eCF",
                "provider": "Alanube",
                "connect_timeout_seconds": 10,
                "read_timeout_seconds": 30,
            }
        )

        with self.assertRaises(frappe.DuplicateEntryError):
            duplicate.insert()

    def test_timeouts_outside_allowed_range_are_rejected(self):
        settings = frappe.get_doc("DGII Settings", COMPANY_A)

        for timeout in (0, 301):
            with self.subTest(timeout=timeout):
                settings.connect_timeout_seconds = timeout
                with self.assertRaises(frappe.ValidationError):
                    settings.save()
                settings.reload()
                settings.read_timeout_seconds = timeout
                with self.assertRaises(frappe.ValidationError):
                    settings.save()
                settings.reload()
