"""Integration test del print format "Representacion Impresa e-CF"
(S2.12) contra una Sales Invoice real y sometida -- el render pasa por
el mismo frappe.render_template() que usa el pipeline de impresion real,
asi que korvexcio_ecf_for_invoice/korvexcio_qr_data_uri (S2.12, hooks.py
jinja.methods) se resuelven exactamente como en produccion."""

import frappe
from frappe.tests import IntegrationTestCase


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
        self.base_customer = "_Test Customer KORVEXCIO PrintFormat"
        self.base_item = "_Test Item KORVEXCIO PrintFormat"

        # Create unique names for this test instance
        self.company_a = f"{self.base_company_a}-{self.test_hash}"
        self.abbr_a = f"{self.base_abbr_a}-{self.test_hash}"
        self.customer = f"{self.base_customer.split('@')[0]}+{self.test_hash}@korvexdev.cc" if "@" in self.base_customer else f"{self.base_customer}+{self.test_hash}"
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

        _ensure_secuencia(self.company_a, "E32")

        self.print_format_html = frappe.get_doc("Print Format", "Representacion Impresa e-CF").html

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

    def _submitted_invoice(self):
        si = frappe.new_doc("Sales Invoice")
        si.company = self.company_a
        si.customer = self.customer
        si.currency = "DOP"
        si.conversion_rate = 1
        si.append(
            "items",
            {
                "item_code": self.item,
                "qty": 1,
                "rate": 1500,
                "income_account": f"Sales - {self.abbr_a}",
                "cost_center": f"Main - {self.abbr_a}",
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
        except (frappe.DoesNotExistError, frappe.ValidationError):
            pass

    def test_renders_with_encf_and_pending_qr_placeholder(self):
        si = self._submitted_invoice()
        html = frappe.render_template(self.print_format_html, {"doc": si})

        self.assertIn(self.customer, html)
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
        si.company = self.company_a
        si.customer = self.customer
        si.currency = "DOP"
        si.conversion_rate = 1
        si.append(
            "items",
            {
                "item_code": self.item,
                "qty": 1,
                "rate": 100,
                "income_account": f"Sales - {self.abbr_a}",
                "cost_center": f"Main - {self.abbr_a}",
            },
        )
        si.insert()
        self.addCleanup(self._cleanup_invoice, si.name)

        html = frappe.render_template(self.print_format_html, {"doc": si})
        self.assertIn("Pendiente de generar", html)
