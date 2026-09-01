"""Unit tests for age rules and encrypted identity values."""

from datetime import date
from unittest import TestCase

from korvexcio.retail.age_verification import decrypt_pii, encrypt_pii, mask_identity, verify_age


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
            with self.assertRaises(Exception):
                decrypt_pii(first, "record-b")
        finally:
            if original is None:
                os.environ.pop("MASTER_ENCRYPTION_KEY", None)
            else:
                os.environ["MASTER_ENCRYPTION_KEY"] = original

    def test_identity_log_mask_has_only_last_two_digits(self):
        self.assertEqual(mask_identity("001-1234567-89"), "***-**89")
