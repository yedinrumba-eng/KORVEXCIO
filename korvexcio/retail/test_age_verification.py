"""Unit tests for age rules and encrypted identity values."""

import hashlib
import json
import pickle
from datetime import date
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import frappe
from cryptography.exceptions import InvalidTag

from korvexcio.retail.age_verification import (
    claim_invoice_age_token,
    decrypt_pii,
    encrypt_pii,
    mask_identity,
    validate_invoice_age,
    verify_age,
)


class _FakeAtomicCache:
    """Simulates real Redis GETDEL semantics (atomic pop) without a live
    site connection -- returns the pickled value once, None every call
    after, exactly like the actual RedisWrapper used in production."""

    def __init__(self):
        self._store: dict[bytes, bytes] = {}

    def make_key(self, key):
        return key.encode()

    def set_value(self, key, value, expires_in_sec=None):
        self._store[key.encode()] = pickle.dumps(value)

    def get_value(self, key):
        raw = self._store.get(key.encode())
        return pickle.loads(raw) if raw is not None else None

    def getdel(self, full_key):
        return self._store.pop(full_key, None)


class TestAgeVerification(TestCase):
    def test_adult_is_accepted_and_underage_is_rejected(self):
        today = date(2026, 9, 1)
        assert verify_age(date(2000, 9, 1), today)
        assert not verify_age(date(2008, 9, 2), today)

    def test_same_pii_gets_unique_iv_and_round_trips(self):
        import os

        original = os.environ.get("MASTER_ENCRYPTION_KEY")
        os.environ["MASTER_ENCRYPTION_KEY"] = "11" * 32
        try:
            first = encrypt_pii("001-1234567-8", "record-a")
            second = encrypt_pii("001-1234567-8", "record-a")
            self.assertNotEqual(first, second)
            self.assertEqual(decrypt_pii(first, "record-a"), "001-1234567-8")
            with self.assertRaises(InvalidTag):
                decrypt_pii(first, "record-b")
        finally:
            if original is None:
                os.environ.pop("MASTER_ENCRYPTION_KEY", None)
            else:
                os.environ["MASTER_ENCRYPTION_KEY"] = original

    def test_identity_log_mask_has_only_last_two_digits(self):
        self.assertEqual(mask_identity("001-1234567-89"), "***-**89")

    @patch("korvexcio.retail.age_verification.frappe.db.get_value")
    def test_regulated_invoice_without_token_is_rejected(self, get_value):
        get_value.side_effect = ["Regulated", 1]
        invoice = SimpleNamespace(items=[SimpleNamespace(item_code="VAPE-001")])
        with self.assertRaises(frappe.exceptions.ValidationError):
            validate_invoice_age(invoice)

    @patch("korvexcio.retail.age_verification.frappe.db.get_value")
    def test_unregulated_invoice_without_token_is_allowed(self, get_value):
        # Bug real encontrado corriendo esto en Frappe de verdad, no en
        # revision: return_value="Coffee" contesta IGUAL a las dos
        # llamadas de get_value dentro de validate_invoice_age (la de
        # item_group y la de requiere_verificacion_edad), y bool("Coffee")
        # es True -- el mock nunca simulaba "no regulado" de verdad, asi
        # que el item de cafe se trataba como regulado y el test tronaba.
        # side_effect ordena las dos respuestas por separado, como ya
        # hacia el test hermano de arriba.
        get_value.side_effect = ["Coffee", 0]
        invoice = SimpleNamespace(items=[SimpleNamespace(item_code="COFFEE-001")])
        validate_invoice_age(invoice)


class TestClaimInvoiceAgeToken(TestCase):
    """Security-review finding (2026-09-01): the token check and consume
    used to be two separate steps (validate() peek + a later before_submit
    delete) -- a duplicated draft carrying the same token value could pass
    the check on both copies before either one deleted it. These tests
    prove the atomic GETDEL-based claim actually closes that window."""

    def setUp(self):
        self.cache = _FakeAtomicCache()
        self.patcher = patch("korvexcio.retail.age_verification.frappe.cache", return_value=self.cache)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    @patch("korvexcio.retail.age_verification.frappe.db.get_value")
    @patch("korvexcio.retail.age_verification.frappe.session")
    def test_second_claim_of_the_same_token_is_rejected(self, session, get_value):
        session.user = "cajero@vlj.example"
        get_value.side_effect = ["Regulated", 1, "Regulated", 1]
        self.cache.set_value(
            "korvexcio:age-token:tok-1",
            {"user": "cajero@vlj.example", "items": _digest(["VAPE-001"])},
        )
        first_invoice = SimpleNamespace(
            items=[SimpleNamespace(item_code="VAPE-001")], age_verification_token="tok-1"
        )
        second_invoice = SimpleNamespace(
            items=[SimpleNamespace(item_code="VAPE-001")], age_verification_token="tok-1"
        )

        # Same token value copied onto two documents (e.g. Frappe's
        # "Duplicate" action, which copies hidden/read-only fields too) --
        # only the FIRST claim may succeed.
        claim_invoice_age_token(first_invoice)
        with self.assertRaises(frappe.exceptions.ValidationError):
            claim_invoice_age_token(second_invoice)

    @patch("korvexcio.retail.age_verification.frappe.db.get_value")
    @patch("korvexcio.retail.age_verification.frappe.session")
    def test_claim_rejects_wrong_user(self, session, get_value):
        session.user = "attacker@example.com"
        get_value.side_effect = ["Regulated", 1]
        self.cache.set_value(
            "korvexcio:age-token:tok-2", {"user": "cajero@vlj.example", "items": _digest(["VAPE-001"])}
        )
        invoice = SimpleNamespace(items=[SimpleNamespace(item_code="VAPE-001")], age_verification_token="tok-2")
        with self.assertRaises(frappe.exceptions.ValidationError):
            claim_invoice_age_token(invoice)


def _digest(item_codes):
    return hashlib.sha256(json.dumps(sorted(set(item_codes))).encode("utf-8")).hexdigest()
