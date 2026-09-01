"""Unit tests for FEFO ordering and expiry alerts."""

from datetime import date, timedelta

from korvexcio.retail.fefo import BatchStock, expiry_alerts, select_batches


def test_select_batches_uses_first_expiring_batch():
    today = date(2026, 9, 1)
    batches = [
        BatchStock("B-LATE", today + timedelta(days=30), 3),
        BatchStock("B-EARLY", today + timedelta(days=5), 3),
    ]
    assert [batch.name for batch in select_batches(batches, today)] == ["B-EARLY", "B-LATE"]


def test_select_batches_ignores_empty_and_expired_batches():
    today = date(2026, 9, 1)
    batches = [
        BatchStock("B-EMPTY", today + timedelta(days=1), 0),
        BatchStock("B-EXPIRED", today - timedelta(days=1), 4),
        BatchStock("B-VALID", today + timedelta(days=1), 4),
    ]
    assert [batch.name for batch in select_batches(batches, today)] == ["B-VALID"]


def test_expiry_alerts_group_by_90_60_30_day_threshold():
    today = date(2026, 9, 1)
    batches = [
        BatchStock("B-90", today + timedelta(days=80), 1),
        BatchStock("B-60", today + timedelta(days=55), 1),
        BatchStock("B-30", today + timedelta(days=20), 1),
    ]
    assert expiry_alerts(batches, today) == {90: ["B-90"], 60: ["B-60"], 30: ["B-30"]}
