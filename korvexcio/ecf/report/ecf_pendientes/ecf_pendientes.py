"""Panel de e-CF pendientes (S2.14) -- regla 4 del CLAUDE.md global:
ninguna venta se pierde en silencio, y lo pendiente no vive solo en un
log. Junta ECF (Pendiente/Enviando, S2.10) y ECF Contingencia (todavia
sin Aceptado, S2.11) en una sola vista, ordenada por antigüedad -- lo
mas viejo primero, porque eso es lo que mas urge revisar.

frappe.get_all() respeta permisos/User Permission nativos, pero el
reporte ADEMAS filtra por `company` explicito cuando se pasa como filtro
(regla 12b: "los reportes propios filtran por company explicitamente --
no se confia en que User Permission lo haga solo". El PR
frappe/erpnext#44695 -- User Permission no se aplicaba en los estados
financieros -- es justo el bug que esta defensa en profundidad evita).
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, time_diff_in_hours

_ECF_PENDING_STATES = ("Pendiente", "Enviando")
_CONTINGENCIA_UNRESOLVED_STATES = ("PendienteDeEnviar", "Enviado", "Rechazado")


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data = _get_ecf_rows(filters) + _get_contingencia_rows(filters)
    data.sort(key=lambda row: row["creation"])
    return columns, data


def get_columns():
    return [
        {"label": _("Tipo"), "fieldname": "tipo", "fieldtype": "Data", "width": 120},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 180},
        {
            "label": _("Documento"),
            "fieldname": "name",
            "fieldtype": "Dynamic Link",
            "options": "doctype",
            "width": 140,
        },
        {"label": _("e-NCF"), "fieldname": "encf", "fieldtype": "Data", "width": 150},
        {"label": _("Estado"), "fieldname": "estado", "fieldtype": "Data", "width": 130},
        {"label": _("Horas esperando"), "fieldname": "horas_esperando", "fieldtype": "Float", "width": 140},
    ]


def _company_filters(filters: dict) -> dict:
    query_filters = {}
    if filters.get("company"):
        query_filters["company"] = filters["company"]
    return query_filters


def _get_ecf_rows(filters: dict) -> list[dict]:
    query_filters = _company_filters(filters)
    query_filters["estado"] = ["in", _ECF_PENDING_STATES]

    rows = frappe.get_all(
        "ECF",
        filters=query_filters,
        fields=["name", "company", "encf", "estado", "creation"],
    )
    for row in rows:
        row["tipo"] = "ECF"
        row["doctype"] = "ECF"
        row["horas_esperando"] = round(time_diff_in_hours(now_datetime(), row["creation"]), 1)
    return rows


def _get_contingencia_rows(filters: dict) -> list[dict]:
    query_filters = _company_filters(filters)
    query_filters["estado"] = ["in", _CONTINGENCIA_UNRESOLVED_STATES]

    rows = frappe.get_all(
        "ECF Contingencia",
        filters=query_filters,
        fields=["name", "company", "encf_precomputado as encf", "estado", "creation"],
    )
    for row in rows:
        row["tipo"] = "ECF Contingencia"
        row["doctype"] = "ECF Contingencia"
        row["horas_esperando"] = round(time_diff_in_hours(now_datetime(), row["creation"]), 1)
    return rows
