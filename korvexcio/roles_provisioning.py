"""User provisioning functions - create cashier, owner, accountant users.

FASE 4.8: Separado de roles.py.
Contiene: create_cashier_user, create_owner_user, create_accountant_user,
_validate_password_policy, _get_password_policy, set_password_policy,
configure_session_limits
"""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint

from .roles_permissions import VLJ, ESE, assign_company_user_permission


def _validate_password_policy(password: str) -> None:
    """Valida que la contraseña cumpla la política configurada."""
    policy = _get_password_policy()

    if len(password) < policy.get("min_length", 12):
        frappe.throw(_("La contraseña debe tener al menos {0} caracteres").format(policy.get("min_length", 12)))

    if policy.get("require_special", True):
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/`~]', password):
            frappe.throw(_("La contraseña debe contener al menos un carácter especial"))

    if policy.get("require_upper", True):
        if not any(c.isupper() for c in password):
            frappe.throw(_("La contraseña debe contener al menos una mayúscula"))

    if policy.get("require_lower", True):
        if not any(c.islower() for c in password):
            frappe.throw(_("La contraseña debe contener al menos una minúscula"))

    if policy.get("require_digit", True):
        if not any(c.isdigit() for c in password):
            frappe.throw(_("La contraseña debe contener al menos un número"))


def _get_password_policy() -> dict:
    """Obtiene la política de contraseñas configurada en System Settings."""
    return {
        "min_length": cint(frappe.db.get_single_value("System Settings", "password_min_length")) or 12,
        "require_special": cint(frappe.db.get_single_value("System Settings", "password_require_special")) or 1,
        "require_upper": cint(frappe.db.get_single_value("System Settings", "password_require_upper")) or 1,
        "require_lower": cint(frappe.db.get_single_value("System Settings", "password_require_lower")) or 1,
        "require_digit": cint(frappe.db.get_single_value("System Settings", "password_require_digit")) or 1,
        "expire_days": cint(frappe.db.get_single_value("System Settings", "password_expire_days")) or 90,
    }


def set_password_policy(
    min_length: int = 12,
    require_special: bool = True,
    expire_days: int = 90,
    require_upper: bool = True,
    require_lower: bool = True,
    require_digit: bool = True
) -> None:
    """Configura la política de contraseñas en System Settings.

    Args:
        min_length: Longitud mínima (default 12)
        require_special: Requiere carácter especial (default True)
        expire_days: Días para expirar (default 90)
        require_upper: Requiere mayúscula (default True)
        require_lower: Requiere minúscula (default True)
        require_digit: Requiere dígito (default True)
    """
    frappe.db.set_single_value("System Settings", "password_min_length", min_length)
    frappe.db.set_single_value("System Settings", "password_require_special", int(require_special))
    frappe.db.set_single_value("System Settings", "password_expire_days", expire_days)
    frappe.db.set_single_value("System Settings", "password_require_upper", int(require_upper))
    frappe.db.set_single_value("System Settings", "password_require_lower", int(require_lower))
    frappe.db.set_single_value("System Settings", "password_require_digit", int(require_digit))


def configure_session_limits(
    cashier_hours: int = 8,
    owner_hours: int = 12,
    concurrent_sessions_cashier: int = 1,
    concurrent_sessions_owner: int = 3
) -> None:
    """Configura límites de sesión por rol en System Settings.

    Args:
        cashier_hours: Horas de sesión para cajero (default 8)
        owner_hours: Horas de sesión para dueño (default 12)
        concurrent_sessions_cashier: Sesiones concurrentes para cajero (default 1)
        concurrent_sessions_owner: Sesiones concurrentes para dueño (default 3)
    """
    frappe.db.set_single_value("System Settings", "cashier_session_hours", cashier_hours)
    frappe.db.set_single_value("System Settings", "owner_session_hours", owner_hours)
    frappe.db.set_single_value("System Settings", "concurrent_sessions_cashier", concurrent_sessions_cashier)
    frappe.db.set_single_value("System Settings", "concurrent_sessions_owner", concurrent_sessions_owner)


def create_cashier_user(email: str, full_name: str, company: str, password: str) -> str:
    """Crea un usuario Cajero para la Company especificada.

    Args:
        email: Email del cajero (usado como login)
        full_name: Nombre completo
        company: Company a la que pertenece (VLJ o ESE)
        password: Contraseña inicial (debe cumplir policy)

    Returns:
        Email del usuario creado
    """
    # Validar company
    if company not in (VLJ, ESE):
        frappe.throw(_("Company debe ser '{0}' o '{1}'").format(VLJ, ESE))

    role = "Cajero VLJ" if company == VLJ else "Cajero ESE"

    # Verificar password policy
    _validate_password_policy(password)

    user_doc = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": full_name,
        "user_type": "System User",
        "send_welcome_email": 0,
        "roles": [{"role": role}],
        "new_password": password,
    })
    user_doc.insert()

    # Asignar User Permission por Company
    assign_company_user_permission(email, company)

    frappe.db.commit()
    return email


def create_owner_user(email: str, full_name: str, companies_list: list, password: str) -> str:
    """Crea un usuario Dueño con acceso a las Companies especificadas.

    Args:
        email: Email del dueño (usado como login)
        full_name: Nombre completo
        companies_list: Lista de companies (ej: [VLJ, ESE] o [VLJ])
        password: Contraseña inicial (debe cumplir policy)

    Returns:
        Email del usuario creado
    """
    # Validar companies
    for company in companies_list:
        if company not in (VLJ, ESE):
            frappe.throw(_("Company '{0}' no es válida").format(company))

    # Validar password policy
    _validate_password_policy(password)

    user_doc = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": full_name,
        "user_type": "System User",
        "send_welcome_email": 0,
        "roles": [{"role": "Dueño"}],
        "new_password": password,
    })
    user_doc.insert()

    # Asignar User Permission por cada Company
    for company in companies_list:
        assign_company_user_permission(email, company)

    frappe.db.commit()
    return email


def create_accountant_user(email: str, full_name: str, companies_list: list, password: str) -> str:
    """Crea un usuario Contador con acceso de solo-lectura a las Companies especificadas.

    Args:
        email: Email del contador (usado como login)
        full_name: Nombre completo
        companies_list: Lista de companies (ej: [VLJ, ESE] o [VLJ])
        password: Contraseña inicial (debe cumplir policy)

    Returns:
        Email del usuario creado
    """
    # Validar companies
    for company in companies_list:
        if company not in (VLJ, ESE):
            frappe.throw(_("Company '{0}' no es válida").format(company))

    # Validar password policy
    _validate_password_policy(password)

    user_doc = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": full_name,
        "user_type": "System User",
        "send_welcome_email": 0,
        "roles": [{"role": "Contador"}],
        "new_password": password,
    })
    user_doc.insert()

    # Asignar User Permission por cada Company
    for company in companies_list:
        assign_company_user_permission(email, company)

    frappe.db.commit()
    return email