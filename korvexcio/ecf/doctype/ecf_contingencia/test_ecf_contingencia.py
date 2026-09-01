"""Integration tests for the ECF Contingencia DocType (S2.11).

A diferencia de ECF (S2.4), que solo bloquea borrar/cancelar una vez que
la DGII respondio Aceptado, ECF Contingencia bloquea SIEMPRE -- incluso
en Draft, sin someter. Es la consecuencia directa del patron ZATCA
Precomputed Invoice: el documento se computa y se entrega al cliente en
el mismo acto de la venta offline, no hay un estado intermedio real
donde "todavia no se le dio al cliente"."""

import frappe
from frappe.tests import IntegrationTestCase

IGNORE_TEST_RECORD_DEPENDENCIES = ["Company"]

COMPANY_A = "_Test Company KORVEXCIO A"


class TestECFContingencia(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests

        before_tests()

    def tearDown(self):
        frappe.db.delete("ECF Contingencia", {"company": COMPANY_A})
        frappe.db.commit()

    def _make_contingencia(self, **overrides):
        data = {
            "doctype": "ECF Contingencia",
            "company": COMPANY_A,
            "reference_doctype": "Company",
            "reference_name": COMPANY_A,
            "tipo_ecf": "E32",
            "encf_precomputado": "E320000009999",
            "fecha_contingencia": frappe.utils.now_datetime(),
            "motivo": "Sin internet",
            "signed_xml": "<ECF><Encabezado/></ECF>",
        }
        data.update(overrides)
        return frappe.get_doc(data).insert()

    def test_missing_signed_xml_is_rejected(self):
        data = {
            "doctype": "ECF Contingencia",
            "company": COMPANY_A,
            "reference_doctype": "Company",
            "reference_name": COMPANY_A,
            "tipo_ecf": "E32",
            "encf_precomputado": "E320000009998",
            "fecha_contingencia": frappe.utils.now_datetime(),
            "motivo": "Sin internet",
        }
        with self.assertRaises(frappe.ValidationError):
            frappe.get_doc(data).insert()

    def test_submit_works_normally(self):
        doc = self._make_contingencia()
        doc.submit()
        self.assertEqual(doc.docstatus, 1)

    def test_signed_xml_is_preserved_byte_for_byte(self):
        """Frappe sanitiza como XSS cualquier campo de texto que 'parezca
        HTML' (bs4, ver frappe/model/base_document.py::_sanitize_content)
        -- un XML firmado SIN ignore_xss_filter=1 en el campo se
        corrompe en silencio al guardar (sale vacio o con tags
        despojados), lo que invalida la firma digital. Bug real
        encontrado por este mismo test al escribirlo (no por revision):
        el primer intento sin ignore_xss_filter fallaba con
        MandatoryError porque el XML de prueba quedaba vacio tras
        sanitizar."""
        original = '<ECF><Encabezado><IdDoc><eNCF>E320000009999</eNCF></IdDoc></Encabezado></ECF>'
        doc = self._make_contingencia(signed_xml=original)
        doc.reload()
        self.assertEqual(doc.signed_xml, original)

    def test_delete_blocked_even_in_draft_without_submitting(self):
        doc = self._make_contingencia()
        self.assertEqual(doc.docstatus, 0)
        with self.assertRaises(frappe.ValidationError):
            frappe.delete_doc("ECF Contingencia", doc.name, force=True)
        self.assertTrue(frappe.db.exists("ECF Contingencia", doc.name))

    def test_delete_blocked_after_submit(self):
        doc = self._make_contingencia()
        doc.submit()
        with self.assertRaises(frappe.ValidationError):
            frappe.delete_doc("ECF Contingencia", doc.name, force=True)
        self.assertTrue(frappe.db.exists("ECF Contingencia", doc.name))

    def test_cancel_blocked_even_right_after_submit(self):
        doc = self._make_contingencia()
        doc.submit()
        with self.assertRaises(frappe.ValidationError):
            doc.cancel()
        doc.reload()
        self.assertEqual(doc.docstatus, 1)

    def test_cancel_blocked_regardless_of_estado(self):
        doc = self._make_contingencia()
        doc.submit()
        doc.db_set("estado", "Rechazado")
        doc.reload()
        with self.assertRaises(frappe.ValidationError):
            doc.cancel()
