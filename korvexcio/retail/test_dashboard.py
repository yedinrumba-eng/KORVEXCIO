"""Unit tests for dashboard authorization boundary."""

from unittest import TestCase
from unittest.mock import patch

import frappe

from korvexcio.retail.dashboard import get_dashboard_data


class TestRetailDashboard(TestCase):
    def test_dashboard_rejects_non_owner(self):
        with (
            patch("korvexcio.retail.dashboard.frappe.get_roles", return_value=[]),
            self.assertRaises(frappe.PermissionError),
        ):
            get_dashboard_data()
