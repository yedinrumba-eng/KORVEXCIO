"""Unit tests for age rules and encrypted identity values."""

from datetime import date

import pytest

from korvexcio.retail.age_verification import decrypt_pii, encrypt_pii, mask_identity, verify_age


def test_adult_is_accepted_and_underage_is_rejected():
    today = date(2026, 9, 1)
    assert verify_age(date(2000, 9, 1), today)
    assert not verify_age(date(2008, 9, 2), today)


def test_same_pii_gets_unique_iv_and_round_trips(monkeypatch):
    monkeypatch.setenv("MASTER_ENCRYPTION_KEY", "11" * 32)
    first = encrypt_pii("001-1234567-8", "record-a")
    second = encrypt_pii("001-1234567-8", "record-a")
    assert first != second
    assert decrypt_pii(first, "record-a") == "001-1234567-8"
    with pytest.raises(Exception):
        decrypt_pii(first, "record-b")


def test_identity_log_mask_has_only_last_two_digits():
    assert mask_identity("001-1234567-89") == "***-**89"
