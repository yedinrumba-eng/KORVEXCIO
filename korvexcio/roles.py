import frappe

VLJ = "VAPERIA LA J Y EL JALAPEÑO"
ESE = "EL SABOR DE LAS 5 ESQUINAS"

ROLES = ["Cajero VLJ", "Cajero ESE", "Dueño", "Contador"]

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

CAJERO_ROLES = ["Cajero VLJ", "Cajero ESE"]

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


def sync_roles():
    for role in ROLES:
        ensure_role(role)

    ensure_doc_perm("User", "Dueño", DUENO_USER_PERMS)
    ensure_doc_perm("Role", "Dueño", BASIC_READ)
    # el dueño crea cajeros Y los restringe a su Company -- necesita
    # poder crear "User Permission", si no la mitad del flujo se queda a medias
    ensure_doc_perm("User Permission", "Dueño", {"read": 1, "write": 1, "create": 1})

    for role in ROLES:
        ensure_doc_perm("Company", role, BASIC_READ)

    for role in CAJERO_ROLES:
        ensure_doc_perm("Sales Invoice", role, CAJERO_SALES_INVOICE_PERMS)
    ensure_doc_perm("Sales Invoice", "Dueño", DUENO_SALES_INVOICE_PERMS)
    ensure_doc_perm("Sales Invoice", "Contador", CONTADOR_SALES_INVOICE_PERMS)

    for role in CAJERO_ROLES:
        ensure_doc_perm("POS Profile", role, BASIC_READ)
    ensure_doc_perm("POS Profile", "Dueño", DUENO_POS_PROFILE_PERMS)

    frappe.db.commit()


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
