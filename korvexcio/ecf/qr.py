"""Generación del QR del e-CF (S2.12) -- DGII exige el QR en la
representación impresa. `PyQRCode` ya viene instalado en el bench (lo
usa `frappe.twofactor` para el 2FA por TOTP) -- mismo patrón, sin
dependencia nueva que avisar.

El QR codifica la URL de verificación del e-CF (`ECF.qr_url`), no una
imagen que entregue el proveedor -- coincide con el patrón real de la
DGII: el QR apunta a una pagina de verificacion con RNC/eNCF/monto/
codigo de seguridad como parametros."""

from __future__ import annotations

from base64 import b64encode
from io import BytesIO


def qr_svg_data_uri(url: str) -> str:
    """SVG del QR como data URI, listo para un <img src="...">. Mismo
    patron que frappe.twofactor.get_qr_svg_code (scale/colores)."""
    from pyqrcode import create as qrcreate

    qr = qrcreate(url)
    stream = BytesIO()
    try:
        qr.svg(stream, scale=4, background="#ffffff", module_color="#000000", xmldecl=False)
        svg_bytes = stream.getvalue()
    finally:
        stream.close()

    return "data:image/svg+xml;base64," + b64encode(svg_bytes).decode()
