"""Registro de implementaciones reales de FiscalProvider, por nombre de
proveedor -- el mismo valor que usa el Select `provider` de DGII Settings
(S2.1: "Alanube", "ECF SSD").

Vacio a proposito hasta que S2.7 desbloquee (D20: sin RNC, sin
certificado, sin correspondencia de proveedor todavia). resolve_provider()
devuelve None cuando el proveedor elegido no tiene implementacion --
nunca un provider falso ni un stub que finja funcionar."""

from __future__ import annotations

import frappe
from korvexcio.ecf.providers.base import FiscalProvider

_REGISTRY: dict[str, type[FiscalProvider]] = {}


def resolve_provider(provider_name: str | None) -> FiscalProvider | None:
    if not provider_name:
        return None
    provider_class = _REGISTRY.get(provider_name)
    if provider_class is None:
        # SEC-L07: Log error si proveedor configurado no tiene implementación
        # Evita que ECF se quede "Pendiente" silenciosamente sin razón visible
        frappe.log_error(
            title=f"FiscalProvider '{provider_name}' no registrado en registry",
            message=f"DGII Settings tiene provider='{provider_name}' pero no hay implementación en korvexcio.ecf.providers.registry._REGISTRY. "
                    f"Providers disponibles: {list(_REGISTRY.keys()) or 'ninguno'}. "
                    f"Verificar S2.7 (proveedor real) o configuración en DGII Settings."
        )
        return None
    return provider_class()
