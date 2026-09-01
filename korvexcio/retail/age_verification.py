"""Server-side age verification with encrypted optional PII storage."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import secrets
from datetime import date

import frappe
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MINIMUM_AGE = 18
MASKED_ID = re.compile(r"^\*\*\*-\*\*(?P<tail>\d{2})$")


def requires_age_verification(item_group: str) -> bool:
    """Read the server-side Item Group flag; never trust POS input for this."""
    return bool(frappe.db.get_value("Item Group", item_group, "requiere_verificacion_edad"))


@frappe.whitelist()
def issue_age_token(item_codes: list[str], birth_date: str) -> str:
    """Issue a short-lived token bound to the current user and regulated Items."""
    if not isinstance(item_codes, list) or not item_codes:
        frappe.throw("At least one Item is required for age verification")
    parsed_date = date.fromisoformat(birth_date)
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


def validate_invoice_age(invoice) -> None:
    """Reject regulated sales without a server-issued token for these Items."""
    regulated_codes = []
    for row in invoice.items:
        item_group = frappe.db.get_value("Item", row.item_code, "item_group")
        if item_group and requires_age_verification(item_group):
            regulated_codes.append(row.item_code)
    if not regulated_codes:
        return
    token = getattr(invoice, "age_verification_token", "")
    payload = frappe.cache().get_value(_token_key(token)) if token else None
    if not isinstance(payload, dict) or payload.get("user") != frappe.session.user:
        frappe.throw("Verificacion de edad requerida antes de vender este Item")
    if payload.get("items") != _items_digest(regulated_codes):
        frappe.throw("La verificacion de edad no corresponde a los Items de la venta")


def consume_invoice_age_token(invoice) -> None:
    """Consume a verified token when a regulated invoice is submitted."""
    if getattr(invoice, "age_verification_token", ""):
        frappe.cache().delete_value(_token_key(invoice.age_verification_token))


def verify_age(birth_date: date, today: date | None = None, minimum_age: int = MINIMUM_AGE) -> bool:
    """Return whether a birth date meets the configured minimum age."""
    current = today or date.today()
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
