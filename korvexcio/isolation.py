"""La barrera de aislamiento de D19 (S1.8).

Frappe ya trae, nativo, el equivalente de RLS: `permission_query_conditions`
+ `has_permission`, evaluados automaticamente para cualquier Link field
llamado "Company" via User Permission (probado en S1.7 contra Warehouse,
Company, etc. con un usuario real, no con Administrator).

Lo que Frappe NO trae solo es el equivalente de un `WITH CHECK`: nada le
impide a un documento ya creado en la Company A que alguien le cambie el
campo `company` a la B despues de guardado. Eso es lo que esta pieza tapa.

Doctypes propios de korvexcio (ECF, etc., Fase 2) todavia no existen —
cuando se creen, se agregan a COMPANY_SCOPED_DOCTYPES.
"""

import frappe

# Doctypes de ERPNext con campo `company` que ya tienen datos reales hoy
# (S0.7, S0.7). Los propios de korvexcio se agregan aqui cuando existan
# (Fase 2: ECF, ECF Settings, Secuencia eNCF...).
COMPANY_SCOPED_DOCTYPES = {
    "Warehouse",
    "Cost Center",
    "Sales Invoice",
    "Sales Order",
    "Delivery Note",
    "Payment Entry",
    "Item Price",
    "DGII Settings",
    "DGII Digital Certificate",
    "Secuencia eNCF",
    "ECF",
    "ECF Integration Log",
    "ECF Contingencia",
    "POS Profile",
}


def freeze_company(doc, method=None):
    """`validate` hook — equivalente al `WITH CHECK` de una politica RLS.

    Si el documento ya existia (no es `doc.is_new()`) y el campo `company`
    cambio contra lo que hay en la base, se rechaza. No aplica a
    documentos nuevos: ahi `company` se esta fijando por primera vez.
    """
    if doc.doctype not in COMPANY_SCOPED_DOCTYPES:
        return
    if not doc.meta.has_field("company"):
        return
    if doc.is_new():
        return

    company_en_db = frappe.db.get_value(doc.doctype, doc.name, "company")
    if company_en_db and doc.company != company_en_db:
        frappe.throw(
            frappe._(
                "No se puede mover {0} {1} de {2} a {3}. La Company de un documento no se cambia despues de creado."
            ).format(doc.doctype, doc.name, company_en_db, doc.company),
            frappe.PermissionError,
        )
