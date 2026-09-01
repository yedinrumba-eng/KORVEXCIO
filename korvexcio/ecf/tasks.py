"""Cola asincrona de e-CF (S2.10).

El POS nunca espera a la DGII para cerrar una venta (CLAUDE.md regla 3):
Sales Invoice.on_submit (S2.9) crea el ECF y encola emitir_ecf() con
enqueue_after_commit=True -- el job no corre si la transaccion de la
venta llega a revertirse, y corre en un worker aparte, nunca en el
request del cajero.

Regla 10 de CLAUDE.md, critica por D19: el proveedor se resuelve por
Company en cada llamada (_resolve_provider_for_company), nunca una vez
al arrancar. Si DGII Settings no existe para esa Company, o el
proveedor elegido no tiene implementacion todavia (S2.7, bloqueado por
D20), no hay a quien llamar -- se deja el ECF en Pendiente para que
retry_pending_ecf() lo reintente, nunca se cae al proveedor de otra
Company.

docstatus (0/1/2) de ECF es "se emitio o no" (S2.4): mientras la
respuesta puede seguir cambiando (Pendiente, reintentable) el documento
queda en Draft; al llegar una respuesta final (Aceptado o Rechazado
definitivo) se somete, quedando bloqueado por ECF.before_cancel/on_trash.
"""

from __future__ import annotations

import re
import time

import frappe

from korvexcio.ecf.providers.base import Err
from korvexcio.ecf.providers.registry import resolve_provider
from korvexcio.ecf.xml_render import validate_well_formed

MAX_ATTEMPTS = 5
_TERMINAL_ESTADOS = {"Aceptado", "Rechazado"}
_VALID_ESTADOS = {"Pendiente", "Enviando", "Aceptado", "Rechazado", "Contingencia", "Anulado"}
MIN_PROVIDER_INTERVAL = 1.7
MAX_PROVIDER_CALLS_PER_MINUTE = 35
_SECRET_PATTERN = re.compile(r"(?i)(authorization|token|password|secret|api[_-]?key)(\s*[:=]\s*)[^\s,;]+")


def _safe_message(message: str | None) -> str | None:
    if not message:
        return None
    sanitized = _SECRET_PATTERN.sub(r"\1\2[REDACTED]", str(message))
    return sanitized[:2000]


def _save_as_system(doc, *, submit: bool = False) -> None:
    """El job de la cola corre bajo la sesion de quien encolo la venta --
    un Cajero (sin NINGUN permiso en ECF, tabla de S2.4) o un Dueño (solo
    create/read/submit, sin write). Ninguno de los dos puede actualizar
    el estado fiscal de su propia venta sin este bypass, y es correcto
    que no puedan: es el SISTEMA avanzando su propio trabajo interno, no
    una accion de negocio del usuario. ignore_permissions=True
    justificado por CLAUDE.md regla 12b -- `company` ya esta congelado
    por freeze_company() desde la creacion del ECF (S2.9), asi que esto
    nunca reasigna un documento a otra Company; el aislamiento entre
    tenants no se toca. Test de aislamiento dedicado:
    test_tasks.py::test_worker_writes_bypass_permission_but_stay_company_scoped.
    """
    doc.flags.ignore_permissions = True
    doc.submit() if submit else doc.save()


def _claim_ecf(ecf_name: str) -> bool:
    """Compare-and-swap atomico via SELECT ... FOR UPDATE -- mismo patron
    que Secuencia eNCF.reserve_next() (S2.3): bloquea la fila hasta el
    commit de esta transaccion, asi que un segundo worker que la pida
    espera, ve el estado ya en Enviando y no puede reclamarla dos veces.
    Sin frappe.db.sql() crudo (CLAUDE.md regla 12b)."""
    estado, docstatus = frappe.db.get_value("ECF", ecf_name, ["estado", "docstatus"], for_update=True)
    if estado != "Pendiente" or docstatus != 0:
        return False
    frappe.db.set_value("ECF", ecf_name, "estado", "Enviando")
    return True


