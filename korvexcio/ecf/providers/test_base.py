"""Unit test del contrato de FiscalProvider contra un provider falso.
Sin DocTypes, sin fixtures de Company -- es una prueba de interfaz pura."""

import unittest

from korvexcio.ecf.providers.base import (
    ConsultaResult,
    EmisionResult,
    Err,
    FiscalProvider,
    Ok,
)


class FakeProvider(FiscalProvider):
    """Provider de prueba: nunca toca la red, controla su respuesta
    desde afuera para poder probar los dos caminos (Ok/Err)."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.emitir_calls: list[tuple[str, str]] = []

    def emitir(self, company: str, signed_xml: str):
        self.emitir_calls.append((company, signed_xml))
        if self.should_fail:
            return Err(message="proveedor caido", code="TIMEOUT", retryable=True)
        return Ok(EmisionResult(track_id="TRK-123", codigo_seguridad="ABC123", qr_url="https://example"))

    def consultar(self, company: str, track_id: str):
        if self.should_fail:
            return Err(message="track_id no encontrado", code="NOT_FOUND", retryable=False)
        return Ok(ConsultaResult(estado="Aceptado"))

    def anular(self, company: str, encf: str, motivo: str):
        if self.should_fail:
            return Err(message="no se pudo anular", retryable=True)
        return Ok(None)


class TestFiscalProviderContract(unittest.TestCase):
    def test_cannot_instantiate_abstract_base(self):
        with self.assertRaises(TypeError):
            FiscalProvider()

    def test_emitir_ok_path(self):
        provider = FakeProvider(should_fail=False)
        result = provider.emitir("VLJ", "<xml/>")
        self.assertIsInstance(result, Ok)
        self.assertTrue(result.is_ok())
        self.assertEqual(result.value.track_id, "TRK-123")
        self.assertEqual(provider.emitir_calls, [("VLJ", "<xml/>")])

    def test_emitir_err_path_never_raises(self):
        provider = FakeProvider(should_fail=True)
        result = provider.emitir("VLJ", "<xml/>")
        self.assertIsInstance(result, Err)
        self.assertFalse(result.is_ok())
        self.assertTrue(result.retryable)

    def test_consultar_ok_and_err(self):
        self.assertIsInstance(FakeProvider(False).consultar("VLJ", "TRK-1"), Ok)
        err = FakeProvider(True).consultar("VLJ", "TRK-1")
        self.assertIsInstance(err, Err)
        self.assertFalse(err.retryable)

    def test_anular_ok_and_err(self):
        self.assertIsInstance(FakeProvider(False).anular("VLJ", "E320000000001", "error de captura"), Ok)
        self.assertIsInstance(FakeProvider(True).anular("VLJ", "E320000000001", "error de captura"), Err)
