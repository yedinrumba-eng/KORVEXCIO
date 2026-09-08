"""Tests de la cola asincrona de e-CF (S2.10) — FIXTURES AISLADAS (FASE 5.3).

`ECF.reference_doctype`/`reference_name` apunta a "Company"/COMPANY_A en
vez de a una Sales Invoice real: el Dynamic Link solo necesita que el
documento exista de verdad (Frappe lo valida), no que sea del pipeline
de ventas -- ese pipeline completo ya lo prueba test_sales_invoice_hooks.py.
Aqui se prueba la logica de la cola: resolucion de proveedor por
Company, la maquina de estados de ECF.estado/docstatus, y el reintento.

Cada test usa setUp/tearDown independiente con datos únicos (generate_hash)
para evitar contaminación entre tests en CI paralelo.
"""

import frappe
from frappe.tests import IntegrationTestCase

from korvexcio.ecf import tasks
from korvexcio.ecf.providers import registry
from korvexcio.ecf.providers.base import ConsultaResult, EmisionResult, Err, Ok


class _FakeProvider:
    def __init__(self, emitir_result=None, consultar_result=None):
        self._emitir_result = emitir_result
        self._consultar_result = consultar_result
        self.calls = []

    def emitir(self, company, signed_xml):
        self.calls.append(("emitir", company, signed_xml))
        return self._emitir_result

    def consultar(self, company, track_id):
        self.calls.append(("consultar", company, track_id))
        return self._consultar_result

    def anular(self, company, encf, motivo):
        # No implementado para tests unitarios de emitir/consultar
        raise RuntimeError("anular no implementado en _FakeProvider")


def _ensure_dgii_settings(company: str, provider: str = "Alanube") -> None:
    if frappe.db.exists("DGII Settings", company):
        return
    frappe.get_doc(
        {
            "doctype": "DGII Settings",
            "company": company,
            "ambiente": "TesteCF",
            "provider": provider,
            "connect_timeout_seconds": 10,
            "read_timeout_seconds": 30,
        }
    ).insert()


def _make_ecf(company: str, estado="Pendiente", track_id=None, attempt_count=0):
    ecf = frappe.get_doc(
        {
            "doctype": "ECF",
            "company": company,
            "reference_doctype": "Company",
            "reference_name": company,
            "tipo_ecf": "E32",
            "encf": f"E32{frappe.generate_hash(length=10)}",
            "estado": estado,
            "track_id": track_id,
            "attempt_count": attempt_count,
        }
    )
    ecf.insert()
    ecf.db_set("signed_xml", "<ECF />")
    ecf.reload()
    return ecf


