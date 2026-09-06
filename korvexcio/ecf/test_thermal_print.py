"""Integration tests for thermal printing (S4.4).

Tests cover:
- Thermal receipt HTML generation
- ESC/POS command generation
- QR code inclusion from ECF
- Print queue operations
- Offline/online queue sync
"""

import json
import os

import frappe
from frappe.tests import IntegrationTestCase

COMPANY_A = "_Test Company KORVEXCIO A"
ABBR_A = "_TCKA"
CUSTOMER = "_Test Customer KORVEXCIO Thermal"
ITEM = "_Test Item KORVEXCIO Thermal"


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


class TestThermalPrint(IntegrationTestCase):
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

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    def _submitted_invoice(self, with_ecf: bool = False) -> str:
        """Create and submit a test Sales Invoice."""
        si = frappe.new_doc("Sales Invoice")
        si.company = COMPANY_A
        si.customer = CUSTOMER
        si.currency = "DOP"
        si.conversion_rate = 1
        si.append(
            "items",
            {
                "item_code": ITEM,
                "qty": 2,
                "rate": 1500,
                "income_account": f"Sales - {ABBR_A}",
                "cost_center": f"Main - {ABBR_A}",
            },
        )
        si.insert()
        si.submit()

        self.addCleanup(self._cleanup_invoice, si.name)

        if with_ecf:
            # The on_submit hook creates ECF automatically
            pass

        return si.name

    def _cleanup_invoice(self, name):
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

    def test_generate_html_receipt_basic(self):
        """Test HTML receipt generation without ECF data."""
        invoice_name = self._submitted_invoice(with_ecf=False)

        from korvexcio.ecf.thermal_print import generate_thermal_receipt_html

        html = generate_thermal_receipt_html(invoice_name)

        # Check basic structure
        self.assertIn("<html", html)
        self.assertIn("FACTURA DE VENTA", html)
        self.assertIn(CUSTOMER, html)
        self.assertIn(invoice_name, html)
        self.assertIn(ITEM, html)
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
        self.assertIn(CUSTOMER.encode("utf-8"), escpos)

        # Check for item
        self.assertIn(ITEM.encode("utf-8"), escpos)

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
        # GS ( k commands for QR code
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
        si.company = COMPANY_A
        si.customer = CUSTOMER
        si.currency = "DOP"
        si.conversion_rate = 1
        si.is_return = 1
        si.append(
            "items",
            {
                "item_code": ITEM,
                "qty": 1,
                "rate": 1000,
                "income_account": f"Sales - {ABBR_A}",
                "cost_center": f"Main - {ABBR_A}",
            },
        )
        si.insert()
        si.submit()

        self.addCleanup(self._cleanup_invoice, si.name)

        from korvexcio.ecf.thermal_print import generate_thermal_receipt_html

        html = generate_thermal_receipt_html(si.name)

        self.assertIn("NOTA DE CRÉDITO", html)
        self.assertIn("e-NCF:", html)  # Should still show e-NCF for credit note

    def test_print_queue_operations(self):
        """Test server-side print queue operations."""
        invoice_name = self._submitted_invoice(with_ecf=True)

        from korvexcio.ecf.print_queue import queue_print_job, get_pending_print_count, process_print_queue

        # Queue a print job
        queue_name = queue_print_job(invoice_name, COMPANY_A, priority=1)
        self.assertTrue(queue_name.startswith("PQ-"))

        # Check count
        count = get_pending_print_count(COMPANY_A)
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

        queue_name1 = queue_print_job(invoice_name, COMPANY_A)
        queue_name2 = queue_print_job(invoice_name, COMPANY_A)

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
                "company": COMPANY_A,
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
    """Tests for offline print queue (POSNext IndexedDB integration)."""

    def test_offline_queue_schema_includes_prints(self):
        """Verify the offline DB schema can be extended for prints."""
        # This test documents the expected schema extension
        # The actual POSNext IndexedDB is in JavaScript
        # We verify the Python side can handle the sync format

        from korvexcio.ecf.print_queue import pos_sync_offline_prints

        # Test with empty array
        result = pos_sync_offline_prints("[]")
        self.assertTrue(result["success"])
        self.assertEqual(result["synced"], 0)

        # Test with invalid JSON
        result = pos_sync_offline_prints("invalid")
        self.assertFalse(result["success"])
        self.assertIn("Invalid JSON", result["error"])