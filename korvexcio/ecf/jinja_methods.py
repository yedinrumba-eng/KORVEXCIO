"""Funciones expuestas al entorno Jinja compartido de Frappe (hooks.py
`jinja.methods`) para el print format de S2.12. Sin ignore_permissions:
quien imprime ya tiene acceso a la Sales Invoice (via User Permission de
su Company); el ECF vinculado vive en la MISMA Company (freeze_company,
D19), asi que respetar los permisos normales del usuario no rompe nada
y evita otro bypass innecesario."""

from __future__ import annotations

import frappe


def korvexcio_ecf_for_invoice(sales_invoice_name: str):
    """El ECF (S2.4) vinculado a esta Sales Invoice, o None si todavia
    no se ha creado (antes de submit) o el usuario no tiene acceso."""
    ecf_name = frappe.get_all(
        "ECF",
        filters={"reference_doctype": "Sales Invoice", "reference_name": sales_invoice_name},
        pluck="name",
        limit=1,
    )
    if not ecf_name:
        return None
    return frappe.get_doc("ECF", ecf_name[0])


def korvexcio_qr_data_uri(url: str) -> str:
    from korvexcio.ecf.qr import qr_svg_data_uri

    return qr_svg_data_uri(url)