def _resolve_provider_for_company(company: str):
    settings_name = frappe.db.get_value("DGII Settings", {"company": company}, "name")
    if not settings_name:
        return None, None
    provider_name = frappe.db.get_value("DGII Settings", settings_name, "provider")
    return resolve_provider(provider_name), provider_name


def _throttle_provider(provider_name: str) -> bool:
    """Coordinate provider calls through Redis across all workers."""
    cache = frappe.cache()
    lock_key = f"korvexcio:ecf:rate:{provider_name}"
    last_key = f"{lock_key}:last"
    minute_key = f"{lock_key}:count:{int(time.time() // 60)}"
    with cache.lock(lock_key, timeout=10):
        count = int(cache.get_value(minute_key) or 0)
        if count >= MAX_PROVIDER_CALLS_PER_MINUTE:
            return False
        last = float(cache.get_value(last_key) or 0)
        delay = MIN_PROVIDER_INTERVAL - (time.time() - last)
        if delay > 0:
            time.sleep(delay)
        cache.set_value(last_key, time.time(), expires_in_sec=120)
        cache.set_value(minute_key, count + 1, expires_in_sec=70)
        return True


def _source_is_submitted(ecf) -> bool:
    if ecf.reference_doctype != "Sales Invoice":
        return True
    return frappe.db.get_value(ecf.reference_doctype, ecf.reference_name, "docstatus") == 1


def _log_attempt(ecf, operation: str, result, provider_name: str | None) -> None:
    """ECF Integration Log solo lo puede crear System Manager (S2.5) --
    Dueño es de proposito lectura-solo ahi, para que el rastro de
    auditoria no se pueda alterar desde una sesion de negocio. Un job en
    background que corre bajo la sesion de un Dueño (porque encolo la
    venta) SI tiene que poder dejar su propio registro: es el sistema
    escribiendo su propio log, no el usuario. ignore_permissions=True
    justificado por CLAUDE.md regla 12b -- freeze_company() sigue
    aplicando (sigue en COMPANY_SCOPED_DOCTYPES desde S2.5), asi que el
    aislamiento de LECTURA entre Companies no se toca. Test de
    aislamiento propio: test_tasks.py::test_log_write_bypasses_create_permission_but_stays_company_scoped.
    """
    frappe.get_doc(
        {
            "doctype": "ECF Integration Log",
            "company": ecf.company,
            "ecf": ecf.name,
            "provider": provider_name,
            "operation": operation,
            "response_status": 200 if result.is_ok() else 0,
            "error_message": None if result.is_ok() else _safe_message(result.message),
        }
    ).insert(ignore_permissions=True)