class TestEmitirECF(IntegrationTestCase):
    """Tests de emisión de e-CF con fixtures aisladas por test."""

    def setUp(self):
        frappe.set_user("Administrator")
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests
        from korvexcio.roles import assign_company_user_permission, sync_roles

        before_tests()
        sync_roles()

        # Generar sufijo único para este test
        self.test_hash = frappe.generate_hash(8)
        self.company = f"_Test Company KORVEXCIO A {self.test_hash}"
        self.dueno = f"_test.isolation.owner.tasks.{self.test_hash}@korvexdev.cc"
        self.cajero = f"_test.isolation.cajero.tasks.{self.test_hash}@korvexdev.cc"

        _ensure_dgii_settings(self.company)

        # Crear usuario Dueño
        if not frappe.db.exists("User", self.dueno):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.dueno,
                    "first_name": "Dueno Tasks Isolation Test",
                    "user_type": "System User",
                    "send_welcome_email": 0,
                    "roles": [{"role": "Dueño"}],
                }
            ).insert()
        assign_company_user_permission(self.dueno, self.company)

        # Crear usuario Cajero
        if not frappe.db.exists("User", self.cajero):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.cajero,
                    "first_name": "Cajero Tasks Isolation Test",
                    "user_type": "System User",
                    "send_welcome_email": 0,
                    "roles": [{"role": "Cajero VLJ"}],
                }
            ).insert()
        assign_company_user_permission(self.cajero, self.company)

        registry._REGISTRY.clear()

    def tearDown(self):
        frappe.set_user("Administrator")
        # Limpiar en orden inverso de dependencias
        try:
            # ECFs
            for ecf_name in frappe.get_all("ECF", filters={"company": self.company}, pluck="name"):
                try:
                    doc = frappe.get_doc("ECF", ecf_name)
                    if doc.docstatus == 1:
                        doc.cancel()
                    frappe.delete_doc("ECF", ecf_name, force=True, ignore_permissions=True)
                except (frappe.DoesNotExistError, frappe.ValidationError):
                    pass

            # ECF Integration Log
            for log_name in frappe.get_all("ECF Integration Log", filters={"company": self.company}, pluck="name"):
                try:
                    frappe.delete_doc("ECF Integration Log", log_name, force=True, ignore_permissions=True)
                except (frappe.DoesNotExistError, frappe.ValidationError):
                    pass

            # DGII Settings
            if frappe.db.exists("DGII Settings", self.company):
                frappe.delete_doc("DGII Settings", self.company, force=True, ignore_permissions=True)

            # Users
            if frappe.db.exists("User", self.dueno):
                frappe.delete_doc("User", self.dueno, force=True, ignore_permissions=True)
            if frappe.db.exists("User", self.cajero):
                frappe.delete_doc("User", self.cajero, force=True, ignore_permissions=True)

        except (frappe.DoesNotExistError, frappe.ValidationError):
            pass

        registry._REGISTRY.clear()
        frappe.set_user("Administrator")

    def test_no_provider_registered_leaves_ecf_pending(self):
        ecf = _make_ecf(self.company)
        tasks.emitir_ecf(ecf.name)
        ecf.reload()
        self.assertEqual(ecf.estado, "Pendiente")
        self.assertEqual(ecf.docstatus, 0)
        self.assertEqual(ecf.attempt_count, 0)
        self.assertIn("S2.7", ecf.validation_messages)

    def test_ok_result_stays_pending_until_poll_confirms_acceptance(self):
        fake = _FakeProvider(
            emitir_result=Ok(EmisionResult(track_id="TRK-1", codigo_seguridad="ABC", qr_url="https://x"))
        )
        registry._REGISTRY["Alanube"] = lambda: fake
        ecf = _make_ecf(self.company)

        tasks.emitir_ecf(ecf.name)
        ecf.reload()
        self.assertEqual(ecf.estado, "Pendiente")
        self.assertEqual(ecf.docstatus, 0)
        self.assertEqual(ecf.track_id, "TRK-1")

        log_name = frappe.db.get_value("ECF Integration Log", {"ecf": ecf.name, "operation": "emitir"}, "name")
        self.assertIsNotNone(log_name)

    def test_claim_is_single_worker(self):
        ecf = _make_ecf(self.company)
        self.assertTrue(tasks._claim_ecf(ecf.name))
        self.assertFalse(tasks._claim_ecf(ecf.name))

    def test_provider_error_message_is_redacted(self):
        fake = _FakeProvider(
            emitir_result=Err(message="token=abc123 password=hunter2", retryable=False)
        )
        registry._REGISTRY["Alanube"] = lambda: fake
        ecf = _make_ecf(self.company)

        tasks.emitir_ecf(ecf.name)

        ecf.reload()
        self.assertNotIn("abc123", ecf.validation_messages)
        self.assertNotIn("hunter2", ecf.validation_messages)

    def test_missing_signed_xml_never_calls_provider(self):
        fake = _FakeProvider(emitir_result=Ok(EmisionResult(track_id="NO-CALL")))
        registry._REGISTRY["Alanube"] = lambda: fake
        ecf = _make_ecf(self.company)
        ecf.signed_xml = None
        ecf.save()

        tasks.emitir_ecf(ecf.name)

        ecf.reload()
        self.assertEqual(fake.calls, [])
        self.assertEqual(ecf.estado, "Pendiente")
        self.assertEqual(ecf.attempt_count, 0)

    def test_malformed_signed_xml_never_calls_provider(self):
        fake = _FakeProvider(emitir_result=Ok(EmisionResult(track_id="NO-CALL")))
        registry._REGISTRY["Alanube"] = lambda: fake
        ecf = _make_ecf(self.company)
        ecf.signed_xml = "<ECF>"
        ecf.save()

        tasks.emitir_ecf(ecf.name)

        ecf.reload()
        self.assertEqual(fake.calls, [])
        self.assertEqual(ecf.estado, "Pendiente")
        self.assertEqual(ecf.attempt_count, 0)

    def test_retryable_err_stays_pending_and_draft(self):
        fake = _FakeProvider(emitir_result=Err(message="timeout", retryable=True))
        registry._REGISTRY["Alanube"] = lambda: fake
        ecf = _make_ecf(self.company, attempt_count=1)

        tasks.emitir_ecf(ecf.name)
        ecf.reload()
        self.assertEqual(ecf.estado, "Pendiente")
        self.assertEqual(ecf.docstatus, 0)
        self.assertEqual(ecf.attempt_count, 2)

    def test_non_retryable_err_is_rejected_and_submitted(self):
        fake = _FakeProvider(emitir_result=Err(message="rechazado por la DGII", retryable=False))
        registry._REGISTRY["Alanube"] = lambda: fake
        ecf = _make_ecf(self.company)

        tasks.emitir_ecf(ecf.name)
        ecf.reload()
        self.assertEqual(ecf.estado, "Rechazado")
        self.assertEqual(ecf.docstatus, 1)

    def test_max_attempts_reached_is_rejected_even_if_retryable(self):
        fake = _FakeProvider(emitir_result=Err(message="timeout", retryable=True))
        registry._REGISTRY["Alanube"] = lambda: fake
        ecf = _make_ecf(self.company, attempt_count=tasks.MAX_ATTEMPTS - 1)

        tasks.emitir_ecf(ecf.name)
        ecf.reload()
        self.assertEqual(ecf.estado, "Rechazado")

    def test_terminal_ecf_is_not_reprocessed(self):
        fake = _FakeProvider(emitir_result=Ok(EmisionResult(track_id="SHOULD-NOT-BE-CALLED")))
        registry._REGISTRY["Alanube"] = lambda: fake
        ecf = _make_ecf(self.company, estado="Aceptado")

        tasks.emitir_ecf(ecf.name)
        self.assertEqual(fake.calls, [])

    def test_log_write_bypasses_create_permission_but_stays_company_scoped(self):
        """Prueba de aislamiento requerida por CLAUDE.md regla 12b para
        el ignore_permissions=True de _log_attempt: un Dueño (que solo
        tiene LECTURA en ECF Integration Log, S2.5) puede disparar la
        escritura del log via el job -- pero el log sigue quedando
        filtrado por company como cualquier otro doctype de la lista."""
        fake = _FakeProvider(emitir_result=Ok(EmisionResult(track_id="TRK-ISO")))
        registry._REGISTRY["Alanube"] = lambda: fake
        ecf = _make_ecf(self.company)

        frappe.set_user(self.dueno)
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc(
                {
                    "doctype": "ECF Integration Log",
                    "company": self.company,
                    "operation": "emitir",
                    "provider": "Alanube",
                }
            ).insert()

        tasks.emitir_ecf(ecf.name)

        log_name = frappe.db.get_value("ECF Integration Log", {"ecf": ecf.name, "operation": "emitir"}, "name")
        self.assertIsNotNone(log_name, "el job no debio fallar por el create-permission del Dueño")
        self.assertEqual(frappe.db.get_value("ECF Integration Log", log_name, "company"), self.company)

    def test_worker_writes_bypass_permission_but_stay_company_scoped(self):
        """Prueba de aislamiento requerida por CLAUDE.md regla 12b para el
        ignore_permissions=True de _save_as_system: un Cajero no tiene
        NINGUN permiso en ECF (tabla de S2.4) -- ni siquiera lectura por
        la via correcta. Confirma dos cosas: (1) el propio Cajero, actuando
        directo, no puede escribir el ECF; (2) el job que su venta encolo
        SI puede avanzarlo -- sin que eso abra una via nueva para tocar
        datos de otra Company (el campo `company` sigue congelado por
        freeze_company(), ignore_permissions=True no toca ese mecanismo)."""
        fake = _FakeProvider(emitir_result=Ok(EmisionResult(track_id="TRK-CAJERO")))
        registry._REGISTRY["Alanube"] = lambda: fake
        ecf = _make_ecf(self.company)

        frappe.set_user(self.cajero)
        # get_doc() no chequea permisos de lectura (leccion de S1.8) -- el
        # save() si los chequea, y es ahi donde se prueba que el Cajero de
        # verdad no tiene acceso de escritura.
        doc = frappe.get_doc("ECF", ecf.name)
        doc.validation_messages = "intento directo del cajero, sin bypass"
        with self.assertRaises(frappe.PermissionError):
            doc.save()

        tasks.emitir_ecf(ecf.name)

        frappe.set_user("Administrator")
        ecf.reload()
        self.assertEqual(ecf.track_id, "TRK-CAJERO")
        self.assertEqual(ecf.company, self.company)


