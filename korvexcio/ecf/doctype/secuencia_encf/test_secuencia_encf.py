"""Integration tests for Secuencia eNCF."""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days

IGNORE_TEST_RECORD_DEPENDENCIES = ["Company"]

COMPANY_A = "_Test Company KORVEXCIO A"


class TestSecuenciaeNCF(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests

        before_tests()

    def tearDown(self):
        frappe.db.delete("Secuencia eNCF", {"company": COMPANY_A})
        frappe.db.commit()

    def _make_sequence(self, tipo_ecf="E32", desde=1, hasta=10, siguiente=None):
        return frappe.get_doc(
            {
                "doctype": "Secuencia eNCF",
                "company": COMPANY_A,
                "tipo_ecf": tipo_ecf,
                "desde": desde,
                "hasta": hasta,
                "siguiente": siguiente if siguiente is not None else desde,
                "fecha_vencimiento": add_days(frappe.utils.today(), 365),
            }
        ).insert()

    def test_desde_mayor_que_hasta_es_rechazado(self):
        with self.assertRaises(frappe.ValidationError):
            self._make_sequence(desde=10, hasta=1)

    def test_siguiente_fuera_de_rango_es_rechazado(self):
        with self.assertRaises(frappe.ValidationError):
            self._make_sequence(desde=1, hasta=10, siguiente=20)

    def test_reserve_next_incrementa_y_formatea_encf(self):
        seq = self._make_sequence(tipo_ecf="E32", desde=1, hasta=5)
        encf_1 = seq.reserve_next()
        self.assertEqual(encf_1, "E320000000001")
        encf_2 = seq.reserve_next()
        self.assertEqual(encf_2, "E320000000002")

        fresh = frappe.get_doc("Secuencia eNCF", seq.name)
        self.assertEqual(fresh.siguiente, 3)

    def test_reserve_next_agotada_lanza_error(self):
        seq = self._make_sequence(tipo_ecf="E32", desde=1, hasta=1)
        seq.reserve_next()
        with self.assertRaises(frappe.ValidationError):
            seq.reserve_next()

    def test_dos_secuencias_mismo_tipo_misma_company_es_rechazado(self):
        self._make_sequence(tipo_ecf="E31")
        with self.assertRaises(frappe.DuplicateEntryError):
            self._make_sequence(tipo_ecf="E31")

    def test_mismo_tipo_distinta_company_no_choca(self):
        self._make_sequence(tipo_ecf="E34")
        other = frappe.get_doc(
            {
                "doctype": "Secuencia eNCF",
                "company": "_Test Company KORVEXCIO B",
                "tipo_ecf": "E34",
                "desde": 1,
                "hasta": 10,
                "siguiente": 1,
                "fecha_vencimiento": add_days(frappe.utils.today(), 365),
            }
        ).insert()
        frappe.delete_doc("Secuencia eNCF", other.name, force=True)
