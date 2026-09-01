"""POS Profile per Company (S4.1, D16 -- POSNext ganó S0.8 con evidencia
real, ver docs/10-SPIKE-POS.md). Ambos frontends candidatos (nativo y
POSNext) usan el mismo DocType core `POS Profile` de ERPNext, asi que
esta estructura no depende de cual quede instalado al final -- ese es
trabajo de forkear POSNext, todavia sin hacer.

El cajero cae en el POS Profile de su Company sin escoger nada: la
propia funcion de ERPNext (erpnext.stock.get_item_details.get_pos_profile)
busca PRIMERO en la tabla hija `applicable_for_users` (POS Profile User)
un match user+default=1, filtrado por company -- eso es lo que
_sync_cajero_assignments() puebla."""

from __future__ import annotations

from typing import Any

import frappe
from korvexcio.retail.site_config import get_retail_config, is_vertical_enabled


def sync_pos_profiles() -> list[str]:
    """Create/update one POS Profile per configured entry; do nothing
    when retail is disabled (regla 2 -- apagado por default)."""
    if not is_vertical_enabled():
        return []
    return [_sync_pos_profile(config) for config in get_retail_config().get("pos_profiles", [])]


def _sync_pos_profile(config: dict[str, Any]) -> str:
    company = config["company"]
    name = config.get("name") or f"POS {company}"
    company_doc = frappe.get_cached_doc("Company", company)

    if frappe.db.exists("POS Profile", name):
        profile = frappe.get_doc("POS Profile", name)
    else:
        profile = frappe.new_doc("POS Profile")
        profile.name = name
        profile.company = company
        profile.warehouse = config["warehouse"]
        profile.currency = company_doc.default_currency
        profile.write_off_account = company_doc.write_off_account
        profile.write_off_cost_center = company_doc.cost_center
        profile.write_off_limit = 0
        for payment in config.get("payments") or [{"mode_of_payment": "Cash", "default": 1}]:
            profile.append("payments", payment)
        profile.insert()

    _sync_cajero_assignments(profile, config.get("cajero_users", []))
    return profile.name


def _sync_cajero_assignments(profile, cajero_users: list[str]) -> None:
    existing = {row.user for row in profile.applicable_for_users}
    changed = False
    for user in cajero_users:
        if user not in existing:
            profile.append("applicable_for_users", {"user": user, "default": 1})
            changed = True
    if changed:
        profile.save()
