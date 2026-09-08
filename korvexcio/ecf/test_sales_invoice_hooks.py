"""Integration tests for the Sales Invoice doc_events (S2.9).

Usa una Sales Invoice real e insertada -- Frappe valida que el Dynamic
Link `ECF.reference_name` exista de verdad, asi que no se puede simular
con un nombre inventado. Crear una Company provisiona un Chart of
Accounts completo por default (verificado en el nodo, no asumido), asi
que solo hacen falta un Customer y un Item de prueba."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase


class TestSalesInvoiceHooks(IntegrationTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests

        before_tests()

        # Generate unique hash for this test instance to ensure isolation
        self.test_hash = frappe.generate_hash(8)

        # Define base names
        self.base_company_a = "_Test Company KORVEXCIO A"
        self.base_abbr_a = "_TCKA"
        self.base_customer = "_Test Customer KORVEXCIO S2.9"
        self.base_customer_with_rnc = "_Test Customer KORVEXCIO RNC S2.9"
        self.base_item = "_Test Item KORVEXCIO S2.9"

        # Create unique names for this test instance
        self.company_a = f"{self.base_company_a}-{self.test_hash}"
        self.abbr_a = f"{self.base_abbr_a}-{self.test_hash}"
        self.customer = f"{self.base_customer.split('@')[0]}+{self.test_hash}@korvexdev.cc" if "@" in self.base_customer else f"{self.base_customer}+{self.test_hash}"
        self.customer_with_rnc = f"{self.base_customer_with_rnc.split('@')[0]}+{self.test_hash}@korvexdev.cc" if "@" in self.base_customer_with_rnc else f"{self.base_customer_with_rnc}+{self.test_hash}"
        self.item = f"{self.base_item}-{self.test_hash}"

        # Create test data
        if not frappe.db.exists("Customer", self.customer):
            frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": self.customer,
                    "customer_group": "Commercial",
                    "territory": "All Territories",
                }
            ).insert()

        if not frappe.db.exists("Customer", self.customer_with_rnc):
            # El RNC fiscal de Korvex vive en Customer.rnc, no en la factura.
            frappe.get_doc(
                {
                    "doctype": "Customer",
                    "customer_name": self.customer_with_rnc,
                    "customer_group": "Commercial",
                    "territory": "All Territories",
                    "rnc": "131234567",
                }
            ).insert()
        else:
            frappe.db.set_value("Customer", self.customer_with_rnc, "rnc", "131234567")

        if not frappe.db.exists("Item", self.item):
            frappe.get_doc(
                {
                    "doctype": "Item",
                    "item_code": self.item,
                    "item_name": self.item,
                    "item_group": "All Item Groups",
                    "is_stock_item": 0,
                    "stock_uom": "Nos",
                }
            ).insert()

        self._ensure_secuencia(self.company_a, "E32")
        self._ensure_secuencia(self.company_a, "E31")
        self._ensure_secuencia(self.company_a, "E34")

    def tearDown(self):
        frappe.set_user("Administrator")
        # Clean up in reverse dependency order to avoid foreign key constraints
        try:
            # Clean ECFs first (they depend on Sales Invoices)
            for ecf_name in frappe.get_all("ECF", filters={"reference_doctype": "Sales Invoice"}, pluck="name"):
                ecf_doc = frappe.get_doc("ECF", ecf_name)
                if ecf_doc.docstatus == 1:
                    ecf_doc.cancel()
                frappe.delete_doc("ECF", ecf_name, force=True)

            # Clean Sales Invoices
            for si_name in frappe.get_all("Sales Invoice", pluck="name"):
                si_doc = frappe.get_doc("Sales Invoice", si_name)
                if si_doc.docstatus == 1:
                    si_doc.cancel()
                frappe.delete_doc("Sales Invoice", si_name, force=True)

            # Clean Print Queue entries
            for pq_name in frappe.get_all("Print Queue", pluck="name"):
                frappe.delete_doc("Print Queue", pq_name, force=True)

            # Clean Customers
            for customer_name in frappe.get_all("Customer", pluck="name"):
                frappe.delete_doc("Customer", customer_name, force=True)

            # Clean Items
            for item_name in frappe.get_all("Item", pluck="name"):
                frappe.delete_doc("Item", item_name, force=True)

            # Clean Companies
            for company_name in frappe.get_all("Company", pluck="name"):
                frappe.delete_doc("Company", company_name, force=True)

            # Clean Sequences
            for seq_name in frappe.get_all("Secuencia eNCF", pluck="name"):
                frappe.delete_doc("Secuencia eNCF", seq_name, force=True)

        except (frappe.DoesNotExistError, frappe.ValidationError):
            # Ignore if documents don't exist or validation errors during cleanup
            pass

        super().tearDown()

    def _new_invoice(self, with_rnc=False, rate=1500):
        si = frappe.new_doc("Sales Invoice")
        si.company = self.company_a
        si.customer = self.customer_with_rnc if with_rnc else self.customer
        si.currency = "DOP"
        si.conversion_rate = 1
        si.append(
            "items",
            {
                "item_code": self.item,
                "qty": 1,
                "rate": rate,
                "income_account": f"Sales - {self.abbr_a}",
                "cost_center": f"Main - {self.abbr_a}",
            },
        )
        return si

    def _submit_and_get_ecf(self, si) -> "frappe.model.document.Document":
        si.insert()
        si.submit()
        self.addCleanup(self._cleanup_invoice, si.name)
        ecf_name = frappe.db.get_value(
            "ECF", {"reference_doctype": "Sales Invoice", "reference_name": si.name}, "name"
        )
        self.assertIsNotNone(ecf_name, "on_submit no creo el registro ECF")
        return frappe.get_doc("ECF", ecf_name)

    def _cleanup_invoice(self, name: str) -> None:
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

    def _ensure_secuencia(self, company: str, tipo_ecf: str) -> None:
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

    def test_rnc_required_above_threshold(self):
        si = self._new_invoice(rate=300_000)
        with self.assertRaises(frappe.ValidationError):
            si.insert()

    def test_rnc_not_required_below_threshold(self):
        si = self._new_invoice(rate=1000)
        si.insert()
        self.addCleanup(self._cleanup_invoice, si.name)

    def test_submit_without_rnc_reserves_e32(self):
        ecf = self._submit_and_get_ecf(self._new_invoice(rate=1500))
        self.assertEqual(ecf.tipo_ecf, "E32")
        self.assertEqual(ecf.estado, "Pendiente")
        self.assertEqual(ecf.company, self.company_a)
        self.assertTrue(ecf.encf.startswith("E32"))

    def test_submit_with_rnc_reserves_e31(self):
        ecf = self._submit_and_get_ecf(self._new_invoice(with_rnc=True, rate=1500))
        self.assertEqual(ecf.tipo_ecf, "E31")
        self.assertTrue(ecf.encf.startswith("E31"))

    def test_credit_note_reserves_e34_regardless_of_rnc(self):
        original = self._submit_and_get_ecf(self._new_invoice(with_rnc=True, rate=1500))
        original_si = frappe.get_all(
            "ECF", filters={"name": original.name}, pluck="reference_name"
        )[0]

        credit_note = frappe.new_doc("Sales Invoice")
        credit_note.company = self.company_a
        credit_note.customer = self.customer_with_rnc
        credit_note.currency = "DOP"
        credit_note.conversion_rate = 1
        credit_note.is_return = 1
        credit_note.return_against = original_si
        credit_note.append(
            "items",
            {
                "item_code": self.item,
                "qty": -1,
                "rate": 1500,
                "income_account": f"Sales - {self.abbr_a}",
                "cost_center": f"Main - {self.abbr_a}",
            },
        )
        ecf = self._submit_and_get_ecf(credit_note)
        self.assertEqual(ecf.tipo_ecf, "E34")
        self.assertTrue(ecf.encf.startswith("E34"))

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

    def test_cancel_blocked_while_ecf_is_being_sent(self):
        si = self._new_invoice(rate=1500)
        ecf = self._submit_and_get_ecf(si)
        frappe.db.set_value("ECF", ecf.name, "estado", "Enviando")
        with self.assertRaises(frappe.ValidationError):
            si.cancel()

    def test_submit_enqueues_after_commit_without_calling_provider(self):
        si = self._new_invoice(rate=1500)
        with patch("frappe.enqueue") as enqueue:
            ecf = self._submit_and_get_ecf(si)
        enqueue.assert_called_once()
        kwargs = enqueue.call_args.kwargs
        self.assertTrue(kwargs["enqueue_after_commit"])
        self.assertEqual(kwargs["queue"], "short")
        self.assertEqual(kwargs["ecf_name"], ecf.name)
