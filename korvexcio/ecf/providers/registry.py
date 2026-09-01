"""Registro de implementaciones reales de FiscalProvider, por nombre de
proveedor -- el mismo valor que usa el Select `provider` de DGII Settings
(S2.1: "Alanube", "ECF SSD").

Vacio a proposito hasta que S2.7 desbloquee (D20: sin RNC, sin
certificado, sin correspondencia de proveedor todavia). resolve_provider()
devuelve None cuando el proveedor elegido no tiene implementacion --
nunca un provider falso ni un stub que finja funcionar."""

from __future__ import annotations

from korvexcio.ecf.providers.base import FiscalProvider

_REGISTRY: dict[str, type[FiscalProvider]] = {}


def resolve_provider(provider_name: str | None) -> FiscalProvider | None:
    if not provider_name:
        return None
    provider_class = _REGISTRY.get(provider_name)
    if provider_class is None:
        return None
    return provider_class()
