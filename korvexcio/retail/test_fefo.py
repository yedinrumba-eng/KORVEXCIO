"""Unit tests for FEFO ordering and expiry alerts."""

from datetime import date, timedelta

import frappe
from frappe.tests import IntegrationTestCase

from korvexcio.retail.fefo import BatchStock, expiry_alerts, select_batches


class TestFefo(IntegrationTestCase):
    def setUp(self):
        """Setup aislado por test - crea datos únicos con generate_hash."""
        frappe.set_user("Administrator")
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests
        before_tests()

        # Generar sufijo único para este test
        self.test_hash = frappe.generate_hash(8)

    def tearDown(self):
        """Limpieza completa por test - elimina datos creados."""
        frappe.set_user("Administrator")
        super().tearDown()

    def test_select_batches_uses_first_expiring_batch(self):
        today = date(2026, 9, 1)
        batches = [
            BatchStock("B-LATE", today + timedelta(days=30), 3),
            BatchStock("B-EARLY", today + timedelta(days=5), 3),
        ]
        assert [batch.name for batch in select_batches(batches, today)] == ["B-EARLY", "B-LATE"]

    def test_select_batches_ignores_empty_and_expired_batches(self):
        today = date(2026, 9, 1)
        batches = [
            BatchStock("B-EMPTY", today + timedelta(days=1), 0),
            BatchStock("B-EXPIRED", today - timedelta(days=1), 4),
            BatchStock("B-VALID", today + timedelta(days=1), 4),
        ]
        assert [batch.name for batch in select_batches(batches, today)] == ["B-VALID"]

    def test_expiry_alerts_group_by_90_60_30_day_threshold(self):
        today = date(2026, 9, 1)
        batches = [
            BatchStock("B-90", today + timedelta(days=80), 1),
            BatchStock("B-60", today + timedelta(days=55), 1),
            BatchStock("B-30", today + timedelta(days=20), 1),
        ]
        assert expiry_alerts(batches, today) == {90: ["B-90"], 60: ["B-60"], 30: ["B-30"]}
