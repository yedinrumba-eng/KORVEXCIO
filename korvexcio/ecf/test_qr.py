"""Tests del QR del e-CF (S2.12). PyQRCode ya viene instalado en el
bench (lo usa frappe.twofactor) -- sin dependencia nueva."""

import base64
import unittest

from korvexcio.ecf.qr import qr_svg_data_uri


class TestQRSvgDataURI(unittest.TestCase):
    def test_returns_a_valid_svg_data_uri(self):
        data_uri = qr_svg_data_uri("https://ecf.dgii.gov.do/verificar?encf=E320000000001")
        self.assertTrue(data_uri.startswith("data:image/svg+xml;base64,"))

        b64_payload = data_uri.split(",", 1)[1]
        svg = base64.b64decode(b64_payload).decode()
        self.assertIn("<svg", svg)

    def test_different_urls_produce_different_svgs(self):
        a = qr_svg_data_uri("https://ecf.dgii.gov.do/verificar?encf=E320000000001")
        b = qr_svg_data_uri("https://ecf.dgii.gov.do/verificar?encf=E320000000002")
        self.assertNotEqual(a, b)
