"""Unit tests for explicit Company scoping in Retail reports."""

from unittest import TestCase

from korvexcio.retail.reports import company_filter


class TestRetailReports(TestCase):
    def test_company_filter_requires_explicit_company(self):
        with self.assertRaises(Exception):
            company_filter({})

    def test_company_filter_rejects_blank_company(self):
        with self.assertRaises(Exception):
            company_filter({"company": "  "})
