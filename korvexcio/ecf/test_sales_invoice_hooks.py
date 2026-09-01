"""Integration tests for the Sales Invoice doc_events (S2.9).

Usa una Sales Invoice real e insertada -- Frappe valida que el Dynamic
Link `ECF.reference_name` exista de verdad, asi que no se puede simular
con un nombre inventado. Crear una Company provisiona un Chart of
Accounts completo por default (verificado en el nodo, no asumido), asi
que solo hacen falta un Customer y un Item de prueba."""

import frappe
from frappe.tests import IntegrationTestCase

COMPANY_A = "_Test Company KORVEXCIO A"
ABBR_A = "_TCKA"
CUSTOMER = "_Test Customer KORVEXCIO S2.9"
CUSTOMER_WITH_RNC = "_Test Customer KORVEXCIO RNC S2.9"
ITEM = "_Test Item KORVEXCIO S2.9"


def _cleanup_invoice(name: str) -> None:
    """Best-effort: cancelar si quedo sometida (Sales Invoice sometida no
    se puede borrar sin cancelar primero) y borrar. Si el propio test dejo
    la factura bloqueada a proposito (ECF Aceptado), se queda sin borrar
    -- es dato de prueba en una Company descartable, no producción."""
    # Best-effort cleanup only: a test can deliberately leave the invoice
    # blocked (ECF Aceptado), and that's fine in a throwaway test Company --
    # no reason to log or fail the test run over tidy-up not landing.
    try:
        doc = frappe.get_doc("Sales Invoice", name)
        if doc.docstatus == 1:
            doc.cancel()
        frappe.delete_doc("Sales Invoice", name, force=True, ignore_permissions=True)
    except Exception:  # noqa: BLE001, S110
        pass


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


class TestSalesInvoiceHooks(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests

        before_tests()

        if not frappe.db.exists("Customer", CUSTOMER):
            frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": CUSTOMER,
                    "customer_group": "Commercial",
                    "territory": "All Territories",
                }
            ).insert()

        if not frappe.db.exists("Customer", CUSTOMER_WITH_RNC):
            # Sales Invoice.tax_id tiene fetch_from=customer.tax_id y es
            # read_only -- ERPNext lo re-fetchea en validate() y pisa
            # cualquier valor puesto a mano en la factura. Para probar el
            # camino E31 hay que ponerle el RNC al Customer, no a la
            # factura.
            frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": CUSTOMER_WITH_RNC,
                    "customer_group": "Commercial",
                    "territory": "All Territories",
                    "tax_id": "131234567",
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

        _ensure_secuencia(COMPANY_A, "E32")
        _ensure_secuencia(COMPANY_A, "E31")

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    def _new_invoice(self, with_rnc=False, rate=1500):
        si = frappe.new_doc("Sales Invoice")
        si.company = COMPANY_A
        si.customer = CUSTOMER_WITH_RNC if with_rnc else CUSTOMER
        si.currency = "DOP"
        si.conversion_rate = 1
        si.append(
            "items",
            {
                "item_code": ITEM,
                "qty": 1,
                "rate": rate,
                "income_account": f"Sales - {ABBR_A}",
                "cost_center": f"Main - {ABBR_A}",
            },
        )
        return si

    def _submit_and_get_ecf(self, si) -> "frappe.model.document.Document":
        si.insert()
        si.submit()
        self.addCleanup(_cleanup_invoice, si.name)
        ecf_name = frappe.db.get_value(
            "ECF", {"reference_doctype": "Sales Invoice", "reference_name": si.name}, "name"
        )
        self.assertIsNotNone(ecf_name, "on_submit no creo el registro ECF")
        return frappe.get_doc("ECF", ecf_name)

    def test_rnc_required_above_threshold(self):
        si = self._new_invoice(rate=300_000)
        with self.assertRaises(frappe.ValidationError):
            si.insert()

    def test_rnc_not_required_below_threshold(self):
        si = self._new_invoice(rate=1000)
        si.insert()
        self.addCleanup(_cleanup_invoice, si.name)

    def test_submit_without_rnc_reserves_e32(self):
        ecf = self._submit_and_get_ecf(self._new_invoice(rate=1500))
        self.assertEqual(ecf.tipo_ecf, "E32")
        self.assertEqual(ecf.estado, "Pendiente")
        self.assertEqual(ecf.company, COMPANY_A)
        self.assertTrue(ecf.encf.startswith("E32"))

    def test_submit_with_rnc_reserves_e31(self):
        ecf = self._submit_and_get_ecf(self._new_invoice(with_rnc=True, rate=1500))
        self.assertEqual(ecf.tipo_ecf, "E31")
        self.assertTrue(ecf.encf.startswith("E31"))

    def test_two_submits_do_not_collide_on_encf(self):
        ecf_1 = self._submit_and_get_ecf(self._new_invoice(rate=1500))
        ecf_2 = self._submit_and_get_ecf(self._new_invoice(rate=1600))
        self.assertNotEqual(ecf_1.encf, ecf_2.encf)

    def test_cancel_blocked_once_ecf_accepted(self):
        si = self._new_invoice(rate=1500)
        ecf = self._submit_and_get_ecf(si)
        frappe.db.set_value("ECF", ecf.name, "estado", "Aceptado")

        with self.assertRaises(frappe.ValidationError):
            si.cancel()

    def test_cancel_allowed_while_pending(self):
        si = self._new_invoice(rate=1500)
        self._submit_and_get_ecf(si)
        si.cancel()
