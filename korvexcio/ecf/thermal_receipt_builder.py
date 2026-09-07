"""ThermalReceiptBuilder - Core receipt building logic (ESC/POS + HTML).

FASE 4.8: Separado de thermal_print.py para cumplir regla ~300 líneas por archivo.
Este módulo contiene SOLO la clase ThermalReceiptBuilder y sus helpers internos.
"""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Any

import frappe
import qrcode

from korvexcio.ecf.thermal_print_api import (
    DEFAULT_PRINTER_WIDTH_DOTS,
    DEFAULT_CHAR_WIDTH_DOTS,
    DEFAULT_CHAR_HEIGHT_DOTS,
    DEFAULT_MAX_CHARS_PER_LINE,
    _get_printer_constants,
    _format_currency,
    _format_qty,
)


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
        # FASE 4.4: Cargar constantes de impresora desde ECF Print Settings
        company_name = invoice_data.get("company")
        self.printer = _get_printer_constants(company_name)

    # --- Helpers de formato ---

    def _center_text(self, text: str, width: int | None = None) -> str:
        """Center text within printer width."""
        w = width or self.printer["max_chars_per_line"]
        if len(text) >= w:
            return text[:w]
        padding = (w - len(text)) // 2
        return " " * padding + text

    def _right_align(self, label: str, value: str, width: int | None = None) -> str:
        """Right-align value with label on left."""
        w = width or self.printer["max_chars_per_line"]
        combined = f"{label}{value}"
        if len(combined) >= w:
            return combined[:w]
        padding = w - len(combined)
        return label + " " * padding + value

    # --- ESC/POS Building ---

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
        cut_cmd = self._get_cut_command()
        commands.extend(cut_cmd)

        return bytes(commands)

    def _get_cut_command(self) -> bytes:
        """Get cut paper command based on printer settings."""
        cut_type = self.printer.get("cut_paper", "Full cut (Guillotina)")
        if "Full" in cut_type:
            return b"\x1d\x56\x00"  # GS V m=0 - Full cut
        elif "Partial" in cut_type:
            return b"\x1d\x56\x01"  # GS V m=1 - Partial cut
        return b""  # Sin corte

    def _escpos_header(self) -> bytes:
        """Build header section."""
        out = bytearray()

        if self.company:
            # Company name - double height/width
            out.extend(b"\x1b\x21\x30")  # ESC ! n - Double height + double width
            out.extend(self._center_text(self.company.company_name).encode("utf-8"))
            out.extend(b"\n")

            # RNC
            out.extend(b"\x1b\x21\x00")  # Normal size
            rnc = getattr(self.company, "tax_id", "") or ""
            if rnc:
                out.extend(self._center_text(f"RNC: {rnc}").encode("utf-8"))
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
                out.extend(self._center_text(line).encode("utf-8"))
                out.extend(b"\n")

        # Separator
        out.extend(b"\x1b\x21\x00")  # Normal
        out.extend("-" * self.printer["max_chars_per_line"].encode("utf-8"))
        out.extend(b"\n")

        # Document type
        doc_type = "NOTA DE CREDITO" if self.invoice.get("is_return") else "FACTURA DE VENTA"
        out.extend(b"\x1b\x21\x20")  # Double height
        out.extend(self._center_text(doc_type).encode("utf-8"))
        out.extend(b"\n")
        out.extend(b"\x1b\x21\x00")  # Normal

        # e-NCF if available
        if self.ecf and self.ecf.get("encf"):
            out.extend(self._center_text(f"e-NCF: {self.ecf['encf']}").encode("utf-8"))
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

        out.extend("-" * self.printer["max_chars_per_line"].encode("utf-8"))
        out.extend(b"\n")

        return out

    def _escpos_items(self) -> bytes:
        """Build items table."""
        out = bytearray()
        max_chars = self.printer["max_chars_per_line"]

        # Header - adjust column widths based on max_chars
        item_width = max(16, max_chars - 24)  # leave room for qty/price/amount
        header = f"{'Item':<{item_width}}{'Cant':>6}{'Precio':>9}{'Monto':>9}\n"
        out.extend(header.encode("utf-8"))
        out.extend("-" * max_chars .encode("utf-8"))
        out.extend(b"\n")

        items = self.invoice.get("items", [])
        for item in items:
            item_name = item.get("item_name") or item.get("item_code") or ""
            qty = _format_qty(item.get("qty") or item.get("quantity"))
            rate = _format_currency(item.get("rate"))
            amount = _format_currency(item.get("amount"))

            # Truncate item name if too long
            if len(item_name) > item_width:
                item_name = item_name[:item_width - 3] + "..."

            line = f"{item_name:<{item_width}}{qty:>6}{rate:>9}{amount:>9}\n"
            out.extend(line.encode("utf-8"))

            # Discount line if applicable
            discount = item.get("discount_amount", 0)
            if discount and float(discount) > 0:
                disc_line = f"{'  Desc.':<{item_width}}{'':>6}{'':>9}-{_format_currency(discount):>8}\n"
                out.extend(disc_line.encode("utf-8"))

        out.extend("-" * max_chars .encode("utf-8"))
        out.extend(b"\n")

        return out

    def _escpos_totals(self) -> bytes:
        """Build totals section."""
        out = bytearray()

        subtotal = float(self.invoice.get("grand_total", 0)) - float(self.invoice.get("total_taxes_and_charges", 0))
        tax = float(self.invoice.get("total_taxes_and_charges", 0))
        total = float(self.invoice.get("grand_total", 0))
        discount = float(self.invoice.get("discount_amount", 0) or 0)

        out.extend(self._right_align("Subtotal: ", _format_currency(subtotal)).encode("utf-8"))
        out.extend(b"\n")
        out.extend(self._right_align("ITBIS: ", _format_currency(tax)).encode("utf-8"))
        out.extend(b"\n")

        if discount > 0:
            out.extend(self._right_align("Descuento: ", f"-{_format_currency(discount)}").encode("utf-8"))
            out.extend(b"\n")

        # Grand total - double height
        out.extend(b"\x1b\x21\x10")  # Double height
        out.extend(self._right_align("TOTAL: ", _format_currency(total)).encode("utf-8"))
        out.extend(b"\n")
        out.extend(b"\x1b\x21\x00")  # Normal
        out.extend(b"\n")

        return out

    def _escpos_payments(self) -> bytes:
        """Build payments section."""
        out = bytearray()
        max_chars = self.printer["max_chars_per_line"]

        payments = self.invoice.get("payments", [])
        if not payments:
            return out

        out.extend("FORMAS DE PAGO:\n".encode("utf-8"))
        out.extend("-" * max_chars .encode("utf-8"))
        out.extend(b"\n")

        for payment in payments:
            mode = payment.get("mode_of_payment", "EFECTIVO")
            amount = _format_currency(payment.get("amount", 0))
            out.extend(self._right_align(f"{mode}: ", amount).encode("utf-8"))
            out.extend(b"\n")

        paid = _format_currency(self.invoice.get("paid_amount", 0))
        out.extend(self._right_align("Total Pagado: ", paid).encode("utf-8"))
        out.extend(b"\n")

        change = self.invoice.get("change_amount", 0)
        if change and float(change) > 0:
            out.extend(self._right_align("Cambio: ", _format_currency(change)).encode("utf-8"))
            out.extend(b"\n")

        outstanding = self.invoice.get("outstanding_amount", 0)
        if outstanding and float(outstanding) > 0:
            out.extend(self._right_align("PENDIENTE: ", _format_currency(outstanding)).encode("utf-8"))
            out.extend(b"\n")

        out.extend("-" * max_chars .encode("utf-8"))
        out.extend(b"\n")

        return out

    def _escpos_qr_code(self) -> bytes:
        """Build QR code section for e-CF verification."""
        out = bytearray()

        if not self.ecf or not self.ecf.get("qr_url"):
            out.extend(self._center_text("QR pendiente").encode("utf-8"))
            out.extend(b"\n")
            out.extend(self._center_text("Se genera al confirmar con DGII").encode("utf-8"))
            out.extend(b"\n\n")
            return out

        # Print QR code using GS ( k command (ESC/POS)
        qr_url = self.ecf["qr_url"]

        out.extend(b"\x1b\x21\x00")  # Normal size
        out.extend(self._center_text("REPRESENTACION IMPRESA e-CF").encode("utf-8"))
        out.extend(b"\n")
        out.extend(self._center_text("Verifique en:").encode("utf-8"))
        out.extend(b"\n")
        out.extend(self._center_text(qr_url).encode("utf-8"))
        out.extend(b"\n\n")

        # QR Code: GS ( k pL pH cn fn n1 n2
        # Model 2, size from settings, error correction from settings
        qr_bytes = qr_url.encode("utf-8")
        qr_len = len(qr_bytes) + 3
        pL = qr_len & 0xFF
        pH = (qr_len >> 8) & 0xFF

        # GS ( k - Select QR code model
        out.extend(b"\x1d\x28\x6b\x04\x00\x31\x41\x32\x00")  # Model 2

        # GS ( k - Set size (1-16, from settings)
        qr_size = self.printer.get("qr_module_size", 4)
        out.extend(b"\x1d\x28\x6b\x03\x00\x31\x43" + bytes([qr_size]))

        # GS ( k - Set error correction (48=M, 49=L, 50=Q, 51=H)
        ec_map = {"L": 49, "M": 48, "Q": 50, "H": 51}
        ec_level = ec_map.get(self.printer.get("qr_error_correction", "M"), 48)
        out.extend(b"\x1d\x28\x6b\x03\x00\x31\x45" + bytes([ec_level]))

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
            out.extend(self._center_text(f"TrackID: {self.ecf['track_id']}").encode("utf-8"))
            out.extend(b"\n")
        if self.ecf.get("codigo_seguridad"):
            out.extend(self._center_text(f"Cod. Seguridad: {self.ecf['codigo_seguridad']}").encode("utf-8"))
            out.extend(b"\n")

        return out

    def _escpos_footer(self) -> bytes:
        """Build footer section."""
        out = bytearray()

        out.extend(b"\n")
        footer_text = self.printer.get("footer_text", "¡Gracias por su compra!")
        out.extend(self._center_text(footer_text).encode("utf-8"))
        out.extend(b"\n")
        out.extend(self._center_text("Powered by Korvex").encode("utf-8"))
        out.extend(b"\n\n\n")

        return out

    # --- HTML Building ---

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
            payments_html += f"<tr><td>{mode}</td><td class=\"text-right\">{amount}</td></tr>"

        paid = _format_currency(self.invoice.get("paid_amount", 0))
        change = self.invoice.get("change_amount", 0)
        outstanding = self.invoice.get("outstanding_amount", 0)

        qr_html = ""
        if qr_url:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=4, border=2)
            qr.add_data(qr_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_b64 = base64.b64encode(buffered.getvalue()).decode()
            qr_html = f'<img src="data:image/png;base64,{qr_b64}" alt="QR e-CF" style="width: 120px; height: 120px;">'
        else:
            qr_html = '<div class="qr-pending">QR pendiente<br><small>Se genera al confirmar con DGII</small></div>'

        header_text = self.printer.get("header_text", "")
        footer_text = self.printer.get("footer_text", "¡Gracias por su compra!")

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Recibo {self.invoice.get('name', '')}</title>
    <style>
        @media print {{
            .no-print {{ display: none !important; }}
            body {{ margin: 0; padding: 0; }}
        }}
        body {{
            font-family: 'Courier New', Courier, monospace;
            font-size: 12px;
            line-height: 1.4;
            max-width: 320px;
            margin: 0 auto;
            padding: 10px;
            background: white;
        }}
        .header {{ text-align: center; margin-bottom: 10px; }}
        .header h1 {{ font-size: 16px; margin: 0 0 5px; }}
        .header .rnc {{ font-size: 11px; margin: 2px 0; }}
        .header .address {{ font-size: 10px; margin: 2px 0; }}
        .doc-type {{ text-align: center; font-weight: bold; font-size: 13px; margin: 10px 0; }}
        .encf {{ text-align: center; font-size: 11px; margin: 5px 0; }}
        .separator {{ border-top: 1px dashed #000; margin: 8px 0; }}
        .invoice-info {{ font-size: 11px; margin: 5px 0; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
        th, td {{ padding: 3px 2px; text-align: left; }}
        .text-right {{ text-align: right; }}
        .items-header {{ background: #f0f0f0; }}
        .items tr {{ border-bottom: 1px solid #eee; }}
        .discount {{ color: #666; font-size: 10px; }}
        .totals {{ margin-top: 10px; font-size: 12px; }}
        .totals .row {{ display: flex; justify-content: space-between; margin: 3px 0; }}
        .totals .grand-total {{ font-weight: bold; font-size: 14px; border-top: 1px solid #000; padding-top: 5px; }}
        .payments {{ margin: 10px 0; font-size: 11px; }}
        .payments table {{ width: 100%; }}
        .qr-section {{ text-align: center; margin: 15px 0; }}
        .qr-pending {{ color: #999; font-size: 11px; }}
        .track-info {{ text-align: center; font-size: 10px; color: #666; margin-top: 10px; }}
        .footer {{ text-align: center; margin-top: 20px; font-size: 11px; }}
        .powered {{ color: #999; font-size: 10px; }}
        button {{ padding: 8px 16px; margin: 5px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="receipt">
        <div class="header">
            {f'<h1>{company_name}</h1>' if company_name else ''}
            {f'<div class="rnc">RNC: {company_rnc}</div>' if company_rnc else ''}
            {f'<div class="address">{company_address}</div>' if company_address else ''}
            {f'<div class="header-text">{header_text}</div>' if header_text else ''}
        </div>

        <div class="separator"></div>

        <div class="doc-type">{doc_type}</div>
        {f'<div class="encf">e-NCF: {encf}</div>' if encf else ''}

        <div class="separator"></div>

        <div class="invoice-info">
            <div>Factura: {self.invoice.get('name', '')}</div>
            <div>Fecha: {self.invoice.get('posting_date', '')}</div>
            {f'<div>Cliente: {self.invoice.get("customer_name", "")}</div>' if self.invoice.get("customer_name") else ''}
            {f'<div>RNC Cliente: {self.invoice.get("tax_id", "")}</div>' if self.invoice.get("tax_id") else ''}
        </div>

        <div class="separator"></div>

        <table class="items">
            <thead class="items-header">
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

        <div class="separator"></div>

        <div class="totals">
            <div class="row"><span>Subtotal:</span><span>{_format_currency(subtotal)}</span></div>
            <div class="row"><span>ITBIS:</span><span>{_format_currency(tax)}</span></div>
            {f'<div class="row"><span>Descuento:</span><span>-{_format_currency(discount_total)}</span></div>' if discount_total > 0 else ''}
            <div class="row grand-total"><span>TOTAL:</span><span>{_format_currency(total)}</span></div>
        </div>

        <div class="separator"></div>

        <div class="payments">
            <strong>FORMAS DE PAGO:</strong>
            <table>
                {payments_html}
            </table>
            <div class="row"><strong>Total Pagado:</strong><span>{paid}</span></div>
            {f'<div class="row"><span>Cambio:</span><span>{_format_currency(change)}</span></div>' if change and float(change) > 0 else ''}
            {f'<div class="row"><span>PENDIENTE:</span><span>{_format_currency(outstanding)}</span></div>' if outstanding and float(outstanding) > 0 else ''}
        </div>

        <div class="separator"></div>

        <div class="qr-section">
            {qr_html}
        </div>

        {f'<div class="track-info">TrackID: {track_id}</div>' if track_id else ''}
        {f'<div class="track-info">Cod. Seguridad: {codigo_seguridad}</div>' if codigo_seguridad else ''}

        <div class="footer">
            <div>{footer_text}</div>
            <div class="powered">Powered by Korvex</div>
        </div>
    </div>

    <div class="no-print" style="text-align: center; margin-top: 20px; padding: 10px;">
        <button onclick="window.print()">Imprimir Recibo</button>
        <button onclick="window.close()">Cerrar</button>
    </div>
</body>
</html>"""
        return html