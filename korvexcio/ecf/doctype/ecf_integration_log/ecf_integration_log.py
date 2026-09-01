"""Controller for ECF Integration Log - patron KSA/India: registra cada
llamada a un proveedor de e-CF, con los secretos SIEMPRE enmascarados
antes de guardar, sin importar lo que el caller haya pasado.

mask_sensitive_info() es publica a proposito: S2.6/S2.7 (providers/) la
van a reusar para construir el log de cada llamada real.
"""

import re

from frappe.model.document import Document

MASK = "***MASKED***"

# Claves sensibles en JSON: "password": "...", "token": "...", etc.
_SENSITIVE_KEYS = [
    "password",
    "token",
    "secret",
    "api_key",
    "apikey",
    "access_token",
    "refresh_token",
    "client_secret",
    "private_key",
    "authorization",
]

_JSON_KEY_PATTERN = re.compile(
    r'"(' + "|".join(_SENSITIVE_KEYS) + r')"\s*:\s*"([^"]*)"',
    re.IGNORECASE,
)

# Headers estilo "Authorization: Bearer xxxxx" o "X-Api-Key: xxxxx" --
# [^\n]+ (no \S+) porque "Bearer xxxxx" son DOS palabras: \S+ solo se
# comia "Bearer" y dejaba el token real sin enmascarar.
_HEADER_PATTERN = re.compile(
    r"(?i)((?:authorization|x-api-key|x-auth-token)\s*:\s*)([^\n]+)"
)


def mask_sensitive_info(text: str | None) -> str | None:
    """Enmascara valores de claves sensibles en un texto JSON o de
    headers HTTP. No falla si el texto no es JSON valido -- es una
    pasada de regex, no un parser."""
    if not text:
        return text

    masked = _JSON_KEY_PATTERN.sub(lambda m: f'"{m.group(1)}": "{MASK}"', text)
    masked = _HEADER_PATTERN.sub(lambda m: f"{m.group(1)}{MASK}", masked)
    return masked


class ECFIntegrationLog(Document):
    def validate(self) -> None:
        self.request_payload = mask_sensitive_info(self.request_payload)
        self.response_payload = mask_sensitive_info(self.response_payload)
        self.error_message = mask_sensitive_info(self.error_message)
