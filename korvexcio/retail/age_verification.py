"""Server-side age verification with encrypted optional PII storage."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import pickle
import secrets
from datetime import date, datetime
from zoneinfo import ZoneInfo

import frappe
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MINIMUM_AGE = 18
_RD_TZ = ZoneInfo("America/Santo_Domingo")


def requires_age_verification(item_group: str) -> bool:
    """Read the server-side Item Group flag; never trust POS input for this."""
    return bool(frappe.db.get_value("Item Group", item_group, "requiere_verificacion_edad"))


@frappe.whitelist()
def issue_age_token(item_codes: list[str], birth_date: str) -> str:
    """Issue a short-lived token bound to the current user and regulated Items."""
    if not isinstance(item_codes, list) or not item_codes:
        frappe.throw("At least one Item is required for age verification")
    try:
        parsed_date = date.fromisoformat(birth_date)
    except (TypeError, ValueError):
        # Security-review finding (2026-09-01): an unhandled ValueError here
        # echoes the raw birth_date string -- PII -- into the exception
        # message, which Frappe's Error Log stores unmasked. Never let the
        # raw input reach a log; always throw a generic message instead.
        frappe.throw("Fecha de nacimiento invalida")
    if not verify_age(parsed_date):
        frappe.throw("La persona no cumple la edad minima")
    regulated_codes = []
    for item_code in sorted(set(item_codes)):
        item_group = frappe.db.get_value("Item", item_code, "item_group")
        if item_group and requires_age_verification(item_group):
            regulated_codes.append(item_code)
    if not regulated_codes:
        frappe.throw("No regulated Item was found")
    token = secrets.token_urlsafe(32)
    frappe.cache().set_value(
        _token_key(token),
        {"user": frappe.session.user, "items": _items_digest(regulated_codes)},
        expires_in_sec=900,
    )
    return token


def _regulated_item_codes(invoice) -> list[str]:
    regulated_codes = []
    for row in invoice.items:
        item_group = frappe.db.get_value("Item", row.item_code, "item_group")
        if item_group and requires_age_verification(item_group):
            regulated_codes.append(row.item_code)
    return regulated_codes


def validate_invoice_age(invoice) -> None:
    """Early, non-destructive check for fast feedback on save -- NOT the
    security boundary. Two documents can share a copied token value and
    both pass this peek; claim_invoice_age_token() (before_submit) is what
    actually enforces one-time use."""
    regulated_codes = _regulated_item_codes(invoice)
    if not regulated_codes:
        return
    token = getattr(invoice, "age_verification_token", "")
    payload = frappe.cache().get_value(_token_key(token)) if token else None
    if not isinstance(payload, dict) or payload.get("user") != frappe.session.user:
        frappe.throw("Verificacion de edad requerida antes de vender este Item")
    if payload.get("items") != _items_digest(regulated_codes):
        frappe.throw("La verificacion de edad no corresponde a los Items de la venta")


def claim_invoice_age_token(invoice) -> None:
    """Atomically check-and-consume the token at the moment the sale
    actually becomes final. Security-review finding (2026-09-01): the
    previous design split the check (validate) from the consume
    (before_submit) as two separate steps -- a duplicated draft carrying
    the same token value could pass the check on both copies before
    either one deleted it. Redis GETDEL makes this one atomic server-side
    operation: whichever submit reaches it first wins the token; every
    other document with the same value finds nothing left, same pattern
    as tasks.py::_claim_ecf (S2.10)."""
    regulated_codes = _regulated_item_codes(invoice)
    if not regulated_codes:
        return
    token = getattr(invoice, "age_verification_token", "")
    payload = _claim_token(token)
    if not isinstance(payload, dict) or payload.get("user") != frappe.session.user:
        frappe.throw("Verificacion de edad requerida antes de vender este Item")
    if payload.get("items") != _items_digest(regulated_codes):
        frappe.throw("La verificacion de edad no corresponde a los Items de la venta")


def _claim_token(token: str) -> dict | None:
    if not token:
        return None
    cache = frappe.cache()
    raw = cache.getdel(cache.make_key(_token_key(token)))
    if raw is None:
        return None
    return pickle.loads(raw)


def verify_age(birth_date: date, today: date | None = None, minimum_age: int = MINIMUM_AGE) -> bool:
    """Return whether a birth date meets the configured minimum age."""
    current = today or datetime.now(tz=_RD_TZ).date()
    age = current.year - birth_date.year - ((current.month, current.day) < (birth_date.month, birth_date.day))
    return age >= minimum_age


def encrypt_pii(value: str, record_id: str) -> str:
    """Encrypt one value with a unique IV and authenticated record context."""
    key = _encryption_key()
    iv = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(iv, value.encode("utf-8"), record_id.encode("utf-8"))
    return base64.urlsafe_b64encode(iv + ciphertext).decode("ascii")


def decrypt_pii(token: str, record_id: str) -> str:
    """Decrypt a value only with the same record context."""
    raw = base64.urlsafe_b64decode(token.encode("ascii"))
    if len(raw) <= 12:
        raise ValueError("Invalid encrypted PII")
    return AESGCM(_encryption_key()).decrypt(raw[:12], raw[12:], record_id.encode("utf-8")).decode("utf-8")


def mask_identity(value: str) -> str:
    """Return a stable log-safe mask without exposing identity digits."""
    digits = "".join(character for character in value if character.isdigit())
    return f"***-**{digits[-2:]}" if len(digits) >= 2 else "***-**"


def _encryption_key() -> bytes:
    encoded = os.environ.get("MASTER_ENCRYPTION_KEY", "")
    try:
        key = bytes.fromhex(encoded)
    except ValueError as exc:
        raise ValueError("MASTER_ENCRYPTION_KEY must be 64 hexadecimal characters") from exc
    if len(key) != 32:
        raise ValueError("MASTER_ENCRYPTION_KEY must be 64 hexadecimal characters")
    return key


def _items_digest(item_codes: list[str]) -> str:
    return hashlib.sha256(json.dumps(sorted(set(item_codes))).encode("utf-8")).hexdigest()


def _token_key(token: str) -> str:
    if not isinstance(token, str) or not token:
        return "korvexcio:age-token:invalid"
    return f"korvexcio:age-token:{token}"
