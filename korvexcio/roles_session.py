"""Session limits and authentication hooks (S5.3).

FASE 4.8: Separado de roles.py.
Contiene: validate_session_limits, on_login, on_logout, on_login_failed,
extend_bootinfo, _check_password_expiry
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, date_diff, nowdate


# =============================================================================
# S5.3: Hook implementations
# =============================================================================

CAJERO_ROLES = ["Cajero VLJ", "Cajero ESE"]


def validate_session_limits(user: str) -> bool:
    """Valida límites de sesión concurrente por rol.

    Se llama desde auth_hooks. Retorna True si permite la sesión, False si la deniega.
    Usa frappe.auth.get_active_sessions() para contar solo sesiones realmente vivas,
    no sesiones expiradas con lastupdate > 24h (fix SEC-A02).
    """
    # Obtener roles del usuario
    user_roles = frappe.get_roles(user)

    # Verificar si es cajero
    is_cajero = any(role in CAJERO_ROLES for role in user_roles)
    is_owner = "Dueño" in user_roles

    if not is_cajero and not is_owner:
        return True  # Otros roles sin límite específico

    # Obtener límite de sesiones concurrentes
    if is_cajero:
        max_sessions = cint(frappe.db.get_single_value("System Settings", "concurrent_sessions_cashier")) or 1
    else:
        max_sessions = cint(frappe.db.get_single_value("System Settings", "concurrent_sessions_owner")) or 3

    # Contar sesiones ACTIVAS reales (no expiradas)
    # frappe.auth.get_active_sessions() devuelve lista de dicts con 'sid', 'user', 'lastupdate'
    active_sessions_list = frappe.auth.get_active_sessions(user)
    # Excluir la sesión actual si está en la lista
    current_sid = getattr(frappe.session, "sid", None)
    if current_sid:
        active_sessions_list = [s for s in active_sessions_list if s.get("sid") != current_sid]

    active_sessions = len(active_sessions_list)

    if active_sessions >= max_sessions:
        log_user_activity(user, "session_limit_exceeded", "Failed",
            f"Usuario tiene {active_sessions} sesiones activas, máximo permitido: {max_sessions}")
        return False

    return True


def on_login(user: str) -> None:
    """Callback al hacer login exitoso - registrar en audit trail."""
    log_user_activity(user, "login", "Success", "Inicio de sesión exitoso")

    # Verificar expiración de contraseña
    _check_password_expiry(user)


def on_logout(user: str) -> None:
    """Callback al hacer logout - registrar en audit trail."""
    log_user_activity(user, "logout", "Success", "Cierre de sesión")


def on_login_failed(user: str) -> None:
    """Callback al fallar login - registrar en audit trail."""
    log_user_activity(user, "failed_login", "Failed", "Intento de inicio de sesión fallido")


def extend_bootinfo(bootinfo: dict) -> None:
    """Extiende bootinfo con configuración de sesión por rol."""
    user = frappe.session.user
    user_roles = frappe.get_roles(user)

    is_cajero = any(role in CAJERO_ROLES for role in user_roles)
    is_owner = "Dueño" in user_roles

    if is_cajero:
        hours = cint(frappe.db.get_single_value("System Settings", "cashier_session_hours")) or 8
    elif is_owner:
        hours = cint(frappe.db.get_single_value("System Settings", "owner_session_hours")) or 12
    else:
        hours = 24  # default

    bootinfo["session_expiry_hours"] = hours


def _check_password_expiry(user: str) -> None:
    """Verifica si la contraseña ha expirado.

    SEC-M06: Decisión de producto documentada - solo avisa (no bloquea).
    Rationale: Bloquear login rompería flujos donde el usuario necesita acceder
    para cambiar la password. El aviso visible (alert=True, indicator=orange)
    es suficiente para cumplimiento normativo. Si se requiere bloqueo estricto,
    cambiar a frappe.throw con redirect a change_password.
    """
    expire_days = cint(frappe.db.get_single_value("System Settings", "password_expire_days")) or 90

    # Obtener última vez que se cambió la contraseña
    # En Frappe, esto se rastrea en User.last_password_updated
    user_doc = frappe.get_doc("User", user)
    if user_doc.last_password_updated:
        days_since_change = date_diff(nowdate(), user_doc.last_password_updated)
        if days_since_change >= expire_days:
            # Solo aviso visible - no bloquea login (ver docstring)
            frappe.msgprint(
                _("Su contraseña ha expirado. Por favor cámbiela."),
                alert=True,
                indicator="orange"
            )


# Re-use log_user_activity from roles_audit
from .roles_audit import log_user_activity

__all__ = [
    "validate_session_limits",
    "on_login",
    "on_logout",
    "on_login_failed",
    "extend_bootinfo",
    "_check_password_expiry",
]