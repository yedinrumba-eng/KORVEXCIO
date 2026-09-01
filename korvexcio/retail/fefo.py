"""FEFO batch selection and configurable expiry alerts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

_RD_TZ = ZoneInfo("America/Santo_Domingo")


@dataclass(frozen=True)
class BatchStock:
    name: str
    expiry_date: date | None
    actual_qty: float


def select_batches(batches: Iterable[BatchStock], today: date | None = None) -> list[BatchStock]:
    """Return usable batches in first-expiring-first-out order."""
    current = today or datetime.now(tz=_RD_TZ).date()
    return sorted(
        (batch for batch in batches if batch.actual_qty > 0 and (batch.expiry_date is None or batch.expiry_date >= current)),
        key=lambda batch: (batch.expiry_date is None, batch.expiry_date or date.max, batch.name),
    )


def expiry_alerts(
    batches: Iterable[BatchStock], today: date, thresholds: tuple[int, ...] = (90, 60, 30)
) -> dict[int, list[str]]:
    """Group usable batches by the nearest configured expiry threshold."""
    alerts = {threshold: [] for threshold in thresholds}
    for batch in batches:
        if batch.actual_qty <= 0 or batch.expiry_date is None:
            continue
        days_left = (batch.expiry_date - today).days
        for threshold in sorted(thresholds):
            if 0 <= days_left <= threshold:
                alerts[threshold].append(batch.name)
                break
    return alerts
