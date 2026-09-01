"""Integration tests for opt-in retail attributes and Item variants."""

import frappe
from frappe.tests import IntegrationTestCase


class TestRetailItemAttributes(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests

        before_tests()

    def tearDown(self):
        for name in ("Test Retail Vape Template", "Test Retail Vape Red 20"):
            if frappe.db.exists("Item", name):
                frappe.delete_doc("Item", name, force=True)
        for name in ("Test Sabor", "Test Nicotina"):
            if frappe.db.exists("Item Attribute", name):
                frappe.delete_doc("Item Attribute", name, force=True)
        frappe.db.commit()

    def test_disabled_site_does_not_create_attributes(self):
        from korvexcio.retail import item_attributes

        original = frappe.conf.get("korvexcio_retail")
        frappe.conf.korvexcio_retail = {"enabled": False, "attributes": []}
        try:
            self.assertEqual(item_attributes.sync_item_attributes(), [])
            self.assertFalse(frappe.db.exists("Item Attribute", "Test Sabor"))
        finally:
            frappe.conf.korvexcio_retail = original

    def test_enabled_configuration_is_idempotent(self):
        from korvexcio.retail import item_attributes

        original = frappe.conf.get("korvexcio_retail")
        frappe.conf.korvexcio_retail = {
            "enabled": True,
            "attributes": [
                {"name": "Test Sabor", "values": ["Red", "Mint"]},
                {"name": "Test Nicotina", "numeric": True, "values": ["20"]},
            ],
        }
        try:
            self.assertEqual(item_attributes.sync_item_attributes(), ["Test Sabor", "Test Nicotina"])
            item_attributes.sync_item_attributes()
            sabor = frappe.get_doc("Item Attribute", "Test Sabor")
            self.assertEqual([row.attribute_value for row in sabor.item_attribute_values], ["Red", "Mint"])
            self.assertEqual(frappe.get_doc("Item Attribute", "Test Nicotina").numeric_values, 1)
        finally:
            frappe.conf.korvexcio_retail = original

    def test_template_generates_variant_with_configured_attributes(self):
        from korvexcio.retail import item_attributes

        original = frappe.conf.get("korvexcio_retail")
        frappe.conf.korvexcio_retail = {
            "enabled": True,
            "attributes": [
                {"name": "Test Sabor", "values": ["Red"]},
                {"name": "Test Nicotina", "values": ["20"]},
            ],
        }
        try:
            item_attributes.sync_item_attributes()
            names = item_attributes.create_item_template_and_variants(
                {
                    "item_code": "Test Retail Vape Template",
                    "item_name": "Test Retail Vape Template",
                    "item_group": "Products",
                    "stock_uom": "Nos",
                },
                [{"Test Sabor": "Red", "Test Nicotina": "20"}],
            )
            self.assertEqual(names, ["Test Retail Vape Template-Red-20"])
            variant = frappe.get_doc("Item", names[0])
            self.assertEqual(variant.variant_of, "Test Retail Vape Template")
            self.assertEqual(
                {row.attribute: row.attribute_value for row in variant.attributes},
                {"Test Sabor": "Red", "Test Nicotina": "20"},
            )
        finally:
            frappe.conf.korvexcio_retail = original
