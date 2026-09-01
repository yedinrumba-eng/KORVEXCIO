"""Unit tests for dashboard authorization boundary."""

from unittest.mock import patch

import pytest

from korvexcio.retail.dashboard import get_dashboard_data


def test_dashboard_rejects_non_owner():
    with patch("korvexcio.retail.dashboard.frappe.has_role", return_value=False), pytest.raises(Exception):
        get_dashboard_data()
