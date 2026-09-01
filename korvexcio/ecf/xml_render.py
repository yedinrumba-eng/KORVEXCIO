"""Render de las plantillas Jinja2 de e-CF (S2.8, extendida en S2.13).

Traducidas 1:1 (mismos tags, mismo orden) de resources/views/ecf/ecf_32.blade.php
y resources/views/rfce/xml.blade.php del repo MIT `platinum-place/laravel-dgii`
(verificado en docs/08-BLUEPRINT.md S0.9/S2.1 como fuente real en produccion).

templates/ecf.xml (renombrado de ecf_32.xml en S2.13) sirve para E31, E32 y
E34 -- se comparo linea por linea contra ecf_31.blade.php y ecf_34.blade.php
del mismo repo: la unica diferencia real son un puñado de campos opcionales
(FechaVencimientoSecuencia en E31; IndicadorNotaCredito y las retenciones
TotalITBISRetenido/TotalISRRetencion/TotalITBISPercepcion en E34), ya
agregados al mismo template con sus propios `'X' in Grupo` -- "misma
maquinaria", tal como pide el blueprint, no tres archivos casi identicos.

NO estan validadas contra el XSD oficial de la DGII -- no lo tenemos. Bajarlo
requiere el mismo acceso que sigue bloqueado por D20 (S0.9/S2.7): sin RNC ni
certificado del cliente no hay portal de la DGII que lo entregue. Cuando eso
se resuelva, este render se re-valida contra el XSD real antes de S5.4
(certificacion como emisor). Lo unico que se puede verificar hoy, de verdad,
es que el XML resultante es bien formado -- ver validate_well_formed().

El ambiente Jinja de Frappe (frappe.utils.jinja.get_jenv()) es compartido con
TODO el resto de la plataforma -- print formats, correos, etc. Prender
trim_blocks/lstrip_blocks para que estas plantillas no dejen lineas en blanco
y NO restaurarlo despues rompe cualquier otro template que se renderice en la
misma request. Por eso el toggle vive en un try/finally.
"""

from __future__ import annotations

import os
from datetime import datetime
from xml.etree import ElementTree
from xml.sax.saxutils import escape as xml_escape
from zoneinfo import ZoneInfo

import frappe

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
_REQUIRED_GROUPS = ("IdDoc", "Emisor", "Totales")
_RD_TZ = ZoneInfo("America/Santo_Domingo")


def _escape_value(value):
    if isinstance(value, str):
        return xml_escape(value)
    if isinstance(value, dict):
        return {key: _escape_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_escape_value(item) for item in value]
    return value


def _prepare_context(context: dict) -> dict:
    """Escapa todo string del contexto (un nombre de cliente con '&' o '<'
    no puede tumbar el parser de la DGII) y garantiza que los grupos
    obligatorios existan como dict real, para que el template pueda hacer
    'campo' in Grupo sin toparse con un Undefined."""
    prepared = _escape_value(context)
    for group in _REQUIRED_GROUPS:
        prepared.setdefault(group, {})
    return prepared


def _render(template_filename: str, context: dict) -> str:
    template_path = os.path.join(TEMPLATES_DIR, template_filename)
    with open(template_path, encoding="utf-8") as f:
        template_source = f.read()

    from frappe.utils.jinja import get_jenv

    jenv = get_jenv()
    original_trim, original_lstrip = jenv.trim_blocks, jenv.lstrip_blocks
    jenv.trim_blocks = True
    jenv.lstrip_blocks = True
    try:
        compiled = jenv.from_string(template_source)
        return compiled.render(**context)
    finally:
        jenv.trim_blocks = original_trim
        jenv.lstrip_blocks = original_lstrip


def _render_ecf(context: dict) -> str:
    """context: dict con IdDoc/Emisor/Comprador/Totales/DetallesItems/etc,
    mismos nombres de campo que el e-CF oficial (ver templates/ecf.xml). El
    mapeo real desde Sales Invoice / ECF vive en S2.9/D21 -- este render no
    lo asume; el propio contexto (IdDoc.TipoeCF) dice de que tipo es."""
    prepared = _prepare_context(context)
    prepared.setdefault("FechaHoraFirma", datetime.now(tz=_RD_TZ).strftime("%d-%m-%Y %H:%M:%S"))
    return _render("ecf.xml", prepared)


# render_ecf_32 es el nombre historico (S2.8, el 95% del volumen del POS).
# render_ecf_31/render_ecf_34 son el mismo render (S2.13) -- un solo
# template generico, el tipo lo decide IdDoc.TipoeCF en el contexto.
render_ecf_32 = _render_ecf
render_ecf_31 = _render_ecf
render_ecf_34 = _render_ecf


def render_rfce(context: dict) -> str:
    """CodigoSeguridadeCF no es opcional en el formato RFCE -- lo devuelve
    el proveedor al aceptar el e-CF individual que se resume (S2.7)."""
    prepared = _prepare_context(context)
    if "CodigoSeguridadeCF" not in prepared:
        frappe.throw(frappe._("RFCE necesita CodigoSeguridadeCF, lo devuelve el proveedor al aceptar el e-CF."))
    return _render("rfce.xml", prepared)


def validate_well_formed(xml_string: str) -> None:
    """No es el XSD oficial de la DGII (no lo tenemos, D20) -- solo confirma
    que el XML resultante parsea. Levanta xml.etree.ElementTree.ParseError
    si no es bien formado."""
    ElementTree.fromstring(xml_string)