class TestRetryAndPoll(IntegrationTestCase):
    """Tests de reintento y polling con fixtures aisladas por test."""

    def setUp(self):
        frappe.set_user("Administrator")
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests
        from korvexcio.roles import assign_company_user_permission, sync_roles

        before_tests()
        sync_roles()

        # Generar sufijo único para este test
        self.test_hash = frappe.generate_hash(8)
        self.company = f"_Test Company KORVEXCIO A {self.test_hash}"

        _ensure_dgii_settings(self.company)
        registry._REGISTRY.clear()

    def tearDown(self):
        frappe.set_user("Administrator")
        # Limpiar en orden inverso de dependencias
        try:
            # ECFs
            for ecf_name in frappe.get_all("ECF", filters={"company": self.company}, pluck="name"):
                try:
                    doc = frappe.get_doc("ECF", ecf_name)
                    if doc.docstatus == 1:
                        doc.cancel()
                    frappe.delete_doc("ECF", ecf_name, force=True, ignore_permissions=True)
                except (frappe.DoesNotExistError, frappe.ValidationError):
                    pass

            # ECF Integration Log
            for log_name in frappe.get_all("ECF Integration Log", filters={"company": self.company}, pluck="name"):
                try:
                    frappe.delete_doc("ECF Integration Log", log_name, force=True, ignore_permissions=True)
                except (frappe.DoesNotExistError, frappe.ValidationError):
                    pass

            # DGII Settings
            if frappe.db.exists("DGII Settings", self.company):
                frappe.delete_doc("DGII Settings", self.company, force=True, ignore_permissions=True)

        except (frappe.DoesNotExistError, frappe.ValidationError):
            pass

        registry._REGISTRY.clear()
        frappe.set_user("Administrator")

    def test_retry_pending_enqueues_only_under_max_attempts(self):
        under = _make_ecf(self.company, attempt_count=0)
        at_max = _make_ecf(self.company, attempt_count=tasks.MAX_ATTEMPTS)
        accepted = _make_ecf(self.company, estado="Aceptado", attempt_count=1)

        enqueued = []
        original_enqueue = frappe.enqueue
        frappe.enqueue = lambda *a, **kw: enqueued.append(kw.get("ecf_name"))
        try:
            tasks.retry_pending_ecf()
        finally:
            frappe.enqueue = original_enqueue

        self.assertIn(under.name, enqueued)
        self.assertNotIn(at_max.name, enqueued)
        self.assertNotIn(accepted.name, enqueued)

    def test_poll_updates_status_from_consultar(self):
        fake = _FakeProvider(consultar_result=Ok(ConsultaResult(estado="Aceptado", validation_messages=None)))
        registry._REGISTRY["Alanube"] = lambda: fake
        ecf = _make_ecf(self.company, track_id="TRK-99")

        tasks.poll_pending_status()
        ecf.reload()
        self.assertEqual(ecf.estado, "Aceptado")
        self.assertEqual(ecf.docstatus, 1)

    def test_poll_skips_ecf_without_track_id(self):
        fake = _FakeProvider(consultar_result=Ok(ConsultaResult(estado="Aceptado")))
        registry._REGISTRY["Alanube"] = lambda: fake
        _make_ecf(self.company, track_id=None)

        tasks.poll_pending_status()
        self.assertEqual(fake.calls, [])
