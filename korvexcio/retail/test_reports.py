"""Unit tests for explicit Company scoping in Retail reports."""

import pytest

from korvexcio.retail.reports import company_filter


def test_company_filter_requires_explicit_company():
    with pytest.raises(Exception):
        company_filter({})


def test_company_filter_rejects_blank_company():
    with pytest.raises(Exception):
        company_filter({"company": "  "})
