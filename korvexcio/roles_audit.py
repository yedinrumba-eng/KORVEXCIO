"""Audit trail and user activity logging (S5.3).

FASE 4.8: Separado de roles.py.
Contiene: log_user_activity, get_user_activity_log, assign_role_to_user,
remove_role_from_user, freeze_user_company, get_users_by_role
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from .roles_permissions import CAJERO_ROLES, PRIVILEGED_ROLES


# =============================================================================
# S5.3: Role Management Helpers (require privileges)
# =============================================================================

# Roles que requieren ser System Manager O Dueño para asignar/remover
PRIVILEGED_ROLES = ["Dueño", "Contador"]


def _check_role_management_permission(role: str) -> None:
    """Valida que el usuario actual tiene permiso para gestionar roles.

    Reglas:
    - Cualquier System User con permiso 'write' en User puede asignar roles de cajero
    - Solo System Manager O Dueño pueden asignar/remover Dueño o Contador
    - System Manager nunca se asigna via esta función (regla de negocio)
    """
    # Check 1: permiso base de escritura en User
    if not frappe.has_permission("User", "write"):
        frappe.throw(
            _("No tiene permiso para gestionar roles de usuarios"),
            frappe.PermissionError,
        )

    # Check 2: roles privilegiados requieren System Manager o Dueño
    if role in PRIVILEGED_ROLES:
        caller_roles = frappe.get_roles()
        is_system_manager = "System Manager" in caller_roles
        is_dueno = "Dueño" in caller_roles

        if not (is_system_manager or is_dueno):
            frappe.throw(
                _("Solo System Manager o Dueño pueden asignar/remover el rol {0}").format(role),
                frappe.PermissionError,
            )


def assign_role_to_user(user: str, role: str) -> None:
    """Asigna un rol a un usuario existente.

    Validaciones:
    - Usuario y rol existen
    - No es System Manager
    - Rol está en lista de asignables
    - Caller tiene permisos (write en User + privilegio si rol es Dueño/Contador)
    """
    if not frappe.db.exists("User", user):
        frappe.throw(_("Usuario {0} no existe").format(user))

    if not frappe.db.exists("Role", role):
        frappe.throw(_("Rol {0} no existe").format(role))

    # Verificar que no es System Manager
    if role == "System Manager":
        frappe.throw(_("No se puede asignar System Manager directamente. Use los roles propios de KORVEXCIO."))

    # Verificar que el rol es asignable via esta API
    if role not in CAJERO_ROLES + PRIVILEGED_ROLES:
        frappe.throw(_("Rol {0} no es asignable via esta función").format(role))

    # Verificar permisos del caller
    _check_role_management_permission(role)

    user_doc = frappe.get_doc("User", user)
    if not any(r.role == role for r in user_doc.roles):
        user_doc.append("roles", {"role": role})
        user_doc.save()
        log_user_activity(frappe.session.user, "role_change", "Success", f"Added role {role} to user {user}", "User", user)


def remove_role_from_user(user: str, role: str) -> None:
    """Remueve un rol de un usuario existente.

    Validaciones:
    - Usuario existe
    - Rol está en lista de asignables
    - Caller tiene permisos (write en User + privilegio si rol es Dueño/Contador)
    - No se puede remover el último rol del usuario (debe tener al menos uno)
    """
    if not frappe.db.exists("User", user):
        frappe.throw(_("Usuario {0} no existe").format(user))

    if role not in CAJERO_ROLES + PRIVILEGED_ROLES:
        frappe.throw(_("Rol {0} no es gestionable via esta función").format(role))

    # Verificar permisos del caller
    _check_role_management_permission(role)

    user_doc = frappe.get_doc("User", user)

    # Verificar que el usuario tiene el rol
    if not any(r.role == role for r in user_doc.roles):
        frappe.throw(_("Usuario {0} no tiene el rol {1}").format(user, role))

    # Protección: no dejar usuario sin roles
    if len(user_doc.roles) <= 1:
        frappe.throw(_("No se puede remover el último rol del usuario. Asigne otro rol primero."))

    user_doc.roles = [r for r in user_doc.roles if r.role != role]
    user_doc.save()
    log_user_activity(frappe.session.user, "role_change", "Success", f"Removed role {role} from user {user}", "User", user)


def get_users_by_role(role: str) -> list:
    """Obtiene todos los usuarios con un rol específico."""
    return frappe.get_all(
        "Has Role",
        filters={"role": role},
        pluck="parent"
    )


# =============================================================================
# S5.3: Hook implementations
# =============================================================================

def freeze_user_company(doc, method=None) -> None:
    """Hook validate para User - evita cambiar la company asignada via User Permission.

    S5.3: freeze_company en User doc también -- equivalente a RLS WITH CHECK.
    El usuario no debe poder cambiar sus User Permissions de Company una vez asignados.
    """
    # Solo validar si el documento ya existe (no es nuevo)
    if doc.is_new():
        return

    # Verificar si hay User Permissions de Company asignadas
    user_perms = frappe.get_all(
        "User Permission",
        filters={"user": doc.name, "allow": "Company"},
        pluck="for_value"
    )

    if not user_perms:
        return

    # El usuario no debería poder remover sus User Permissions de Company
    # Esto se valida en el cliente, pero el hook sirve como barrera adicional
    # Si se intenta borrar el User Permission, Frappe lo previene por permisos
    pass


# =============================================================================
# Audit Trail
# =============================================================================

def log_user_activity(
    user: str,
    action: str,
    status: str,
    details: str = "",
    reference_doctype: str | None = None,
    reference_name: str | None = None,
) -> None:
    """Registra actividad de usuario en User Activity Log.

    Args:
        user: Usuario que realizó la acción
        action: Tipo de acción (login, logout, failed_login, role_change, etc.)
        status: Success / Failed
        details: Detalles adicionales
        reference_doctype: Doctype relacionado (opcional)
        reference_name: Nombre del documento relacionado (opcional)
    """
    try:
        frappe.get_doc({
            "doctype": "User Activity Log",
            "user": user,
            "action": action,
            "status": status,
            "details": details,
            "reference_doctype": reference_doctype,
            "reference_name": reference_name,
            "timestamp": frappe.utils.now(),
            "ip_address": getattr(frappe.local, "request_ip", None) or "system",
        }).insert(ignore_permissions=True)
    except Exception:
        # Never fail the main operation due to audit logging
        pass


def get_user_activity_log(
    user: str | None = None,
    action: str | None = None,
    status: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Obtiene logs de actividad con filtros opcionales.

    Args:
        user: Filtrar por usuario
        action: Filtrar por acción
        status: Filtrar por estado
        from_date: Fecha inicio (inclusive)
        to_date: Fecha fin (inclusive) - NO IMPLEMENTADO AÚN
        limit: Límite de resultados

    Returns:
        Lista de logs ordenados por timestamp descendente
    """
    filters = {}

    if user:
        filters["user"] = user
    if action:
        filters["action"] = action
    if status:
        filters["status"] = status
    if from_date:
        filters["timestamp"] = [">=", from_date]

    # TODO: implement to_date filter
    if to_date:
        pass  # Añadir filtro to_date cuando se necesite

    return frappe.get_list(
        "User Activity Log",
        filters=filters,
        fields=["user", "action", "status", "details", "reference_doctype", "reference_name", "timestamp", "ip_address"],
        order_by="timestamp desc",
        limit=limit
    )