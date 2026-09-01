"""Unit tests for opt-in cafe configuration boundaries."""

from unittest.mock import patch

from korvexcio.retail.cafe import sync_cafe_catalog


def test_cafe_catalog_is_off_by_default():
    with patch("korvexcio.retail.cafe.get_retail_config", return_value={"enabled": False}), patch(
        "korvexcio.retail.cafe.is_vertical_enabled", return_value=False
    ):
        assert sync_cafe_catalog() == []
