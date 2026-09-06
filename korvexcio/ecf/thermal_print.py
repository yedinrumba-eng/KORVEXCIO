"""Thermal print utilities for 80mm receipts with e-CF QR code (S4.4).

This module provides ESC/POS command generation and HTML-to-thermal
conversion for printing e-CF compliant receipts on thermal printers.
No hardware dependency for development - outputs can be tested via
file capture or virtual printer."""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Any

import frappe


# 80mm thermal printer constants (at 203 DPI standard)
PRINTER_WIDTH_MM = 80
PRINTER_WIDTH_DOTS = 576  # 80mm * 203 DPI / 25.4 ≈ 640, but ESC/POS typically 576
CHAR_WIDTH_DOTS = 12
CHAR_HEIGHT_DOTS = 24
MAX_CHARS_PER_LINE = PRINTER_WIDTH_DOTS // CHAR_WIDTH_DOTS  # 48 chars


def _center_text(text: str, width: int = MAX_CHARS_PER_LINE) -> str:
    """Center text within printer width."""
    if len(text) >= width:
        return text[:width]
    padding = (width - len(text)) // 2
    return " " * padding + text


def _right_align(label: str, value: str, width: int = MAX_CHARS_PER_LINE) -> str:
    """Right-align value with label on left."""
    combined = f"{label}{value}"
    if len(combined) >= width:
        return combined[:width]
    padding = width - len(combined)
    return label + " " * padding + value


def _format_currency(amount: float | int | None) -> str:
    """Format currency for Dominican Republic (DOP)."""
    if amount is None:
        return "0.00"
    return f"{float(amount):,.2f}"


def _format_qty(qty: float | int | None) -> str:
    """Format quantity without decimals if whole number."""
    if qty is None:
        return "0"
    q = float(qty)
    return str(int(q)) if q == int(q) else f"{q:.2f}"


