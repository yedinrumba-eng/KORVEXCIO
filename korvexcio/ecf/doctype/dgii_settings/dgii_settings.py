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
        # CR-31: Max 300s (5 min) porque:
        # - DGII TesteCF/CerteCF responden típicamente en <30s
        # - 300s cubre latencia alta + retries internos del proveedor
        # - Más de 5 min bloquearía worker queue-short innecesariamente
        # - Alineado con timeouts por defecto de requests/httpx (30-60s) + buffer
        if not 1 <= timeout <= 300:
            frappe.throw(message, frappe.ValidationError)
