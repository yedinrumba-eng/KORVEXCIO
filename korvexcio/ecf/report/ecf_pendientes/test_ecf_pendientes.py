"""Tests del panel de e-CF pendientes (S2.14)."""

import frappe
from frappe.tests import IntegrationTestCase

from korvexcio.ecf.report.ecf_pendientes.ecf_pendientes import execute

COMPANY_A = "_Test Company KORVEXCIO A"
COMPANY_B = "_Test Company KORVEXCIO B"


class TestECFPendientesReport(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests

        before_tests()

    def tearDown(self):
        frappe.db.delete("ECF", {"company": ["in", [COMPANY_A, COMPANY_B]]})
        frappe.db.delete("ECF Contingencia", {"company": ["in", [COMPANY_A, COMPANY_B]]})
        frappe.db.commit()

    def _make_ecf(self, company, estado, encf="E320000000001"):
        return frappe.get_doc(
            {
                "doctype": "ECF",
                "company": company,
                "reference_doctype": "Company",
                "reference_name": company,
                "tipo_ecf": "E32",
                "encf": encf,
                "estado": estado,
            }
        ).insert()

    def _make_contingencia(self, company, estado, encf="E320000009999"):
        return frappe.get_doc(
            {
                "doctype": "ECF Contingencia",
                "company": company,
                "reference_doctype": "Company",
                "reference_name": company,
                "tipo_ecf": "E32",
                "encf_precomputado": encf,
                "estado": estado,
                "fecha_contingencia": frappe.utils.now_datetime(),
                "motivo": "Sin internet",
                "signed_xml": "<ECF/>",
            }
        ).insert()

    def test_only_unresolved_documents_appear(self):
        pending_ecf = self._make_ecf(COMPANY_A, "Pendiente", encf="E320000000001")
        self._make_ecf(COMPANY_A, "Aceptado", encf="E320000000002")
        pending_contingencia = self._make_contingencia(COMPANY_A, "PendienteDeEnviar", encf="E320000000003")
        self._make_contingencia(COMPANY_A, "Aceptado", encf="E320000000004")

        _columns, data = execute({"company": COMPANY_A})
        names = {row["name"] for row in data}

        self.assertIn(pending_ecf.name, names)
        self.assertIn(pending_contingencia.name, names)
        self.assertEqual(len(data), 2)

    def test_company_filter_is_explicit_not_just_user_permission(self):
        self._make_ecf(COMPANY_A, "Pendiente")
        self._make_ecf(COMPANY_B, "Pendiente")

        _columns, data_a = execute({"company": COMPANY_A})
        self.assertTrue(all(row["company"] == COMPANY_A for row in data_a))

        _columns, data_b = execute({"company": COMPANY_B})
        self.assertTrue(all(row["company"] == COMPANY_B for row in data_b))

    def test_rows_are_sorted_oldest_first(self):
        first = self._make_ecf(COMPANY_A, "Pendiente", encf="E320000000010")
        second = self._make_contingencia(COMPANY_A, "Enviado", encf="E320000000011")

        _columns, data = execute({"company": COMPANY_A})
        self.assertEqual([row["name"] for row in data], [first.name, second.name])

    def test_dynamic_link_doctype_field_matches_row_type(self):
        self._make_ecf(COMPANY_A, "Enviando")
        self._make_contingencia(COMPANY_A, "Rechazado")

        _columns, data = execute({"company": COMPANY_A})
        by_tipo = {row["tipo"]: row["doctype"] for row in data}
        self.assertEqual(by_tipo["ECF"], "ECF")
        self.assertEqual(by_tipo["ECF Contingencia"], "ECF Contingencia")
