"""Integration tests for thermal printing (S4.4) — FIXTURES AISLADAS (FASE 5.3).

Tests cover:
- Thermal receipt HTML generation
- ESC/POS command generation
- QR code inclusion from ECF
- Print queue operations
- Offline/online queue sync

Cada test usa setUp/tearDown independiente con datos únicos (generate_hash)
para evitar contaminación entre tests en CI paralelo.
"""

import json
import os

import frappe
from frappe.tests import IntegrationTestCase


class TestThermalPrint(IntegrationTestCase):
    """Tests de impresión térmica con fixtures aisladas por test."""

    def setUp(self):
        """Setup aislado por test - crea datos únicos con generate_hash."""
        frappe.set_user("Administrator")
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests
        before_tests()

        # Generar sufijo único para este test
        self.test_hash = frappe.generate_hash(8)
        self.company = "_Test Company KORVEXCIO A"
        self.abbr = "_TCKA"
        self.customer_name = f"_Test Customer Thermal {self.test_hash}"
        self.item_code = f"_Test Item Thermal {self.test_hash}"

        # Crear customer único
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": self.customer_name,
            "customer_group": "Commercial",
            "territory": "All Territories",
        }).insert()

        # Crear item único
        self.item = frappe.get_doc({
            "doctype": "Item",
            "item_code": self.item_code,
            "item_name": self.item_code,
            "item_group": "All Item Groups",
            "is_stock_item": 0,
            "stock_uom": "Nos",
        }).insert()

        # Asegurar secuencia E32 para company
        seq_name = f"{self.company}-E32"
        if not frappe.db.exists("Secuencia eNCF", seq_name):
            frappe.get_doc({
                "doctype": "Secuencia eNCF",
                "company": self.company,
                "tipo_ecf": "E32",
                "desde": 1,
                "hasta": 999999,
                "siguiente": 1,
                "fecha_vencimiento": "2027-12-31",
            }).insert()

    def tearDown(self):
        """Limpieza completa por test - elimina datos creados."""
        frappe.set_user("Administrator")
        # Limpiar en orden inverso de dependencias
        try:
            # ECFs
            for ecf_name in frappe.get_all("ECF", filters={"reference_doctype": "Sales Invoice"}, pluck="name"):
                try:
                    doc = frappe.get_doc("ECF", ecf_name)
                    if doc.docstatus == 1:
                        doc.cancel()
                    frappe.delete_doc("ECF", ecf_name, force=True, ignore_permissions=True)
                except (frappe.DoesNotExistError, frappe.ValidationError):
                    pass

            # Sales Invoices
            for si_name in frappe.get_all("Sales Invoice", filters={"customer": self.customer_name}, pluck="name"):
                try:
                    doc = frappe.get_doc("Sales Invoice", si_name)
                    if doc.docstatus == 1:
                        doc.cancel()
                    frappe.delete_doc("Sales Invoice", si_name, force=True, ignore_permissions=True)
                except (frappe.DoesNotExistError, frappe.ValidationError):
                    pass

            # Print Queue
            for pq_name in frappe.get_all("ECF Print Queue", filters={"company": self.company}, pluck="name"):
                try:
                    frappe.delete_doc("ECF Print Queue", pq_name, force=True, ignore_permissions=True)
                except (frappe.DoesNotExistError, frappe.ValidationError):
                    pass

            # Customer
            if frappe.db.exists("Customer", self.customer_name):
                frappe.delete_doc("Customer", self.customer_name, force=True, ignore_permissions=True)

            # Item
            if frappe.db.exists("Item", self.item_code):
                frappe.delete_doc("Item", self.item_code, force=True, ignore_permissions=True)

        except (frappe.DoesNotExistError, frappe.ValidationError):
            pass

    def _submitted_invoice(self, with_ecf: bool = False) -> str:
        """Crea y somete una Sales Invoice de prueba."""
        si = frappe.new_doc("Sales Invoice")
        si.company = self.company
        si.customer = self.customer_name
        si.currency = "DOP"
        si.conversion_rate = 1
        si.append(
            "items",
            {
                "item_code": self.item_code,
                "qty": 2,
                "rate": 1500,
                "income_account": f"Sales - {self.abbr}",
                "cost_center": f"Main - {self.abbr}",
            },
        )
        si.insert()
        si.submit()
        return si.name

    def test_generate_html_receipt_basic(self):
        """Test HTML receipt generation without ECF data."""
        invoice_name = self._submitted_invoice(with_ecf=False)

        from korvexcio.ecf.thermal_print import generate_thermal_receipt_html

        html = generate_thermal_receipt_html(invoice_name)

        # Check basic structure
        self.assertIn("<html", html)
        self.assertIn("FACTURA DE VENTA", html)
        self.assertIn(self.customer_name, html)
        self.assertIn(invoice_name, html)
        self.assertIn(self.item_code, html)
        self.assertIn("1,500.00", html)  # rate
        self.assertIn("3,000.00", html)  # amount (2 * 1500)
        self.assertIn("ITBIS", html)
        self.assertIn("TOTAL", html)
        self.assertIn("¡Gracias por su compra!", html)

        # QR should show placeholder
        self.assertIn("QR pendiente", html)
        self.assertIn("Se genera al confirmar con DGII", html)

    def test_generate_html_receipt_with_ecf(self):
        """Test HTML receipt generation with ECF data (QR code)."""
        invoice_name = self._submitted_invoice(with_ecf=True)

        # Get the ECF and add QR URL
        ecf_name = frappe.db.get_value(
            "ECF", {"reference_doctype": "Sales Invoice", "reference_name": invoice_name}, "name"
        )
        frappe.db.set_value("ECF", ecf_name, "qr_url", "https://ecf.dgii.gov.do/verificar?encf=E3200000001")
        frappe.db.set_value("ECF", ecf_name, "track_id", "TRACK123456")
        frappe.db.set_value("ECF", ecf_name, "codigo_seguridad", "A1B2C3D4")

        from korvexcio.ecf.thermal_print import generate_thermal_receipt_html

        html = generate_thermal_receipt_html(invoice_name)

        # Check ECF data is present
        self.assertIn("e-NCF:", html)
        self.assertIn("REPRESENTACIÓN IMPRESA e-CF", html)
        self.assertIn("Verifique en:", html)
        self.assertIn("https://ecf.dgii.gov.do/verificar?encf=E3200000001", html)
        self.assertIn("TrackID: TRACK123456", html)
        self.assertIn("Cod. Seguridad: A1B2C3D4", html)

        # QR code should be embedded as data URI
        self.assertIn('src="data:image/svg+xml;base64,', html)

    def test_generate_escpos_receipt_basic(self):
        """Test ESC/POS binary generation without ECF data."""
        invoice_name = self._submitted_invoice(with_ecf=False)

        from korvexcio.ecf.thermal_print import generate_thermal_receipt_escpos

        escpos = generate_thermal_receipt_escpos(invoice_name)

        # Should be valid bytes
        self.assertIsInstance(escpos, bytes)
        self.assertGreater(len(escpos), 0)

        # Check for ESC/POS initialization
        self.assertIn(b"\x1b\x40", escpos)  # ESC @ init

        # Check for company name (encoded)
        self.assertIn("KORVEXCIO".encode("utf-8"), escpos)

        # Check for invoice info
        self.assertIn(invoice_name.encode("utf-8"), escpos)
        self.assertIn(self.customer_name.encode("utf-8"), escpos)

        # Check for item
        self.assertIn(self.item_code.encode("utf-8"), escpos)

        # Check for totals
        self.assertIn("TOTAL".encode("utf-8"), escpos)

        # Check for cut command
        self.assertIn(b"\x1d\x56\x00", escpos)  # GS V cut

    def test_generate_escpos_receipt_with_ecf(self):
        """Test ESC/POS binary generation with ECF data (QR code)."""
        invoice_name = self._submitted_invoice(with_ecf=True)

        ecf_name = frappe.db.get_value(
            "ECF", {"reference_doctype": "Sales Invoice", "reference_name": invoice_name}, "name"
        )
        frappe.db.set_value("ECF", ecf_name, "qr_url", "https://ecf.dgii.gov.do/verificar?encf=E3200000001")
        frappe.db.set_value("ECF", ecf_name, "track_id", "TRACK123456")
        frappe.db.set_value("ECF", ecf_name, "codigo_seguridad", "A1B2C3D4")

        from korvexcio.ecf.thermal_print import generate_thermal_receipt_escpos

        escpos = generate_thermal_receipt_escpos(invoice_name)

        # Check for QR code ESC/POS commands
        self.assertIn(b"\x1d\x28\x6b", escpos)  # GS ( k

        # Check for e-CF specific text
        self.assertIn("REPRESENTACION IMPRESA e-CF".encode("utf-8"), escpos)
        self.assertIn("TrackID: TRACK123456".encode("utf-8"), escpos)
        self.assertIn("Cod. Seguridad: A1B2C3D4".encode("utf-8"), escpos)

    def test_save_receipt_for_test(self):
        """Test saving receipt files for development testing."""
        invoice_name = self._submitted_invoice(with_ecf=True)

        ecf_name = frappe.db.get_value(
            "ECF", {"reference_doctype": "Sales Invoice", "reference_name": invoice_name}, "name"
        )
        frappe.db.set_value("ECF", ecf_name, "qr_url", "https://ecf.dgii.gov.do/verificar?encf=E3200000001")

        from korvexcio.ecf.thermal_print import save_receipt_for_test

        result = save_receipt_for_test(invoice_name, "/tmp/korvexcio_thermal_test_unit")

        self.assertIn("html", result)
        self.assertIn("escpos", result)
        self.assertIn("escpos_b64", result)

        # Verify files exist
        self.assertTrue(os.path.exists(result["html"]))
        self.assertTrue(os.path.exists(result["escpos"]))
        self.assertTrue(os.path.exists(result["escpos_b64"]))

        # Verify HTML is valid
        with open(result["html"], encoding="utf-8") as f:
            html = f.read()
        self.assertIn("<html", html)
        self.assertIn("REPRESENTACIÓN IMPRESA e-CF", html)

        # Verify ESC/POS is valid
        with open(result["escpos"], "rb") as f:
            escpos = f.read()
        self.assertIn(b"\x1b\x40", escpos)

        # Verify base64 matches
        with open(result["escpos_b64"]) as f:
            b64 = f.read()
        import base64
        self.assertEqual(base64.b64decode(b64), escpos)

    def test_thermal_receipt_builder_class(self):
        """Test ThermalReceiptBuilder class directly."""
        invoice_name = self._submitted_invoice(with_ecf=True)

        invoice = frappe.get_doc("Sales Invoice", invoice_name).as_dict()
        ecf = frappe.get_doc("ECF", {"reference_doctype": "Sales Invoice", "reference_name": invoice_name}).as_dict()

        from korvexcio.ecf.thermal_print import ThermalReceiptBuilder

        builder = ThermalReceiptBuilder(invoice, ecf)

        # Test HTML
        html = builder.build_html()
        self.assertIn("<html", html)
        self.assertIn("FACTURA DE VENTA", html)

        # Test ESC/POS
        escpos = builder.build_escpos()
        self.assertIsInstance(escpos, bytes)
        self.assertIn(b"\x1b\x40", escpos)

    def test_credit_note_receipt(self):
        """Test receipt generation for credit note (is_return)."""
        # Create a return invoice
        si = frappe.new_doc("Sales Invoice")
        si.company = self.company
        si.customer = self.customer_name
        si.currency = "DOP"
        si.conversion_rate = 1
        si.is_return = 1
        si.append(
            "items",
            {
                "item_code": self.item_code,
                "qty": 1,
                "rate": 1000,
                "income_account": f"Sales - {self.abbr}",
                "cost_center": f"Main - {self.abbr}",
            },
        )
        si.insert()
        si.submit()

        self.addCleanup(lambda: self._cleanup_invoice(si.name))

        from korvexcio.ecf.thermal_print import generate_thermal_receipt_html

        html = generate_thermal_receipt_html(si.name)

        self.assertIn("NOTA DE CRÉDITO", html)
        self.assertIn("e-NCF:", html)  # Should still show e-NCF for credit note

    def _cleanup_invoice(self, name):
        """Cleanup helper for single invoice."""
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

    def test_print_queue_operations(self):
        """Test server-side print queue operations."""
        invoice_name = self._submitted_invoice(with_ecf=True)

        from korvexcio.ecf.print_queue import queue_print_job, get_pending_print_count, process_print_queue

        # Queue a print job
        queue_name = queue_print_job(invoice_name, self.company, priority=1)
        self.assertTrue(queue_name.startswith("PQ-"))

        # Check count
        count = get_pending_print_count(self.company)
        self.assertEqual(count, 1)

        # Process queue (in development mode, saves to file)
        result = process_print_queue(limit=5)
        self.assertEqual(result["processed"], 1)
        self.assertEqual(result["failed"], 0)

        # Check status
        queue_doc = frappe.get_doc("ECF Print Queue", queue_name)
        self.assertEqual(queue_doc.status, "Completed")

    def test_print_queue_duplicate_prevention(self):
        """Test that duplicate print jobs are not created."""
        invoice_name = self._submitted_invoice(with_ecf=True)

        from korvexcio.ecf.print_queue import queue_print_job

        queue_name1 = queue_print_job(invoice_name, self.company)
        queue_name2 = queue_print_job(invoice_name, self.company)

        # Should return same queue name
        self.assertEqual(queue_name1, queue_name2)

    def test_pos_queue_print_api(self):
        """Test POS API endpoint for queuing prints."""
        invoice_name = self._submitted_invoice(with_ecf=True)

        from korvexcio.ecf.print_queue import pos_queue_print, pos_get_print_status

        # Queue via API
        result = pos_queue_print(invoice_name)
        self.assertTrue(result["success"])
        self.assertEqual(result["invoice_name"], invoice_name)
        self.assertEqual(result["status"], "queued")

        # Check status
        status = pos_get_print_status(invoice_name)
        self.assertEqual(status["status"], "pending")

    def test_pos_sync_offline_prints(self):
        """Test syncing offline prints from POS."""
        invoice_name = self._submitted_invoice(with_ecf=True)

        from korvexcio.ecf.print_queue import pos_sync_offline_prints

        # Simulate offline prints from POS
        offline_data = json.dumps([
            {
                "invoice_name": invoice_name,
                "company": self.company,
                "timestamp": "2026-09-05T10:00:00Z",
            }
        ])

        result = pos_sync_offline_prints(offline_data)
        self.assertTrue(result["success"])
        self.assertEqual(result["synced"], 1)

        # Verify queue was created
        queue = frappe.get_all("ECF Print Queue", filters={"invoice_name": invoice_name}, pluck="name")
        self.assertEqual(len(queue), 1)

    def test_qr_code_generation_in_receipt(self):
        """Test that QR code is properly generated and embedded."""
        from korvexcio.ecf.qr import qr_svg_data_uri

        test_url = "https://ecf.dgii.gov.do/verificar?encf=E3200000001"
        data_uri = qr_svg_data_uri(test_url)

        # Should be valid data URI
        self.assertTrue(data_uri.startswith("data:image/svg+xml;base64,"))

        # Decode and verify it's valid SVG
        import base64
        svg_bytes = base64.b64decode(data_uri.split(",")[1])
        svg = svg_bytes.decode("utf-8")
        self.assertIn("<svg", svg)
        self.assertIn("xmlns", svg)

    def test_thermal_print_with_payments(self):
        """Test receipt includes payment information."""
        invoice_name = self._submitted_invoice(with_ecf=True)

        # Add payments to the invoice
        si = frappe.get_doc("Sales Invoice", invoice_name)
        si.append("payments", {"mode_of_payment": "Efectivo", "amount": 3000})
        si.append("payments", {"mode_of_payment": "Tarjeta", "amount": 500})
        si.paid_amount = 3500
        si.change_amount = 0
        si.outstanding_amount = 0
        si.save()

        from korvexcio.ecf.thermal_print import generate_thermal_receipt_html

        html = generate_thermal_receipt_html(invoice_name)

        # Check payments section
        self.assertIn("FORMAS DE PAGO", html)
        self.assertIn("Efectivo", html)
        self.assertIn("Tarjeta", html)
        self.assertIn("Total Pagado", html)
        self.assertIn("3,500.00", html)  # paid amount


class TestThermalPrintOfflineQueue(IntegrationTestCase):
    """Tests for offline print queue (POSNext IndexedDB integration) - aislados."""

    def setUp(self):
        frappe.set_user("Administrator")
        if not frappe.local.lang:
            frappe.local.lang = "en"

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_offline_queue_schema_includes_prints(self):
        """Verify the offline DB schema can be extended for prints."""
        from korvexcio.ecf.print_queue import pos_sync_offline_prints

        # Test with empty array
        result = pos_sync_offline_prints("[]")
        self.assertTrue(result["success"])
        self.assertEqual(result["synced"], 0)

        # Test with invalid JSON
        result = pos_sync_offline_prints("invalid")
        self.assertFalse(result["success"])
        self.assertIn("Invalid JSON", result["error"])