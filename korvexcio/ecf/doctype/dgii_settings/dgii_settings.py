"""Controller for the company-scoped DGII Settings DocType."""

import frappe
from frappe.model.document import Document


class DGIISettings(Document):
    def validate(self) -> None:
        self._validate_timeout(
            self.connect_timeout_seconds,
            frappe._("El tiempo de conexion debe estar entre 1 y 300 segundos."),
        )
        self._validate_timeout(
            self.read_timeout_seconds,
            frappe._("El tiempo de lectura debe estar entre 1 y 300 segundos."),
        )

    @staticmethod
    def _validate_timeout(timeout: int, message: str) -> None:
        if not 1 <= timeout <= 300:
            frappe.throw(message, frappe.ValidationError)
