"""Company access control — centralizador de verificación de acceso a Company.

Reemplaza llamadas duplicadas a `_assert_user_may_view_company()` en reports.py,
dashboard.py y futuros módulos. Un solo punto de verdad para el aislamiento lógico
entre Companies (D19)."""

from __future__ import annotations

import functools
from typing import Any, Callable

import frappe
from frappe import _


def require_company_access(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator que valida acceso a Company antes de ejecutar la función.

    Uso:
        @require_company_access
        def mi_funcion(company: str, ...):
            ...

    La función decorada DEBE tener un parámetro `company` (str) como primer
    argumento posicional o keyword. Si el usuario no tiene acceso, lanza
    `frappe.PermissionError`.

    System Manager pasa sin chequeo (compatibilidad con jobs de sistema).
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Extraer `company` de args o kwargs
        company = None
        if args:
            company = args[0]
        elif "company" in kwargs:
            company = kwargs["company"]

        if not isinstance(company, str) or not company.strip():
            frappe.throw(_("Company is required"), frappe.ValidationError)

        _assert_user_may_view_company(company.strip())
        return func(*args, **kwargs)

    return wrapper


def _assert_user_may_view_company(company: str) -> None:
    """Verifica que el usuario actual puede ver datos de `company`.

    Sistema de permisos: User Permission (allow=Company, for_value=company).
    Si el usuario NO tiene User Permissions de Company, no está acotado por
    diseño (p.ej. sesiones de servicio) — no denegar por ausencia.
    Solo denegar cuando SÍ está acotado a otra Company distinta.
    """
    if "System Manager" in frappe.get_roles():
        return

    allowed_companies = frappe.get_all(
        "User Permission",
        filters={"user": frappe.session.user, "allow": "Company"},
        pluck="for_value",
    )

    if allowed_companies and company not in allowed_companies:
        frappe.throw(
            _("No tienes acceso a los datos de {0}.").format(company),
            frappe.PermissionError,
        )


def get_user_allowed_companies() -> list[str]:
    """Retorna lista de Companies a las que el usuario actual tiene acceso.

    Retorna lista vacía si el usuario no tiene User Permissions de Company
    (acceso sin restricción por diseño, p.ej. System Manager, servicios).
    """
    if "System Manager" in frappe.get_roles():
        return []

    return frappe.get_all(
        "User Permission",
        filters={"user": frappe.session.user, "allow": "Company"},
        pluck="for_value",
    )


def filter_companies_by_permission(companies: list[str]) -> list[str]:
    """Filtra una lista de Companies dejando solo las que el usuario puede ver.

    Si el usuario no tiene User Permissions de Company, retorna la lista original
    (no acotado por diseño).
    """
    allowed = get_user_allowed_companies()
    if not allowed:
        return companies
    return [c for c in companies if c in allowed]