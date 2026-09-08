"""Integration tests for opt-in retail attributes and Item variants."""

import frappe
from frappe.tests import IntegrationTestCase


class TestRetailItemAttributes(IntegrationTestCase):
    def setUp(self):
        """Setup aislado por test - crea datos únicos con generate_hash."""
        frappe.set_user("Administrator")
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests
        before_tests()

        # Generar sufijo único para este test
        self.test_hash = frappe.generate_hash(8)

        # Definir nombres únicos para este test
        self.template_name = f"Test Retail Vape Template {self.test_hash}"
        self.variant_name = f"Test Retail Vape Template Red 20 {self.test_hash}"
        self.sabor_name = f"Test Sabor {self.test_hash}"
        self.nicotina_name = f"Test Nicotina {self.test_hash}"

    def tearDown(self):
        """Limpieza completa por test - elimina datos creados."""
        frappe.set_user("Administrator")
        # Limpiar en orden inverso de dependencias
        try:
            # Items (variants first, then templates)
            for item_name in frappe.get_all("Item", pluck="name"):
                if item_name.startswith("Test Retail Vape Template"):
                    frappe.delete_doc("Item", item_name, force=True)

            # Item Attributes
            for attr_name in frappe.get_all("Item Attribute", pluck="name"):
                if attr_name.startswith("Test Sabor") or attr_name.startswith("Test Nicotina"):
                    frappe.delete_doc("Item Attribute", attr_name, force=True)

        except (frappe.DoesNotExistError, frappe.ValidationError):
            pass

        super().tearDown()

    def test_disabled_site_does_not_create_attributes(self):
        from korvexcio.retail import item_attributes

        original = frappe.conf.get("korvexcio_retail")
        frappe.conf.korvexcio_retail = {"enabled": False, "attributes": []}
        try:
            self.assertEqual(item_attributes.sync_item_attributes(), [])
            self.assertFalse(frappe.db.exists("Item Attribute", self.sabor_name))
        finally:
            frappe.conf.korvexcio_retail = original

    def test_enabled_configuration_is_idempotent(self):
        from korvexcio.retail import item_attributes

        original = frappe.conf.get("korvexcio_retail")
        frappe.conf.korvexcio_retail = {
            "enabled": True,
            "attributes": [
                {"name": self.sabor_name, "values": ["Red", "Mint"]},
                {"name": self.nicotina_name, "values": ["20"]},
            ],
        }
        try:
            self.assertEqual(item_attributes.sync_item_attributes(), [self.sabor_name, self.nicotina_name])
            item_attributes.sync_item_attributes()
            sabor = frappe.get_doc("Item Attribute", self.sabor_name)
            self.assertEqual([row.attribute_value for row in sabor.item_attribute_values], ["Red", "Mint"])
            nicotina = frappe.get_doc("Item Attribute", self.nicotina_name)
            self.assertEqual([row.attribute_value for row in nicotina.item_attribute_values], ["20"])
        finally:
            frappe.conf.korvexcio_retail = original

    def test_template_generates_variant_with_configured_attributes(self):
        from korvexcio.retail import item_attributes

        original = frappe.conf.get("korvexcio_retail")
        frappe.conf.korvexcio_retail = {
            "enabled": True,
            "attributes": [
                {"name": self.sabor_name, "values": ["Red"]},
                {"name": self.nicotina_name, "values": ["20"]},
            ],
        }
        try:
            item_attributes.sync_item_attributes()
            names = item_attributes.create_item_template_and_variants(
                {
                    "item_code": self.template_name,
                    "item_name": self.template_name,
                    "item_group": "Products",
                    "stock_uom": "Nos",
                },
                [{"Test Sabor": "Red", "Test Nicotina": "20"}],
            )
            self.assertEqual(names, [self.variant_name])
            variant = frappe.get_doc("Item", self.variant_name)
            self.assertEqual(variant.variant_of, self.template_name)
            self.assertEqual(
                {row.attribute: row.attribute_value for row in variant.attributes},
                {"Test Sabor": "Red", "Test Nicotina": "20"},
            )
        finally:
            frappe.conf.korvexcio_retail = original
