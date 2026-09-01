"""Integration test del print format "Representacion Impresa e-CF"
(S2.12) contra una Sales Invoice real y sometida -- el render pasa por
el mismo frappe.render_template() que usa el pipeline de impresion real,
asi que korvexcio_ecf_for_invoice/korvexcio_qr_data_uri (S2.12, hooks.py
jinja.methods) se resuelven exactamente como en produccion."""

import frappe
from frappe.tests import IntegrationTestCase

COMPANY_A = "_Test Company KORVEXCIO A"
ABBR_A = "_TCKA"
CUSTOMER = "_Test Customer KORVEXCIO PrintFormat"
ITEM = "_Test Item KORVEXCIO PrintFormat"


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


class TestRepresentacionImpresa(IntegrationTestCase):
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

        cls.print_format_html = frappe.get_doc("Print Format", "Representacion Impresa e-CF").html

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    def _submitted_invoice(self):
        si = frappe.new_doc("Sales Invoice")
        si.company = COMPANY_A
        si.customer = CUSTOMER
        si.currency = "DOP"
        si.conversion_rate = 1
        si.append(
            "items",
            {
                "item_code": ITEM,
                "qty": 1,
                "rate": 1500,
                "income_account": f"Sales - {ABBR_A}",
                "cost_center": f"Main - {ABBR_A}",
            },
        )
        si.insert()
        si.submit()
        self.addCleanup(self._cleanup_invoice, si.name)
        return si

    def _cleanup_invoice(self, name):
        # Naming series de Frappe puede reciclar el mismo nombre entre
        # tests una vez la Sales Invoice anterior se borra -- sin borrar
        # tambien el ECF huerfano, el siguiente test con el mismo nombre
        # "hereda" el e-CF de una corrida previa (bug real encontrado por
        # este mismo test al escribirlo).
        try:
            for ecf_name in frappe.get_all(
                "ECF", filters={"reference_doctype": "Sales Invoice", "reference_name": name}, pluck="name"
            ):
                doc = frappe.get_doc("ECF", ecf_name)
                if doc.docstatus == 1:
                    doc.cancel()
                frappe.delete_doc("ECF", ecf_name, force=True, ignore_permissions=True)

            doc = frappe.get_doc("Sales Invoice", name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc("Sales Invoice", name, force=True, ignore_permissions=True)
        except Exception:  # noqa: BLE001, S110
            pass

    def test_renders_with_encf_and_pending_qr_placeholder(self):
        si = self._submitted_invoice()
        html = frappe.render_template(self.print_format_html, {"doc": si})

        self.assertIn(CUSTOMER, html)
        self.assertIn("QR pendiente", html)

        ecf_name = frappe.db.get_value(
            "ECF", {"reference_doctype": "Sales Invoice", "reference_name": si.name}, "name"
        )
        encf = frappe.db.get_value("ECF", ecf_name, "encf")
        self.assertIn(encf, html)

    def test_renders_qr_image_once_provider_gives_a_qr_url(self):
        si = self._submitted_invoice()
        ecf_name = frappe.db.get_value(
            "ECF", {"reference_doctype": "Sales Invoice", "reference_name": si.name}, "name"
        )
        frappe.db.set_value("ECF", ecf_name, "qr_url", "https://ecf.dgii.gov.do/verificar?encf=TEST")

        html = frappe.render_template(self.print_format_html, {"doc": si})
        self.assertIn('src="data:image/svg+xml;base64,', html)
        self.assertNotIn("QR pendiente", html)

    def test_renders_without_crashing_before_ecf_exists(self):
        si = frappe.new_doc("Sales Invoice")
        si.company = COMPANY_A
        si.customer = CUSTOMER
        si.currency = "DOP"
        si.conversion_rate = 1
        si.append(
            "items",
            {
                "item_code": ITEM,
                "qty": 1,
                "rate": 100,
                "income_account": f"Sales - {ABBR_A}",
                "cost_center": f"Main - {ABBR_A}",
            },
        )
        si.insert()
        self.addCleanup(self._cleanup_invoice, si.name)

        html = frappe.render_template(self.print_format_html, {"doc": si})
        self.assertIn("Pendiente de generar", html)
