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
