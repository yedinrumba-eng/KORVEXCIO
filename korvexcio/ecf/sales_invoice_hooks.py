"""doc_events para Sales Invoice (S2.9) -- Sales Invoice es de ERPNext,
nunca se toca su codigo (CLAUDE.md regla 1); todo esto entra por
korvexcio/hooks.py's doc_events, nunca por override_doctype_class.

D21 (esta sesion): sin correspondencia real de proveedor (S0.9/S2.7,
D20), el tipo de e-CF se decide con la unica senal que ya existe en el
documento -- Sales Invoice.tax_id lleno o no. Si el cliente pidio
factura con RNC -> E31 (credito fiscal). Si no -> E32 (consumo, el 95%
del volumen de este POS). El flujo completo de E31 (validaciones propias
de credito fiscal) se termina de formalizar en S2.13; aqui solo se elige
el tipo para poder reservar el eNCF correcto.

El POS nunca espera a la DGII para cerrar una venta (CLAUDE.md regla 3):
todo lo de aqui es local -- reservar un numero de una secuencia propia y
crear un registro ECF en estado Pendiente. La llamada real al proveedor
(FiscalProvider.emitir, S2.6/S2.7) se dispara despues, desde la cola
asincrona de S2.10, nunca desde este hook.
"""

from __future__ import annotations

import frappe

RNC_REQUIRED_THRESHOLD = 250_000
FINAL_ECF_STATES = {"Aceptado", "Enviando"}

_ENCF_FLAG = "_korvexcio_reserved_encf"
_TIPO_ECF_FLAG = "_korvexcio_tipo_ecf"


def _tipo_ecf_for(doc) -> str:
    """D21: con RNC en la factura -> E31 (credito fiscal). Sin RNC -> E32
    (consumo). Norma 05-19 exige el RNC a partir de RD$250,000; por debajo
    de eso es el cliente quien decide si lo da. "E31"/"E32" (con prefijo)
    para calzar con el Select de Secuencia eNCF y de ECF."""
    return "E31" if _buyer_rnc(doc) else "E32"


def _buyer_rnc(doc) -> str:
    """Return the buyer identifier from Korvex's custom Customer field.

    ``tax_id`` is retained as a migration fallback for existing ERPNext data;
    new fiscal data is stored in the agreed ``Customer.rnc`` field.
    """
    if not doc.get("customer"):
        return ""
    values = frappe.db.get_value("Customer", doc.customer, ["rnc", "tax_id"], as_dict=True)
    if not values:
        return ""
    return values.get("rnc") or values.get("tax_id") or ""


def validate_rnc_threshold(doc, method=None) -> None:
    """Regla 9 de CLAUDE.md: el RNC se exige a partir de RD$250,000 --
    lo hace el sistema, no el criterio del cajero (Norma 05-19)."""
    amount_dop = getattr(doc, "base_grand_total", 0) or doc.grand_total
    if amount_dop >= RNC_REQUIRED_THRESHOLD and not _buyer_rnc(doc):
        frappe.throw(
            frappe._(
                "Ventas de RD${0} o más necesitan el RNC del comprador (Norma 05-19). "
                "Esta factura es de RD${1}."
            ).format(f"{RNC_REQUIRED_THRESHOLD:,}", f"{amount_dop:,.2f}"),
            frappe.ValidationError,
        )


def reserve_encf(doc, method=None) -> None:
    """Reserva el proximo numero de la Secuencia eNCF de esta Company y
    este tipo. No crea el ECF todavia -- eso es on_submit. Si la
    secuencia no existe, es un hueco de aprovisionamiento (S5.4), no algo
    que este hook deba inventar."""
    tipo_ecf = _tipo_ecf_for(doc)
    secuencia_name = f"{doc.company}-{tipo_ecf}"

    if not frappe.db.exists("Secuencia eNCF", secuencia_name):
        frappe.throw(
            frappe._(
                "No hay una Secuencia eNCF configurada para {0}, tipo {1}. "
                "Un Dueño tiene que crearla antes de facturar."
            ).format(doc.company, tipo_ecf),
            frappe.ValidationError,
        )

    secuencia = frappe.get_doc("Secuencia eNCF", secuencia_name)
    encf = secuencia.reserve_next()

    doc.set(_ENCF_FLAG, encf)
    doc.set(_TIPO_ECF_FLAG, tipo_ecf)


def create_ecf_record(doc, method=None) -> None:
    """Crea el documento ECF en estado Pendiente, referenciando esta
    Sales Invoice. La emision real contra el proveedor la dispara la cola
    de S2.10 -- este hook nunca llama a un FiscalProvider."""
    encf = doc.get(_ENCF_FLAG)
    tipo_ecf = doc.get(_TIPO_ECF_FLAG)
    if not encf or not tipo_ecf:
        frappe.throw(
            frappe._("La factura se sometió sin haber reservado un eNCF primero (before_submit no corrió)."),
            frappe.ValidationError,
        )

    ecf = frappe.get_doc(
        {
            "doctype": "ECF",
            "company": doc.company,
            "reference_doctype": "Sales Invoice",
            "reference_name": doc.name,
            "tipo_ecf": tipo_ecf,
            "encf": encf,
            "estado": "Pendiente",
        }
    )
    # This is an internal record created by the trusted Sales Invoice hook;
    # POS cashiers must not need direct ECF create permission.
    ecf.insert(ignore_permissions=True)

    # S2.10: el POS nunca espera a la DGII (CLAUDE.md regla 3). El job
    # real corre despues del commit, en un worker aparte -- si la venta
    # se revierte por cualquier razon, el job ni se encola.
    frappe.enqueue(
        "korvexcio.ecf.tasks.emitir_ecf",
        queue="short",
        enqueue_after_commit=True,
        ecf_name=ecf.name,
    )


def block_cancel_if_accepted(doc, method=None) -> None:
    """Espejo de ECF.before_cancel (S2.4): un e-CF ya aceptado por la
    DGII no se cancela desde ERPNext, se anula ante la DGII (S2.11)."""
    estado = frappe.db.get_value(
        "ECF",
        {"reference_doctype": "Sales Invoice", "reference_name": doc.name},
        "estado",
    )
    if estado == "Enviando":
        frappe.throw(
            frappe._("Esta factura tiene una emisión e-CF en curso. Espere el resultado antes de cancelar."),
            frappe.ValidationError,
        )
    if estado == "Aceptado":
        frappe.throw(
            frappe._(
                "Esta factura ya tiene un e-CF aceptado por la DGII. No se cancela: se anula (S2.11)."
            ),
            frappe.ValidationError,
        )