class ThermalReceiptBuilder:
    """Builds thermal receipt content as ESC/POS commands or HTML.

    Usage:
        builder = ThermalReceiptBuilder(invoice_data)
        escpos_bytes = builder.build_escpos()
        html_content = builder.build_html()
    """

    def __init__(self, invoice_data: dict[str, Any], ecf_data: dict[str, Any] | None = None):
        self.invoice = invoice_data
        self.ecf = ecf_data
        self.company = frappe.get_doc("Company", invoice_data.get("company")) if invoice_data.get("company") else None

    def build_escpos(self) -> bytes:
        """Generate ESC/POS binary commands for thermal printer."""
        commands = bytearray()

        # Initialize printer
        commands.extend(b"\x1b\x40")  # ESC @ - Initialize

        # Header
        commands.extend(self._escpos_header())

        # Invoice info
        commands.extend(self._escpos_invoice_info())

        # Items
        commands.extend(self._escpos_items())

        # Totals
        commands.extend(self._escpos_totals())

        # Payments
        commands.extend(self._escpos_payments())

        # QR Code (e-CF)
        commands.extend(self._escpos_qr_code())

        # Footer
        commands.extend(self._escpos_footer())

        # Cut paper
        commands.extend(b"\x1d\x56\x00")  # GS V m=0 - Full cut

        return bytes(commands)

    def _escpos_header(self) -> bytes:
        """Build header section."""
        out = bytearray()

        if self.company:
            # Company name - double height/width
            out.extend(b"\x1b\x21\x30")  # ESC ! n - Double height + double width
            out.extend(_center_text(self.company.company_name).encode("utf-8"))
            out.extend(b"\n")

            # RNC
            out.extend(b"\x1b\x21\x00")  # Normal size
            rnc = getattr(self.company, "tax_id", "") or ""
            if rnc:
                out.extend(_center_text(f"RNC: {rnc}").encode("utf-8"))
                out.extend(b"\n")

            # Address
            address_parts = []
            if getattr(self.company, "address_line1", ""):
                address_parts.append(self.company.address_line1)
            if getattr(self.company, "city", "") or getattr(self.company, "state", ""):
                city_state = " ".join(filter(None, [getattr(self.company, "city", ""), getattr(self.company, "state", "")]))
                address_parts.append(city_state)
            if getattr(self.company, "country", ""):
                address_parts.append(self.company.country)

            for line in address_parts:
                out.extend(_center_text(line).encode("utf-8"))
                out.extend(b"\n")

        # Separator
        out.extend(b"\x1b\x21\x00")  # Normal
        out.extend("-" * MAX_CHARS_PER_LINE .encode("utf-8"))
        out.extend(b"\n")

        # Document type
        doc_type = "NOTA DE CREDITO" if self.invoice.get("is_return") else "FACTURA DE VENTA"
        out.extend(b"\x1b\x21\x20")  # Double height
        out.extend(_center_text(doc_type).encode("utf-8"))
        out.extend(b"\n")
        out.extend(b"\x1b\x21\x00")  # Normal

        # e-NCF if available
        if self.ecf and self.ecf.get("encf"):
            out.extend(_center_text(f"e-NCF: {self.ecf['encf']}").encode("utf-8"))
            out.extend(b"\n")

        return out

    def _escpos_invoice_info(self) -> bytes:
        """Build invoice information section."""
        out = bytearray()

        out.extend(f"Factura: {self.invoice.get('name', '')}\n".encode("utf-8"))
        out.extend(f"Fecha: {self.invoice.get('posting_date', '')}\n".encode("utf-8"))

        customer = self.invoice.get("customer_name", "")
        if customer:
            out.extend(f"Cliente: {customer}\n".encode("utf-8"))

        buyer_rnc = self.invoice.get("tax_id", "") or ""
        if buyer_rnc:
            out.extend(f"RNC Cliente: {buyer_rnc}\n".encode("utf-8"))

        out.extend("-" * MAX_CHARS_PER_LINE .encode("utf-8"))
        out.extend(b"\n")

        return out

    def _escpos_items(self) -> bytes:
        """Build items table."""
        out = bytearray()

        # Header
        header = f"{'Item':<24}{'Cant':>6}{'Precio':>9}{'Monto':>9}\n"
        out.extend(header.encode("utf-8"))
        out.extend("-" * MAX_CHARS_PER_LINE .encode("utf-8"))
        out.extend(b"\n")

        items = self.invoice.get("items", [])
        for item in items:
            item_name = item.get("item_name") or item.get("item_code") or ""
            qty = _format_qty(item.get("qty") or item.get("quantity"))
            rate = _format_currency(item.get("rate"))
            amount = _format_currency(item.get("amount"))

            # Truncate item name if too long
            if len(item_name) > 24:
                item_name = item_name[:21] + "..."

            line = f"{item_name:<24}{qty:>6}{rate:>9}{amount:>9}\n"
            out.extend(line.encode("utf-8"))

            # Discount line if applicable
            discount = item.get("discount_amount", 0)
            if discount and float(discount) > 0:
                disc_line = f"{'  Desc.':<24}{'':>6}{'':>9}-{_format_currency(discount):>8}\n"
                out.extend(disc_line.encode("utf-8"))

        out.extend("-" * MAX_CHARS_PER_LINE .encode("utf-8"))
        out.extend(b"\n")

        return out

    def _escpos_totals(self) -> bytes:
        """Build totals section."""
        out = bytearray()

        subtotal = float(self.invoice.get("grand_total", 0)) - float(self.invoice.get("total_taxes_and_charges", 0))
        tax = float(self.invoice.get("total_taxes_and_charges", 0))
        total = float(self.invoice.get("grand_total", 0))
        discount = float(self.invoice.get("discount_amount", 0) or 0)

        out.extend(_right_align("Subtotal: ", _format_currency(subtotal)).encode("utf-8"))
        out.extend(b"\n")
        out.extend(_right_align("ITBIS: ", _format_currency(tax)).encode("utf-8"))
        out.extend(b"\n")

        if discount > 0:
            out.extend(_right_align("Descuento: ", f"-{_format_currency(discount)}").encode("utf-8"))
            out.extend(b"\n")

        # Grand total - double height
        out.extend(b"\x1b\x21\x10")  # Double height
        out.extend(_right_align("TOTAL: ", _format_currency(total)).encode("utf-8"))
        out.extend(b"\n")
        out.extend(b"\x1b\x21\x00")  # Normal
        out.extend(b"\n")

        return out

    def _escpos_payments(self) -> bytes:
        """Build payments section."""
        out = bytearray()

        payments = self.invoice.get("payments", [])
        if not payments:
            return out

        out.extend("FORMAS DE PAGO:\n".encode("utf-8"))
        out.extend("-" * MAX_CHARS_PER_LINE .encode("utf-8"))
        out.extend(b"\n")

        for payment in payments:
            mode = payment.get("mode_of_payment", "EFECTIVO")
            amount = _format_currency(payment.get("amount", 0))
            out.extend(_right_align(f"{mode}: ", amount).encode("utf-8"))
            out.extend(b"\n")

        paid = _format_currency(self.invoice.get("paid_amount", 0))
        out.extend(_right_align("Total Pagado: ", paid).encode("utf-8"))
        out.extend(b"\n")

        change = self.invoice.get("change_amount", 0)
        if change and float(change) > 0:
            out.extend(_right_align("Cambio: ", _format_currency(change)).encode("utf-8"))
            out.extend(b"\n")

        outstanding = self.invoice.get("outstanding_amount", 0)
        if outstanding and float(outstanding) > 0:
            out.extend(_right_align("PENDIENTE: ", _format_currency(outstanding)).encode("utf-8"))
            out.extend(b"\n")

        out.extend("-" * MAX_CHARS_PER_LINE .encode("utf-8"))
        out.extend(b"\n")

        return out

    def _escpos_qr_code(self) -> bytes:
        """Build QR code section for e-CF verification."""
        out = bytearray()

        if not self.ecf or not self.ecf.get("qr_url"):
            out.extend(_center_text("QR pendiente").encode("utf-8"))
            out.extend(b"\n")
            out.extend(_center_text("Se genera al confirmar con DGII").encode("utf-8"))
            out.extend(b"\n\n")
            return out

        # Print QR code using GS ( k command (ESC/POS)
        qr_url = self.ecf["qr_url"]

        out.extend(b"\x1b\x21\x00")  # Normal size
        out.extend(_center_text("REPRESENTACION IMPRESA e-CF").encode("utf-8"))
        out.extend(b"\n")
        out.extend(_center_text("Verifique en:").encode("utf-8"))
        out.extend(b"\n")
        out.extend(_center_text(qr_url).encode("utf-8"))
        out.extend(b"\n\n")

        # QR Code: GS ( k pL pH cn fn n1 n2
        # Model 2, size 3 (small), error correction 48 (M)
        qr_bytes = qr_url.encode("utf-8")
        qr_len = len(qr_bytes) + 3
        pL = qr_len & 0xFF
        pH = (qr_len >> 8) & 0xFF

        # GS ( k - Select QR code model
        out.extend(b"\x1d\x28\x6b\x04\x00\x31\x41\x32\x00")  # Model 2

        # GS ( k - Set size (1-16, 3 is typical for 80mm)
        out.extend(b"\x1d\x28\x6b\x03\x00\x31\x43\x03")

        # GS ( k - Set error correction (48=M, 49=L, 50=Q, 51=H)
        out.extend(b"\x1d\x28\x6b\x03\x00\x31\x45\x30")

        # GS ( k - Store QR code data
        out.extend(b"\x1d\x28\x6b")
        out.extend(bytes([pL, pH]))
        out.extend(b"\x31\x50\x30")
        out.extend(qr_bytes)

        # GS ( k - Print QR code
        out.extend(b"\x1d\x28\x6b\x03\x00\x31\x51\x30")

        out.extend(b"\n\n")

        # TrackID and security code
        if self.ecf.get("track_id"):
            out.extend(_center_text(f"TrackID: {self.ecf['track_id']}").encode("utf-8"))
            out.extend(b"\n")
        if self.ecf.get("codigo_seguridad"):
            out.extend(_center_text(f"Cod. Seguridad: {self.ecf['codigo_seguridad']}").encode("utf-8"))
            out.extend(b"\n")

        return out

    def _escpos_footer(self) -> bytes:
        """Build footer section."""
        out = bytearray()

        out.extend(b"\n")
        out.extend(_center_text("¡Gracias por su compra!").encode("utf-8"))
        out.extend(b"\n")
        out.extend(_center_text("Powered by Korvex").encode("utf-8"))
        out.extend(b"\n\n\n")

        return out

    def build_html(self) -> str:
        """Build HTML representation for browser-based printing (testing without hardware)."""
        company_name = self.company.company_name if self.company else "KORVEXCIO"
        company_rnc = getattr(self.company, "tax_id", "") if self.company else ""
        company_address = ""
        if self.company:
            parts = []
            if getattr(self.company, "address_line1", ""):
                parts.append(self.company.address_line1)
            if getattr(self.company, "city", "") or getattr(self.company, "state", ""):
                parts.append(" ".join(filter(None, [getattr(self.company, "city", ""), getattr(self.company, "state", "")])))
            if getattr(self.company, "country", ""):
                parts.append(self.company.country)
            company_address = ", ".join(parts)

        doc_type = "NOTA DE CRÉDITO" if self.invoice.get("is_return") else "FACTURA DE VENTA"
        encf = self.ecf.get("encf") if self.ecf else None
        qr_url = self.ecf.get("qr_url") if self.ecf else None
        track_id = self.ecf.get("track_id") if self.ecf else None
        codigo_seguridad = self.ecf.get("codigo_seguridad") if self.ecf else None

        items_html = ""
        for item in self.invoice.get("items", []):
            item_name = item.get("item_name") or item.get("item_code") or ""
            qty = _format_qty(item.get("qty") or item.get("quantity"))
            rate = _format_currency(item.get("rate"))
            amount = _format_currency(item.get("amount"))
            discount = item.get("discount_amount", 0)

            items_html += f"""
            <tr>
                <td>{item_name}</td>
                <td class="text-right">{qty}</td>
                <td class="text-right">{rate}</td>
                <td class="text-right">{amount}</td>
            </tr>"""
            if discount and float(discount) > 0:
                items_html += f"""
            <tr class="discount">
                <td colspan="3">Descuento</td>
                <td class="text-right">-{_format_currency(discount)}</td>
            </tr>"""

        subtotal = float(self.invoice.get("grand_total", 0)) - float(self.invoice.get("total_taxes_and_charges", 0))
        tax = float(self.invoice.get("total_taxes_and_charges", 0))
        total = float(self.invoice.get("grand_total", 0))
        discount_total = float(self.invoice.get("discount_amount", 0) or 0)

        payments_html = ""
        for payment in self.invoice.get("payments", []):
            mode = payment.get("mode_of_payment", "EFECTIVO")
            amount = _format_currency(payment.get("amount", 0))
            payments_html += f"""
            <div class="payment-row">
                <span>{mode}:</span>
                <span>{amount}</span>
            </div>"""

        paid = _format_currency(self.invoice.get("paid_amount", 0))
        change = self.invoice.get("change_amount", 0)
        outstanding = self.invoice.get("outstanding_amount", 0)

        # Generate QR code as base64 SVG for HTML
        qr_html = ""
        if qr_url:
            from korvexcio.ecf.qr import qr_svg_data_uri
            qr_data_uri = qr_svg_data_uri(qr_url)
            qr_html = f'<img src="{qr_data_uri}" alt="QR e-CF" class="qr-code">'
        else:
            qr_html = '<div class="qr-placeholder">QR pendiente<br><small>Se genera al confirmar con DGII</small></div>'

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>e-CF Receipt - {self.invoice.get('name', '')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Courier New', monospace;
            width: 80mm;
            max-width: 80mm;
            margin: 0 auto;
            padding: 10px;
            font-size: 12px;
            line-height: 1.4;
            background: white;
        }}
        .receipt {{ width: 100%; }}
        .header {{
            text-align: center;
            margin-bottom: 15px;
            border-bottom: 2px dashed #000;
            padding-bottom: 10px;
        }}
        .company-name {{ font-size: 16px; font-weight: bold; margin-bottom: 3px; }}
        .company-rnc {{ font-size: 10px; margin-bottom: 2px; }}
        .company-address {{ font-size: 9px; color: #666; }}
        .doc-type {{ font-size: 14px; font-weight: bold; margin: 10px 0; }}
        .encf {{ font-size: 11px; font-weight: bold; margin-bottom: 10px; }}
        .invoice-info {{
            font-size: 11px;
            margin-bottom: 10px;
        }}
        .invoice-info div {{ display: flex; justify-content: space-between; margin-bottom: 2px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
        th {{ text-align: left; border-bottom: 1px dashed #000; padding-bottom: 3px; font-weight: bold; }}
        td {{ padding: 2px 0; }}
        .text-right {{ text-align: right; }}
        .discount {{ color: #666; font-size: 10px; }}
        .totals {{
            margin-top: 10px;
            border-top: 1px dashed #000;
            padding-top: 10px;
            text-align: right;
        }}
        .total-row {{ display: flex; justify-content: space-between; margin-bottom: 3px; }}
        .grand-total {{ font-size: 16px; font-weight: bold; border-top: 2px solid #000; padding-top: 8px; margin-top: 8px; }}
        .payments {{
            margin-top: 15px;
            border-top: 1px dashed #000;
            padding-top: 10px;
            font-size: 11px;
        }}
        .payment-row {{ display: flex; justify-content: space-between; margin-bottom: 2px; }}
        .qr-section {{
            margin-top: 20px;
            text-align: center;
            border-top: 2px dashed #000;
            padding-top: 15px;
        }}
        .qr-title {{ font-size: 11px; font-weight: bold; margin-bottom: 5px; }}
        .qr-url {{ font-size: 8px; color: #666; margin-bottom: 10px; word-break: break-all; }}
        .qr-code {{ width: 110px; height: 110px; }}
        .qr-placeholder {{ font-size: 9px; color: #888; width: 110px; margin: 0 auto; }}
        .track-info {{ font-size: 9px; margin-top: 10px; color: #666; }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            padding-top: 10px;
            border-top: 2px dashed #000;
            font-size: 10px;
            color: #666;
        }}
        @media print {{
            @page {{ size: 80mm auto; margin: 0; }}
            body {{ width: 80mm; padding: 5mm; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="receipt">
        <div class="header">
            <div class="company-name">{company_name}</div>
            {f'<div class="company-rnc">RNC: {company_rnc}</div>' if company_rnc else ''}
            {f'<div class="company-address">{company_address}</div>' if company_address else ''}
        </div>

        <div class="doc-type">{doc_type}</div>
        {f'<div class="encf">e-NCF: {encf}</div>' if encf else ''}

        <div class="invoice-info">
            <div><span>Factura:</span><span>{self.invoice.get("name", "")}</span></div>
            <div><span>Fecha:</span><span>{self.invoice.get("posting_date", "")}</span></div>
            {f'<div><span>Cliente:</span><span>{self.invoice.get("customer_name", "")}</span></div>' if self.invoice.get("customer_name") else ''}
            {f'<div><span>RNC Cliente:</span><span>{self.invoice.get("tax_id", "")}</span></div>' if self.invoice.get("tax_id") else ''}
        </div>

        <table>
            <thead>
                <tr>
                    <th>Item</th>
                    <th class="text-right">Cant</th>
                    <th class="text-right">Precio</th>
                    <th class="text-right">Monto</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>

        <div class="totals">
            <div class="total-row"><span>Subtotal:</span><span>{_format_currency(subtotal)}</span></div>
            <div class="total-row"><span>ITBIS:</span><span>{_format_currency(tax)}</span></div>
            {f'<div class="total-row" style="color: #28a745;"><span>Descuento:</span><span>-{_format_currency(discount_total)}</span></div>' if discount_total > 0 else ''}
            <div class="total-row grand-total"><span>TOTAL:</span><span>{_format_currency(total)}</span></div>
        </div>

        {f'''
        <div class="payments">
            <div style="font-weight: bold; margin-bottom: 5px;">FORMAS DE PAGO:</div>
            {payments_html}
            <div class="payment-row"><span>Total Pagado:</span><span>{paid}</span></div>
            {f'<div class="payment-row"><span>Cambio:</span><span>{_format_currency(change)}</span></div>' if change and float(change) > 0 else ''}
            {f'<div class="payment-row" style="font-weight: bold; color: #dc3545;"><span>PENDIENTE:</span><span>{_format_currency(outstanding)}</span></div>' if outstanding and float(outstanding) > 0 else ''}
        </div>
        ''' if self.invoice.get("payments") else ''}

        <div class="qr-section">
            <div class="qr-title">REPRESENTACIÓN IMPRESA e-CF</div>
            <div class="qr-url">Verifique en: {qr_url or "Pendiente de DGII"}</div>
            {qr_html}
            {f'<div class="track-info">TrackID: {track_id}</div>' if track_id else ''}
            {f'<div class="track-info">Cod. Seguridad: {codigo_seguridad}</div>' if codigo_seguridad else ''}
        </div>

        <div class="footer">
            <div>¡Gracias por su compra!</div>
            <div>Powered by Korvex</div>
        </div>
    </div>

    <div class="no-print" style="text-align: center; margin-top: 20px; padding: 10px;">
        <button onclick="window.print()" style="padding: 10px 20px; font-size: 14px; cursor: pointer; margin-right: 10px;">
            Imprimir Recibo
        </button>
        <button onclick="window.close()" style="padding: 10px 20px; font-size: 14px; cursor: pointer;">
            Cerrar
        </button>
    </div>
</body>
</html>"""
        return html


def generate_thermal_receipt_html(invoice_name: str) -> str:
    """Generate HTML thermal receipt for a Sales Invoice.

    This is the main entry point for the print queue system.
    Can be called from background job or directly for testing.

    Args:
        invoice_name: Name of the Sales Invoice document

    Returns:
        HTML string ready for browser printing
    """
    invoice = frappe.get_doc("Sales Invoice", invoice_name).as_dict()

    # Get linked ECF
    ecf = None
    ecf_name = frappe.get_all(
        "ECF",
        filters={"reference_doctype": "Sales Invoice", "reference_name": invoice_name},
        pluck="name",
        limit=1,
    )
    if ecf_name:
        ecf_doc = frappe.get_doc("ECF", ecf_name[0])
        ecf = {
            "encf": ecf_doc.encf,
            "qr_url": ecf_doc.qr_url,
            "track_id": ecf_doc.track_id,
            "codigo_seguridad": ecf_doc.codigo_seguridad,
            "estado": ecf_doc.estado,
        }

    builder = ThermalReceiptBuilder(invoice, ecf)
    return builder.build_html()


def generate_thermal_receipt_escpos(invoice_name: str) -> bytes:
    """Generate ESC/POS binary for a Sales Invoice.

    For direct thermal printer sending via serial/USB/Bluetooth.

    Args:
        invoice_name: Name of the Sales Invoice document

    Returns:
        ESC/POS command bytes
    """
    invoice = frappe.get_doc("Sales Invoice", invoice_name).as_dict()

    ecf = None
    ecf_name = frappe.get_all(
        "ECF",
        filters={"reference_doctype": "Sales Invoice", "reference_name": invoice_name},
        pluck="name",
        limit=1,
    )
    if ecf_name:
        ecf_doc = frappe.get_doc("ECF", ecf_name[0])
        ecf = {
            "encf": ecf_doc.encf,
            "qr_url": ecf_doc.qr_url,
            "track_id": ecf_doc.track_id,
            "codigo_seguridad": ecf_doc.codigo_seguridad,
            "estado": ecf_doc.estado,
        }

    builder = ThermalReceiptBuilder(invoice, ecf)
    return builder.build_escpos()


def save_receipt_for_test(invoice_name: str, output_dir: str = "/tmp/korvexcio_thermal_test") -> dict[str, str]:
    """Save both HTML and ESC/POS receipt for testing without hardware.

    Args:
        invoice_name: Name of the Sales Invoice
        output_dir: Directory to save test files

    Returns:
        Dict with paths to saved files
    """
    import os

    os.makedirs(output_dir, exist_ok=True)

    html = generate_thermal_receipt_html(invoice_name)
    escpos = generate_thermal_receipt_escpos(invoice_name)

    safe_name = invoice_name.replace("/", "_").replace("\\", "_")
    html_path = os.path.join(output_dir, f"{safe_name}.html")
    escpos_path = os.path.join(output_dir, f"{safe_name}.escpos")
    escpos_b64_path = os.path.join(output_dir, f"{safe_name}.escpos.b64")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    with open(escpos_path, "wb") as f:
        f.write(escpos)

    with open(escpos_b64_path, "w") as f:
        f.write(base64.b64encode(escpos).decode())

    return {
        "html": html_path,
        "escpos": escpos_path,
        "escpos_b64": escpos_b64_path,
    }


def test_thermal_print() -> dict[str, Any]:
    """Test function for bench run-tests --module korvexcio.ecf.test_thermal_print.

    Creates a test invoice and generates receipt outputs.
    """
    from frappe.tests import IntegrationTestCase

    # This is a simple function test, not a full IntegrationTestCase
    # Use save_receipt_for_test with a test invoice

    test_company = "_Test Company KORVEXCIO A"
    if not frappe.db.exists("Company", test_company):
        return {"error": "Test company not found. Run before_tests first."}

    # Find a submitted test invoice
    test_invoice = frappe.get_all(
        "Sales Invoice",
        filters={"company": test_company, "docstatus": 1},
        pluck="name",
        limit=1,
    )

    if not test_invoice:
        return {"error": "No submitted test invoice found"}

    result = save_receipt_for_test(test_invoice[0])
    result["invoice"] = test_invoice[0]
    return result