"""Integration tests for the ECF DocType."""

import frappe
from frappe.tests import IntegrationTestCase

IGNORE_TEST_RECORD_DEPENDENCIES = ["Company"]

COMPANY_A = "_Test Company KORVEXCIO A"


class TestECF(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests

        before_tests()

    def tearDown(self):
        frappe.db.delete("ECF", {"company": COMPANY_A})
        frappe.db.commit()

    def _make_ecf(self, estado="Pendiente"):
        return frappe.get_doc(
            {
                "doctype": "ECF",
                "company": COMPANY_A,
                "reference_doctype": "Company",
                "reference_name": COMPANY_A,
                "tipo_ecf": "E32",
                "estado": estado,
            }
        ).insert()

    def test_submit_pending_ecf(self):
        ecf = self._make_ecf(estado="Pendiente")
        ecf.submit()
        self.assertEqual(ecf.docstatus, 1)

    def test_cancel_pending_ecf_allowed(self):
        ecf = self._make_ecf(estado="Pendiente")
        ecf.submit()
        ecf.cancel()
        self.assertEqual(ecf.docstatus, 2)

    def test_cancel_aceptado_ecf_blocked(self):
        ecf = self._make_ecf(estado="Pendiente")
        ecf.submit()
        ecf.db_set("estado", "Aceptado")
        ecf.reload()
        with self.assertRaises(frappe.ValidationError):
            ecf.cancel()
        ecf.reload()
        self.assertEqual(ecf.docstatus, 1)

    def test_delete_aceptado_ecf_blocked_even_forced(self):
        ecf = self._make_ecf(estado="Pendiente")
        ecf.submit()
        ecf.db_set("estado", "Aceptado")
        with self.assertRaises(frappe.ValidationError):
            frappe.delete_doc("ECF", ecf.name, force=True)
        self.assertTrue(frappe.db.exists("ECF", ecf.name))
