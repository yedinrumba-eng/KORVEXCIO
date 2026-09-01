"""Controller for the ECF DocType - el documento fiscal electronico.

Es submittable: el docstatus (0 Draft / 1 Submitted / 2 Cancelled) es la
maquina de estados de "se emitio o no", separado de `estado` (Pendiente/
Aceptado/Rechazado/Contingencia/Anulado), que es la respuesta real de la
DGII/proveedor. No hay logica de emision todavia (S2.6/S2.7 - la interfaz
de providers y el proveedor real no existen aun); este slice solo modela
el documento y sus reglas de negocio basicas.
"""

import frappe
from frappe.model.document import Document

# Un e-CF ya aceptado por la DGII nunca se cancela ni se borra -- se anula
# (mecanismo separado, Fase 2 mas adelante). Es un registro legal.
FINAL_STATES = {"Aceptado"}


class ECF(Document):
    def before_cancel(self) -> None:
        if self.estado in FINAL_STATES:
            frappe.throw(
                frappe._(
                    "El e-CF {0} ya fue aceptado por la DGII. No se cancela: se anula."
                ).format(self.encf or self.name),
                frappe.ValidationError,
            )

    def on_trash(self) -> None:
        if self.estado in FINAL_STATES:
            frappe.throw(
                frappe._(
                    "El e-CF {0} ya fue aceptado por la DGII. No se puede borrar un documento fiscal aceptado."
                ).format(self.encf or self.name),
                frappe.ValidationError,
            )
