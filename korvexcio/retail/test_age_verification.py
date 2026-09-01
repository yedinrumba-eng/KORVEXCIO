"""Unit tests for age rules and encrypted identity values."""

from datetime import date
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import frappe
from cryptography.exceptions import InvalidTag

from korvexcio.retail.age_verification import (
    decrypt_pii,
    encrypt_pii,
    mask_identity,
    validate_invoice_age,
    verify_age,
)


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
