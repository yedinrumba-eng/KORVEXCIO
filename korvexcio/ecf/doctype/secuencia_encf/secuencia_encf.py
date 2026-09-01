"""Controller for Secuencia eNCF - rangos de comprobantes fiscales por
Company y tipo de e-CF (E31/E32/E34).

Nombre compuesto {company}-{tipo_ecf} via autoname (format:) en vez de
un campo unique simple: dos secuencias del mismo tipo para la misma
Company chocan por nombre duplicado, que es exactamente lo que se quiere.

reserve_next() usa frappe.db.get_value(..., for_update=True) -- un SELECT
... FOR UPDATE real, pero via el query builder de Frappe, no
frappe.db.sql() crudo (eso si esta prohibido, CLAUDE.md 12b). El lock de
fila vive hasta que la transaccion de la request hace commit, que es
exactamente cuando S2.9 va a llamar esto: dentro del mismo before_submit
de la venta, misma transaccion.
"""

import frappe
from frappe.model.document import Document


class SecuenciaeNCF(Document):
    def validate(self) -> None:
        self._validate_range()
        self._warn_if_low()

    def _validate_range(self) -> None:
        if self.desde > self.hasta:
            frappe.throw(frappe._("'Desde' no puede ser mayor que 'Hasta'."))
        if not (self.desde <= self.siguiente <= self.hasta + 1):
            frappe.throw(
                frappe._("'Siguiente' debe estar entre {0} y {1}.").format(
                    self.desde, self.hasta + 1
                )
            )

    def _warn_if_low(self) -> None:
        remaining = self.hasta + 1 - self.siguiente
        if remaining <= 0:
            frappe.msgprint(
                frappe._("La secuencia {0} de {1} esta agotada.").format(
                    self.tipo_ecf, self.company
                ),
                indicator="red",
                alert=True,
            )
        elif remaining <= self.warning_threshold:
            frappe.msgprint(
                frappe._("La secuencia {0} de {1} tiene solo {2} numeros disponibles.").format(
                    self.tipo_ecf, self.company, remaining
                ),
                indicator="orange",
                alert=True,
            )

    def reserve_next(self) -> str:
        """Reserva el siguiente numero de la secuencia y devuelve el eNCF
        completo (ej. E320000000001). SELECT ... FOR UPDATE via el query
        builder (no SQL crudo) para que dos reservas concurrentes nunca
        entreguen el mismo numero -- el lock de fila vive hasta el commit
        de la transaccion actual. Llamado por korvexcio.hooks antes de
        emitir (S2.9)."""
        siguiente, hasta, tipo_ecf = frappe.db.get_value(
            self.doctype, self.name, ["siguiente", "hasta", "tipo_ecf"], for_update=True
        )

        if siguiente > hasta:
            frappe.throw(
                frappe._("La secuencia {0} de {1} esta agotada.").format(
                    tipo_ecf, self.company
                )
            )

        frappe.db.set_value(self.doctype, self.name, "siguiente", siguiente + 1)
        self.reload()

        return f"{tipo_ecf}{siguiente:010d}"
