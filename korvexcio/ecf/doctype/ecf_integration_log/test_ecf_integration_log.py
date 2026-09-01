"""Integration tests for ECF Integration Log masking."""

import frappe
from frappe.tests import IntegrationTestCase

IGNORE_TEST_RECORD_DEPENDENCIES = ["Company"]

COMPANY_A = "_Test Company KORVEXCIO A"


class TestECFIntegrationLog(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests

        before_tests()

    def tearDown(self):
        frappe.db.delete("ECF Integration Log", {"company": COMPANY_A})
        frappe.db.commit()

    def test_token_masked_in_json_payload(self):
        log = frappe.get_doc(
            {
                "doctype": "ECF Integration Log",
                "company": COMPANY_A,
                "provider": "Alanube",
                "operation": "token",
                "request_url": "https://sandbox.alanube.co/dom/v1/auth",
                "response_payload": '{"access_token": "dummy-real-looking-token-abc123", "expires_in": 3600}',
            }
        ).insert()

        self.assertNotIn("dummy-real-looking-token-abc123", log.response_payload)
        self.assertIn("MASKED", log.response_payload)
        self.assertIn("expires_in", log.response_payload)
        self.assertIn("3600", log.response_payload)

        stored = frappe.db.get_value("ECF Integration Log", log.name, "response_payload")
        self.assertNotIn("dummy-real-looking-token-abc123", stored)

    def test_authorization_header_masked(self):
        log = frappe.get_doc(
            {
                "doctype": "ECF Integration Log",
                "company": COMPANY_A,
                "provider": "ECF SSD",
                "operation": "emitir",
                "request_payload": "Authorization: Bearer dummy-real-token-xyz789\nContent-Type: application/json",
            }
        ).insert()

        self.assertNotIn("dummy-real-token-xyz789", log.request_payload)
        self.assertIn("MASKED", log.request_payload)
        self.assertIn("Content-Type: application/json", log.request_payload)

    def test_non_sensitive_content_untouched(self):
        log = frappe.get_doc(
            {
                "doctype": "ECF Integration Log",
                "company": COMPANY_A,
                "provider": "Alanube",
                "operation": "consultar",
                "response_payload": '{"encf": "E320000000001", "estado": "Aceptado"}',
            }
        ).insert()
        self.assertEqual(
            log.response_payload, '{"encf": "E320000000001", "estado": "Aceptado"}'
        )
