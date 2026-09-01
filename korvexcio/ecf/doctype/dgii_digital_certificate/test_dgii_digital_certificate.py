"""Integration tests for the company-scoped DGII Digital Certificate DocType."""

from datetime import date

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days

IGNORE_TEST_RECORD_DEPENDENCIES = ["Company"]

COMPANY_A = "_Test Company KORVEXCIO A"


class TestDGIIDigitalCertificate(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests

        before_tests()

    def tearDown(self):
        frappe.db.delete("DGII Digital Certificate", {"company": COMPANY_A})
        frappe.db.commit()

    def test_password_is_masked_never_stored_plain(self):
        cert = frappe.get_doc(
            {
                "doctype": "DGII Digital Certificate",
                "company": COMPANY_A,
                "certificate": "/private/files/test-cert.p12",
                "password": "dummy-cert-password-1",
                "valid_until": add_days(date.today(), 400),
            }
        ).insert()

        raw = frappe.db.get_value("DGII Digital Certificate", cert.name, "password")
        self.assertNotEqual(raw, "dummy-cert-password-1")

        as_dict = frappe.client.get("DGII Digital Certificate", cert.name)
        self.assertNotIn("dummy-cert-password-1", str(as_dict.get("password", "")))

    def test_expiry_message_pure_function(self):
        from korvexcio.ecf.doctype.dgii_digital_certificate.dgii_digital_certificate import (
            expiry_message,
        )

        today = date(2026, 1, 1)
        self.assertIsNone(
            expiry_message(COMPANY_A, date(2027, 1, 1), warning_days=30, today=today)
        )
        soon = expiry_message(COMPANY_A, date(2026, 1, 10), warning_days=30, today=today)
        self.assertIsNotNone(soon)
        self.assertIn("vence", soon)
        expired = expiry_message(COMPANY_A, date(2025, 12, 1), warning_days=30, today=today)
        self.assertIn("vencio", expired)

    def test_insert_does_not_raise_when_close_to_expiry(self):
        cert = frappe.get_doc(
            {
                "doctype": "DGII Digital Certificate",
                "company": COMPANY_A,
                "certificate": "/private/files/test-cert.p12",
                "password": "dummy-cert-password-2",
                "valid_until": add_days(date.today(), 5),
                "expiry_warning_days": 30,
            }
        )
        cert.insert()
        self.assertTrue(frappe.db.exists("DGII Digital Certificate", cert.name))

    def test_only_one_certificate_per_company(self):
        frappe.get_doc(
            {
                "doctype": "DGII Digital Certificate",
                "company": COMPANY_A,
                "certificate": "/private/files/test-cert.p12",
                "password": "dummy-cert-password-first",
                "valid_until": add_days(date.today(), 400),
            }
        ).insert()

        duplicate = frappe.get_doc(
            {
                "doctype": "DGII Digital Certificate",
                "company": COMPANY_A,
                "certificate": "/private/files/other-cert.p12",
                "password": "dummy-cert-password-second",
                "valid_until": add_days(date.today(), 400),
            }
        )
        with self.assertRaises(frappe.DuplicateEntryError):
            duplicate.insert()
