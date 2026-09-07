"""Roles and permissions management - sync, doc perms, company access.

FASE 4.8: Separado de roles.py.
Contiene: sync_roles, sync_transactional_doctype_perms, sync_ecf_doctype_perms,
ensure_role, ensure_doc_perm, assign_company_user_permission,
CAJERO_ROLES, VLJ, ESE, ROLES, and permission constants.
"""

from __future__ import annotations

import frappe
from frappe import _


# =============================================================================
# Constants
# =============================================================================

VLJ = "VAPERIA LA J Y EL JALAPEÑO"
ESE = "EL SABOR DE LAS 5 ESQUINAS"

ROLES = ["Cajero VLJ", "Cajero ESE", "Dueño", "Contador"]

CAJERO_ROLES = ["Cajero VLJ", "Cajero ESE"]

# Dueño necesita crear cajeros con un rol acotado -- NO System Manager
# (blueprint S1.7). Se le da acceso al doctype User y a leer Role para
# poder marcar los checkboxes de rol en el formulario, nada mas.
DUENO_USER_PERMS = {
    "read": 1,
    "write": 1,
    "create": 1,
    "delete": 0,
    "print": 1,
    "email": 1,
    "share": 0,
    "report": 1,
}

BASIC_READ = {"read": 1}

# Hallazgo real (2026-09-01): ningun rol propio tenia NINGUN permiso sobre
# Sales Invoice -- ni siquiera leer. Paso desapercibido porque S2.9 en
# adelante siempre probo como Administrator. Un Cajero real no podia ni
# ver el formulario de venta. Un Cajero somete la venta (S2.9) pero nunca
# la cancela libremente -- eso es control de caja, va a Dueño.
CAJERO_SALES_INVOICE_PERMS = {"create": 1, "read": 1, "write": 1, "submit": 1}
DUENO_SALES_INVOICE_PERMS = {"create": 1, "read": 1, "write": 1, "submit": 1, "cancel": 1}
CONTADOR_SALES_INVOICE_PERMS = {"read": 1}

# S4.1: el cajero solo LEE su POS Profile (get_pos_profile() de ERPNext lo
# resuelve solo). Configurarlo -- warehouse, metodos de pago, usuarios
# asignados -- es tarea de Dueño, nunca del cajero.
DUENO_POS_PROFILE_PERMS = {"create": 1, "read": 1, "write": 1}

# S4.5: el cajero abre y cierra SU propio turno (create/read/write/submit)
# pero no puede cancelarlo -- eso es control de caja, va a Dueño. El
# arqueo ya es visible via submit; cancelar un turno cerrado es reabrir
# la caja del dia anterior.
CAJERO_CASH_SHIFT_PERMS = {"create": 1, "read": 1, "write": 1, "submit": 1}
DUENO_CASH_SHIFT_PERMS = {"create": 1, "read": 1, "write": 1, "submit": 1, "cancel": 1}
CONTADOR_CASH_SHIFT_PERMS = {"read": 1}


# =============================================================================
# Role/permission sync functions
# =============================================================================

def sync_roles() -> None:
    """Sync all roles and permissions for KORVEXCIO.

    Called from hooks.py after_migrate. Idempotent.
    """
    for role in ROLES:
        ensure_role(role)

    ensure_doc_perm("User", "Dueño", DUENO_USER_PERMS)
    ensure_doc_perm("Role", "Dueño", BASIC_READ)
    # el dueño crea cajeros Y los restringe a su Company -- necesita
    # poder crear "User Permission", si no la mitad del flujo se queda a medias
    ensure_doc_perm("User Permission", "Dueño", {"read": 1, "write": 1, "create": 1})

    for role in ROLES:
        ensure_doc_perm("Company", role, BASIC_READ)

    # Hallazgo real (2026-09-01, S4.5): un Cajero real no podia someter NI
    # UNA venta -- ERPNext valida permiso de LECTURA sobre `Account` al
    # someter cualquier Sales Invoice (income_account, debit_to, etc.), y
    # ningun rol propio lo tenia. Tampoco tenia permiso sobre `Customer`
    # -- no podia ni buscar a quien venderle. Ambos pasaron
    # desapercibidos porque S2.9 solo se probo como Administrator; S4.5
    # es el primer test que somete una venta como un Cajero real.
    for role in CAJERO_ROLES:
        ensure_doc_perm("Account", role, BASIC_READ)
        ensure_doc_perm("Customer", role, {"create": 1, "read": 1})
        ensure_doc_perm("Item", role, BASIC_READ)
        ensure_doc_perm("Cost Center", role, BASIC_READ)
        ensure_doc_perm("UOM", role, BASIC_READ)
        ensure_doc_perm("Mode of Payment", role, BASIC_READ)
    ensure_doc_perm("Customer", "Dueño", {"create": 1, "read": 1, "write": 1})
    ensure_doc_perm("Customer", "Contador", BASIC_READ)

    for role in CAJERO_ROLES:
        ensure_doc_perm("Sales Invoice", role, CAJERO_SALES_INVOICE_PERMS)
    ensure_doc_perm("Sales Invoice", "Dueño", DUENO_SALES_INVOICE_PERMS)
    ensure_doc_perm("Sales Invoice", "Contador", CONTADOR_SALES_INVOICE_PERMS)

    for role in CAJERO_ROLES:
        ensure_doc_perm("POS Profile", role, BASIC_READ)
    ensure_doc_perm("POS Profile", "Dueño", DUENO_POS_PROFILE_PERMS)

    # "... Entry" son los nativos de ERPNext (S4.5); "... Shift" son los
    # propios de POSNext (S4.2) -- la pantalla real crea estos ultimos,
    # no sabemos cual va a quedar en pie a largo plazo.
    for doctype in ("POS Opening Entry", "POS Closing Entry", "POS Opening Shift", "POS Closing Shift"):
        for role in CAJERO_ROLES:
            ensure_doc_perm(doctype, role, CAJERO_CASH_SHIFT_PERMS)
        ensure_doc_perm(doctype, "Dueño", DUENO_CASH_SHIFT_PERMS)
        ensure_doc_perm(doctype, "Contador", CONTADOR_CASH_SHIFT_PERMS)

    # --- S5.3: Transactional doctypes permissions ---
    sync_transactional_doctype_perms()

    # --- S5.3: ECF doctypes permissions ---
    sync_ecf_doctype_perms()

    frappe.db.commit()


