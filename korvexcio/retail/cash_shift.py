"""Cash shift / POS Closing Entry reconciliation (S4.5).

Wraps ERPNext's own POS Opening Entry / POS Closing Entry -- the
per-mode reconciliation math (`payment_reconciliation`) comes from
`erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry.
make_closing_entry_from_opening()`, which sums real submitted
invoices for the period. Nothing here reimplements that query; this
module only fills in what ERPNext's own function leaves at zero
(`opening_amount`) and what only the cashier knows (`closing_amount`,
what they actually counted), then computes `difference` explicitly so
"que cuadre" doesn't depend on a client script that no frontend here
runs yet.

Permission is enforced the normal way: `frappe.new_doc(...).insert()`
checks "create" on the doctype for the calling user, same as any other
document -- no `ignore_permissions=True` anywhere in this module.
"""

from __future__ import annotations

import frappe
from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import (
    make_closing_entry_from_opening,
)


@frappe.whitelist()
def open_shift(pos_profile: str, opening_balances: dict[str, float]) -> str:
    """Opens a cash shift for the current user against `pos_profile`.
    `opening_balances`: {mode_of_payment: opening_amount}. Returns the
    submitted POS Opening Entry name."""
    profile = frappe.get_doc("POS Profile", pos_profile)
    if not profile.has_permission("read"):
        # frappe.get_doc() doesn't check read permission (the S1.8
        # lesson) -- without this, a caller could name a POS Profile
        # from another Company and have its `company` used below before
        # Frappe's own create-time isolation check gets a chance to run.
        frappe.throw(frappe._("No tienes permiso para leer este POS Profile."), frappe.PermissionError)
    entry = frappe.new_doc("POS Opening Entry")
    entry.pos_profile = pos_profile
    entry.company = profile.company
    entry.user = frappe.session.user
    entry.period_start_date = frappe.utils.now_datetime()
    for mode, amount in opening_balances.items():
        entry.append("balance_details", {"mode_of_payment": mode, "opening_amount": amount})
    entry.insert()
    entry.submit()
    return entry.name


@frappe.whitelist()
def close_shift(pos_opening_entry: str, counted_amounts: dict[str, float]) -> str:
    """Closes the shift opened as `pos_opening_entry`. `counted_amounts`:
    {mode_of_payment: amount actually counted in the drawer/terminal at
    close}. Returns the submitted POS Closing Entry name; each row of
    `payment_reconciliation` carries the real `difference` (counted
    minus expected, expected including the opening float for that
    mode)."""
    opening = frappe.get_doc("POS Opening Entry", pos_opening_entry)
    if not opening.has_permission("read"):
        # Same S1.8 gap as above: get_doc() ignores read permission, and
        # make_closing_entry_from_opening() below would otherwise query
        # another Company's real sales invoices into memory before any
        # permission check ran.
        frappe.throw(
            frappe._("No tienes permiso para leer este turno."), frappe.PermissionError
        )
    closing = make_closing_entry_from_opening(opening)

    opening_by_mode = {row.mode_of_payment: row.opening_amount for row in opening.balance_details}

    for row in closing.payment_reconciliation:
        opening_amount = opening_by_mode.get(row.mode_of_payment, 0)
        row.opening_amount = opening_amount
        row.expected_amount = row.expected_amount + opening_amount
        row.closing_amount = counted_amounts.get(row.mode_of_payment, 0)
        row.difference = row.closing_amount - row.expected_amount

    closing.insert()
    closing.submit()
    return closing.name