def emitir_ecf(ecf_name: str) -> None:
    """El job real que llama al proveedor. Nunca se llama directo desde
    un doc_event sincrono -- siempre por frappe.enqueue."""
    ecf = frappe.get_doc("ECF", ecf_name)
    if ecf.estado in _TERMINAL_ESTADOS:
        return
    if ecf.estado != "Pendiente" or not _claim_ecf(ecf_name):
        return
    # _claim_ecf() escribe directo a la base (frappe.db.set_value), lo que
    # actualiza `modified` -- sin este reload, el `ecf` en memoria queda
    # con un timestamp viejo y el primer .save() de mas abajo revienta con
    # TimestampMismatchError (optimistic locking de Frappe).
    ecf.reload()

    if not _source_is_submitted(ecf):
        ecf.estado = "Anulado"
        ecf.validation_messages = frappe._(
            "La factura origen ya no está sometida; el e-CF no se enviará."
        )
        _save_as_system(ecf)
        return

    if not ecf.signed_xml:
        ecf.validation_messages = frappe._("No se puede enviar un e-CF sin XML firmado.")
        ecf.estado = "Pendiente"
        _save_as_system(ecf)
        return
    try:
        validate_well_formed(ecf.signed_xml)
    except Exception as exc:  # noqa: BLE001
        ecf.validation_messages = frappe._("El XML del e-CF no es valido: {0}").format(
            type(exc).__name__
        )
        ecf.estado = "Pendiente"
        _save_as_system(ecf)
        return

    provider, provider_name = _resolve_provider_for_company(ecf.company)

    if provider is None:
        ecf.validation_messages = frappe._(
            "Sin proveedor real configurado todavia para {0} (S2.7 sigue bloqueado por D20)."
        ).format(ecf.company)
        ecf.estado = "Pendiente"
        _save_as_system(ecf)
        return

    if not _throttle_provider(provider_name):
        ecf.validation_messages = frappe._("Límite temporal del proveedor alcanzado; se reintentará.")
        ecf.estado = "Pendiente"
        _save_as_system(ecf)
        return

    ecf.attempt_count = (ecf.attempt_count or 0) + 1
    try:
        result = provider.emitir(ecf.company, ecf.signed_xml)
    except Exception:  # noqa: BLE001
        frappe.log_error(title=f"emitir_ecf: {provider_name} emitir() crashed for {ecf_name}")
        result = Err(message="Proveedor no disponible", code="provider_error", retryable=True)
    _log_attempt(ecf, "emitir", result, provider_name)

    if result.is_ok():
        ecf.track_id = result.value.track_id
        ecf.codigo_seguridad = result.value.codigo_seguridad
        ecf.qr_url = result.value.qr_url
        # TrackID is an acknowledgement only; polling confirms acceptance.
        ecf.estado = "Pendiente"
        _save_as_system(ecf)
        return

    ecf.validation_messages = _safe_message(result.message)
    if not result.retryable or ecf.attempt_count >= MAX_ATTEMPTS:
        ecf.estado = "Rechazado"
        _save_as_system(ecf, submit=True)
    else:
        ecf.estado = "Pendiente"
        _save_as_system(ecf)


def retry_pending_ecf() -> None:
    """scheduler_events */5 -- reintenta los ECF Pendiente que no
    llegaron al tope de intentos."""
    pending = frappe.get_all(
        "ECF",
        filters={"estado": "Pendiente", "attempt_count": ["<", MAX_ATTEMPTS]},
        pluck="name",
    )
    for ecf_name in pending:
        frappe.enqueue("korvexcio.ecf.tasks.emitir_ecf", queue="short", ecf_name=ecf_name)


def poll_pending_status() -> None:
    """scheduler_events */15 -- para los ECF ya enviados (tienen
    track_id) pero sin respuesta final, pregunta el estado real."""
    awaiting = frappe.get_all(
        "ECF",
        filters={"estado": "Pendiente", "track_id": ["is", "set"]},
        pluck="name",
    )
    for ecf_name in awaiting:
        ecf = frappe.get_doc("ECF", ecf_name)
        provider, provider_name = _resolve_provider_for_company(ecf.company)
        if provider is None:
            continue

        if not _throttle_provider(provider_name):
            continue
        try:
            result = provider.consultar(ecf.company, ecf.track_id)
        except Exception:  # noqa: BLE001
            frappe.log_error(
                title=f"poll_pending_status: {provider_name} consultar() crashed for {ecf_name}"
            )
            continue
        _log_attempt(ecf, "consultar", result, provider_name)
        if not result.is_ok():
            continue

        if result.value.estado not in _VALID_ESTADOS:
            continue
        ecf.estado = result.value.estado
        ecf.validation_messages = _safe_message(result.value.validation_messages)
        if ecf.estado in _TERMINAL_ESTADOS:
            _save_as_system(ecf, submit=True)
        else:
            _save_as_system(ecf)


def refresh_provider_tokens() -> None:
    """scheduler_events 0 */6 -- estructura para renovar tokens de
    proveedores que los usen (OAuth y similares). Sin proveedor real
    (S2.7, D20) no hay token que renovar todavia; existe para que S2.7
    no tenga que inventar el cron cuando llegue."""
    settings = frappe.get_all("DGII Settings", fields=["company", "provider"])
    for setting in settings:
        provider = resolve_provider(setting.provider)
        refresh = getattr(provider, "refresh_token", None) if provider else None
        if refresh:
            try:
                refresh(setting.company)
            except Exception:  # noqa: BLE001
                frappe.log_error(title=f"refresh_provider_tokens: {setting.provider} crashed for {setting.company}")
                continue