def sync_transactional_doctype_perms() -> None:
    """S5.3: Permisos para doctypes transaccionales de ERPNext."""
    transactional_doctypes = [
        "Sales Invoice",
        "Sales Order",
        "Delivery Note",
        "Purchase Invoice",
        "Purchase Order",
        "Purchase Receipt",
        "Stock Entry",
        "Payment Entry",
        "Journal Entry",
        "POS Opening Entry",
        "POS Closing Entry",
        "POS Opening Shift",
        "POS Closing Shift",
    ]

    for doctype in transactional_doctypes:
        for role in CAJERO_ROLES:
            ensure_doc_perm(doctype, role, CAJERO_SALES_INVOICE_PERMS)
        ensure_doc_perm(doctype, "Dueño", DUENO_SALES_INVOICE_PERMS)
        ensure_doc_perm(doctype, "Contador", CONTADOR_SALES_INVOICE_PERMS)


def sync_ecf_doctype_perms() -> None:
    """S5.3: Permisos para doctypes ECF propios."""
    ecf_doctypes = [
        "ECF",
        "ECF Settings",
        "ECF Integration Log",
        "ECF Contingencia",
        "ECF Print Queue",
        "Secuencia eNCF",
        "DGII Settings",
        "DGII Digital Certificate",
    ]

    # Cajeros: solo leen ECF (para ver estado) y leen ECF Print Queue (para reimprimir)
    # Dueño: full access (create/read/write/submit/cancel)
    # Contador: read only
    for doctype in ecf_doctypes:
        for role in CAJERO_ROLES:
            if doctype in ("ECF", "ECF Print Queue"):
                ensure_doc_perm(doctype, role, {"read": 1})
            else:
                ensure_doc_perm(doctype, role, {})
        ensure_doc_perm(doctype, "Dueño", {"create": 1, "read": 1, "write": 1, "submit": 1, "cancel": 1})
        ensure_doc_perm(doctype, "Contador", {"read": 1})


def ensure_role(role_name: str) -> None:
    if frappe.db.exists("Role", role_name):
        return
    frappe.get_doc(
        {
            "doctype": "Role",
            "role_name": role_name,
            "desk_access": 1,
        }
    ).insert()


def ensure_doc_perm(doctype: str, role: str, perms: dict) -> None:
    existing = frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role})
    if existing:
        return

    doc = frappe.get_doc(
        {
            "doctype": "Custom DocPerm",
            "parent": doctype,
            "parenttype": "DocType",
            "parentfield": "permissions",
            "role": role,
            **perms,
        }
    )
    doc.insert()


def assign_company_user_permission(user: str, company: str) -> None:
    """Restringe a `user` a ver solo `company`. Se puede llamar varias
    veces con distintas companies para el mismo usuario (caso Dueño:
    una fila por Company, ve las dos, nunca una tercera sin permiso
    explicito)."""
    if frappe.db.exists(
        "User Permission", {"user": user, "allow": "Company", "for_value": company}
    ):
        return

    frappe.get_doc(
        {
            "doctype": "User Permission",
            "user": user,
            "allow": "Company",
            "for_value": company,
            "apply_to_all_doctypes": 1,
        }
    ).insert()


# =============================================================================
# Re-export constants for backward compatibility
# =============================================================================

__all__ = [
    # Constants
    "VLJ",
    "ESE",
    "ROLES",
    "CAJERO_ROLES",
    "DUENO_USER_PERMS",
    "BASIC_READ",
    "CAJERO_SALES_INVOICE_PERMS",
    "DUENO_SALES_INVOICE_PERMS",
    "CONTADOR_SALES_INVOICE_PERMS",
    "DUENO_POS_PROFILE_PERMS",
    "CAJERO_CASH_SHIFT_PERMS",
    "DUENO_CASH_SHIFT_PERMS",
    "CONTADOR_CASH_SHIFT_PERMS",
    # Functions
    "sync_roles",
    "sync_transactional_doctype_perms",
    "sync_ecf_doctype_perms",
    "ensure_role",
    "ensure_doc_perm",
    "assign_company_user_permission",
]