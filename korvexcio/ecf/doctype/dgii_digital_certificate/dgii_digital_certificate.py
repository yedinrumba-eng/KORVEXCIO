"""Controller for the company-scoped DGII Digital Certificate DocType.

El .p12 se guarda como Attach (archivo privado) y la contrasena como
Password (Frappe la cifra en reposo y nunca la devuelve por la API REST -
CLAUDE.md regla 6, docs/08-BLUEPRINT.md S2.2). Sin adapter HTTP ni logica
de firma todavia: eso vive en providers/ (S2.6/S2.7), este DocType solo
guarda el material y avisa cuando esta por vencer.
"""

from datetime import date

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class DGIIDigitalCertificate(Document):
    def validate(self) -> None:
        message = expiry_message(self.company, self.valid_until, self.expiry_warning_days)
        if message:
            frappe.msgprint(message, indicator="red" if "vencio" in message else "orange", alert=True)


def days_until_expiry(valid_until, today: date | None = None) -> int:
    return (getdate(valid_until) - (today or date.today())).days


def expiry_message(company: str, valid_until, warning_days: int, today: date | None = None) -> str | None:
    """Pure function, testable sin insertar nada en la base."""
    days_left = days_until_expiry(valid_until, today)
    if days_left < 0:
        return frappe._("El certificado de {0} ya vencio.").format(company)
    if days_left <= warning_days:
        return frappe._("El certificado de {0} vence en {1} dias.").format(company, days_left)
    return None
