"""Validated access to site-local retail configuration."""

from __future__ import annotations

from typing import Any

import frappe


def get_retail_config() -> dict[str, Any]:
    """Return the opt-in retail configuration from the current site."""
    configured = frappe.conf.get("korvexcio_retail", {})
    if not isinstance(configured, dict):
        frappe.throw("korvexcio_retail must be an object in site_config.json")
    return configured


def is_vertical_enabled() -> bool:
    """Return whether this site opted into the retail vertical."""
    return get_retail_config().get("enabled") is True
