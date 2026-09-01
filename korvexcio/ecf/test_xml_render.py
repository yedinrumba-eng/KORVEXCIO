"""Tests de las plantillas Jinja2 de e-CF (S2.8).

No validan contra el XSD oficial de la DGII -- no lo tenemos (D20, mismo
hueco que S0.9/S2.7). Solo prueban que el render es determinista, que el
XML resultante es bien formado, y que los secretos/datos con caracteres
especiales no rompen el documento."""

import unittest
from xml.etree import ElementTree

import frappe
import frappe.utils.jinja

from korvexcio.ecf.xml_render import render_ecf_32, render_rfce, validate_well_formed


def _sample_ecf_32_context() -> dict:
    return {
        "IdDoc": {
            "TipoeCF": "32",
            "eNCF": "E320000000001",
            "TipoIngresos": "01",
            "TipoPago": "1",
            "TablaFormasPago": [{"FormaPago": "01", "MontoPago": "1500.00"}],
        },
        "Emisor": {
            "RNCEmisor": "131234567",
            "RazonSocialEmisor": "VAPERIA LA J Y EL JALAPEÑO SRL",
            "NombreComercial": "VAPERIA LA J Y EL JALAPEÑO",
            "DireccionEmisor": "Calle Principal #1",
            "Municipio": "010100",
            "Provincia": "01",
            "TablaTelefonoEmisor": [{"TelefonoEmisor": "8095551234"}],
            "CorreoEmisor": "facturacion@vaperialaj.example",
            "ActividadEconomica": "Venta al por menor",
            "FechaEmision": "31-08-2026",
        },
        "Totales": {
            "MontoGravadoTotal": "1500.00",
            "TotalITBIS": "270.00",
            "MontoTotal": "1770.00",
        },
        "DetallesItems": [
            {
                "NumeroLinea": 1,
                "NombreItem": "Pod desechable sabor menta",
                "IndicadorBienoServicio": "1",
                "CantidadItem": "1",
                "PrecioUnitarioItem": "1500.00",
                "MontoItem": "1500.00",
            }
        ],
    }


class TestRenderECF32(unittest.TestCase):
    def setUp(self):
        self._jenv = frappe.utils.jinja.get_jenv()
        self._original_trim = self._jenv.trim_blocks
        self._original_lstrip = self._jenv.lstrip_blocks

    def test_full_context_renders_well_formed_xml(self):
        xml_string = render_ecf_32(_sample_ecf_32_context())
        validate_well_formed(xml_string)

        root = ElementTree.fromstring(xml_string)
        self.assertEqual(root.tag, "ECF")
        self.assertEqual(root.findtext("./Encabezado/IdDoc/TipoeCF"), "32")
        self.assertEqual(root.findtext("./Encabezado/IdDoc/eNCF"), "E320000000001")
        self.assertEqual(root.findtext("./Encabezado/Emisor/RNCEmisor"), "131234567")
        self.assertEqual(root.findtext("./Encabezado/Totales/MontoTotal"), "1770.00")
        self.assertEqual(root.findtext("./DetallesItems/Item/NombreItem"), "Pod desechable sabor menta")
        self.assertIsNotNone(root.findtext("./FechaHoraFirma"))

    def test_minimal_context_omits_optional_groups(self):
        minimal = {
            "IdDoc": {"TipoeCF": "32", "eNCF": "E320000000002"},
            "Emisor": {"RNCEmisor": "131234567"},
            "Totales": {"MontoTotal": "100.00"},
        }
        xml_string = render_ecf_32(minimal)
        validate_well_formed(xml_string)

        root = ElementTree.fromstring(xml_string)
        self.assertIsNone(root.find("./Encabezado/Comprador"))
        self.assertIsNone(root.find("./Encabezado/InformacionesAdicionales"))
        self.assertIsNone(root.find("./Encabezado/Transporte"))
        self.assertIsNone(root.find("./DetallesItems"))
        self.assertIsNone(root.find("./InformacionReferencia"))

    def test_ampersand_and_angle_brackets_are_escaped_not_broken(self):
        context = _sample_ecf_32_context()
        context["Emisor"]["NombreComercial"] = 'Vapes & Snacks <RD> "El Jalapeño"'
        xml_string = render_ecf_32(context)

        validate_well_formed(xml_string)
        self.assertIn("&amp;", xml_string)
        self.assertIn("&lt;RD&gt;", xml_string)

        root = ElementTree.fromstring(xml_string)
        self.assertEqual(
            root.findtext("./Encabezado/Emisor/NombreComercial"),
            'Vapes & Snacks <RD> "El Jalapeño"',
        )

    def test_missing_fecha_hora_firma_gets_a_default(self):
        minimal = {
            "IdDoc": {"TipoeCF": "32"},
            "Emisor": {"RNCEmisor": "131234567"},
            "Totales": {"MontoTotal": "0.00"},
        }
        xml_string = render_ecf_32(minimal)
        root = ElementTree.fromstring(xml_string)
        self.assertTrue(root.findtext("./FechaHoraFirma"))

    def test_shared_jinja_env_trim_and_lstrip_restored_after_render(self):
        render_ecf_32(_sample_ecf_32_context())
        self.assertEqual(self._jenv.trim_blocks, self._original_trim)
        self.assertEqual(self._jenv.lstrip_blocks, self._original_lstrip)

    def test_shared_jinja_env_restored_even_if_context_is_broken(self):
        # Blind except is deliberate: this proves the try/finally in _render()
        # restores the shared jenv no matter WHAT breaks, not just one error type.
        with self.assertRaises(Exception):  # noqa: B017
            render_ecf_32({"IdDoc": None, "Emisor": {}, "Totales": {}})
        self.assertEqual(self._jenv.trim_blocks, self._original_trim)
        self.assertEqual(self._jenv.lstrip_blocks, self._original_lstrip)


class TestRenderRFCE(unittest.TestCase):
    def _sample_rfce_context(self) -> dict:
        return {
            "IdDoc": {"TipoeCF": "32", "eNCF": "E320000000099", "TipoIngresos": "01"},
            "Emisor": {"RNCEmisor": "131234567", "RazonSocialEmisor": "VAPERIA LA J Y EL JALAPEÑO SRL"},
            "Totales": {"MontoGravadoTotal": "1500.00", "TotalITBIS": "270.00", "MontoTotal": "1770.00"},
            "CodigoSeguridadeCF": "AB12CD34EF",
        }

    def test_renders_well_formed_rfce(self):
        xml_string = render_rfce(self._sample_rfce_context())
        validate_well_formed(xml_string)

        root = ElementTree.fromstring(xml_string)
        self.assertEqual(root.tag, "RFCE")
        self.assertEqual(root.findtext("./Encabezado/CodigoSeguridadeCF"), "AB12CD34EF")
        self.assertEqual(root.findtext("./Encabezado/Totales/MontoTotal"), "1770.00")

    def test_missing_codigo_seguridad_is_rejected(self):
        context = self._sample_rfce_context()
        del context["CodigoSeguridadeCF"]
        with self.assertRaises(frappe.ValidationError):
            render_rfce(context)
