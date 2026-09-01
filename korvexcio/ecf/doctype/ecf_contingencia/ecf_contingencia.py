"""Controller for ECF Contingencia - patron ZATCA Precomputed Invoice
(S2.11): cuando no hay internet o la DGII no responde, el e-CF se
computa y se firma LOCALMENTE en el momento de la venta (CLAUDE.md
regla 4: "sin internet, el negocio sigue vendiendo") y se entrega al
cliente ahi mismo -- no hay borrador que editar despues.

Por eso es incondicionalmente inmutable: a diferencia de ECF (S2.4), que
solo bloquea borrar/cancelar una vez que la DGII respondio Aceptado, un
ECF Contingencia YA fue entregado en papel al cliente al momento de
crearse. No existe un estado "todavia no se le dio al cliente" que
justifique poder borrarlo o cancelarlo -- ni siquiera Pendiente de
enviar.
"""

import frappe
from frappe.model.document import Document


class ECFContingencia(Document):
    def validate(self) -> None:
        # `reqd: 1` en el JSON NO sirve para este campo: el validador
        # nativo de Frappe (has_content(), en
        # frappe/model/base_document.py) le hace strip_html() a
        # CUALQUIER campo reqd sin importar ignore_xss_filter -- un XML
        # puro sin texto entre tags (p.ej. "<ECF><Encabezado/></ECF>")
        # queda vacio despues de despojar los tags, y Frappe lo rechaza
        # como "faltante" aunque el valor real no lo este. Bug real
        # encontrado por el propio test al escribirlo (MandatoryError en
        # el insert, con el valor visiblemente presente en el objeto).
        if not self.signed_xml:
            frappe.throw(
                frappe._("Un e-CF de contingencia necesita el XML precomputado y firmado."),
                frappe.ValidationError,
            )

    def before_cancel(self) -> None:
        frappe.throw(
            frappe._(
                "El e-CF de contingencia {0} ya fue entregado al cliente en el momento "
                "de la venta. No se cancela: se anula ante la DGII (S2.13)."
            ).format(self.encf_precomputado or self.name),
            frappe.ValidationError,
        )

    def on_trash(self) -> None:
        frappe.throw(
            frappe._(
                "El e-CF de contingencia {0} ya fue entregado al cliente en el momento "
                "de la venta. No se puede borrar un documento fiscal ya entregado, sin "
                "importar su estado."
            ).format(self.encf_precomputado or self.name),
            frappe.ValidationError,
        )
