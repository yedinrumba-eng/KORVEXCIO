"""Integration tests for bulk_import.py (S5.1)."""

import frappe
from frappe.tests import IntegrationTestCase
import csv
import tempfile
import os


class TestBulkImport(IntegrationTestCase):
    def setUp(self):
        """Setup aislado por test - crea datos únicos con generate_hash."""
        frappe.set_user("Administrator")
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests
        before_tests()

        # Generar sufijo único para este test
        self.test_hash = frappe.generate_hash(8)

        # Define unique company names for this test
        self.company_a = f"_Test Company KORVEXCIO A {self.test_hash}"
        self.company_b = f"_Test Company KORVEXCIO B {self.test_hash}"

        # Ensure retail is enabled for test site
        frappe.conf.korvexcio_retail = {
            "enabled": True,
            "attributes": [
                {"name": "Sabor", "values": ["Menta", "Fresa", "Mango"]},
                {"name": "Nicotina mg", "values": ["3mg", "6mg", "12mg"]},
                {"name": "Tamaño ml", "values": ["30ml", "60ml"]},
                {"name": "Ohmiaje", "values": ["0.3ohm", "0.5ohm", "0.8ohm", "1.0ohm", "1.2ohm"]},
            ],
        }

        from korvexcio.retail.item_attributes import sync_item_attributes
        sync_item_attributes()

    def tearDown(self):
        """Limpieza completa por test - elimina datos creados."""
        frappe.set_user("Administrator")
        # Limpiar en orden inverso de dependencias
        try:
            # Item Prices
            for price_name in frappe.get_all("Item Price", pluck="name"):
                frappe.delete_doc("Item Price", price_name, force=True)

            # Items
            for item_name in frappe.get_all("Item", pluck="name"):
                if item_name.startswith("TEST-") or item_name.startswith("BULK-") or \
                   item_name.startswith(self.company_a.replace(" ", "-")) or \
                   item_name.startswith(self.company_b.replace(" ", "-")):
                    frappe.delete_doc("Item", item_name, force=True)

            # Item Defaults
            for default_name in frappe.get_all("Item Default", pluck="name"):
                frappe.delete_doc("Item Default", default_name, force=True)

        except (frappe.DoesNotExistError, frappe.ValidationError):
            pass

        super().tearDown()

    def test_parse_csv_creates_correct_itemrows(self):
        """Test CSV parsing produces expected ItemRow objects."""
        from korvexcio.retail.bulk_import import _parse_csv, ItemRow

        csv_content = """item_code,item_name,item_group,stock_uom,is_stock_item,company,warehouse,price_list,price_list_rate,valuation_rate,description,variant_of,sabor,nicotina_mg,tamano_ml,ohmiaje
BULK-TEMPLATE,Test Template,Products,Nos,1,Test Company,Stores - TC,Standard Selling,100,50,Test description,,,,
BULK-VAR1,Test Variant 1,Products,Nos,1,Test Company,Stores - TC,Standard Selling,100,50,Test variant,BULK-TEMPLATE,Menta,3mg,30ml,
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            rows = _parse_csv(csv_path, "Test Company")
            self.assertEqual(len(rows), 2)

            template = rows[0]
            self.assertEqual(template.item_code, "BULK-TEMPLATE")
            self.assertEqual(template.item_name, "Test Template")
            self.assertEqual(template.item_group, "Products")
            self.assertEqual(template.stock_uom, "Nos")
            self.assertEqual(template.is_stock_item, 1)
            self.assertEqual(template.company, "Test Company")
            self.assertEqual(template.variant_of, "")
            self.assertEqual(template.sabor, "")

            variant = rows[1]
            self.assertEqual(variant.item_code, "BULK-VAR1")
            self.assertEqual(variant.variant_of, "BULK-TEMPLATE")
            self.assertEqual(variant.sabor, "Menta")
            self.assertEqual(variant.nicotina_mg, "3mg")
            self.assertEqual(variant.tamano_ml, "30ml")
            self.assertEqual(variant.ohmiaje, "")
        finally:
            os.unlink(csv_path)

    def test_idempotent_import_updates_existing(self):
        """Test that running import twice updates instead of duplicating."""
        from korvexcio.retail.bulk_import import execute_import

        # Create a simple CSV for testing
        csv_content = """item_code,item_name,item_group,stock_uom,is_stock_item,company,warehouse,price_list,price_list_rate,valuation_rate,description,variant_of,sabor,nicotina_mg,tamano_ml,ohmiaje
BULK-IDEM-TMPL,Idempotent Template,Products,Nos,1,{company_a},Stores - TCKA,Standard Selling,100,50,Template desc,,,,
BULK-IDEM-VAR,Idempotent Variant,Products,Nos,1,{company_a},Stores - TCKA,Standard Selling,100,50,Variant desc,BULK-IDEM-TMPL,Menta,3mg,30ml,
""".format(company_a=self.company_a)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            # First import
            result1 = execute_import(csv_path, self.company_a)
            self.assertEqual(result1.created, 2)  # template + variant
            self.assertEqual(result1.updated, 0)
            self.assertEqual(len(result1.errors), 0)

            # Second import (should update)
            result2 = execute_import(csv_path, self.company_a)
            self.assertEqual(result2.created, 0)
            self.assertEqual(result2.updated, 2)  # template + variant updated
            self.assertEqual(len(result2.errors), 0)

            # Verify items exist
            self.assertTrue(frappe.db.exists("Item", "BULK-IDEM-TMPL"))
            self.assertTrue(frappe.db.exists("Item", "BULK-IDEM-VAR"))

            variant = frappe.get_doc("Item", "BULK-IDEM-VAR")
            self.assertEqual(variant.variant_of, "BULK-IDEM-TMPL")
            attrs = {row.attribute: row.attribute_value for row in variant.attributes}
            self.assertEqual(attrs.get("Sabor"), "Menta")
            self.assertEqual(attrs.get("Nicotina mg"), "3mg")
            self.assertEqual(attrs.get("Tamaño ml"), "30ml")

            # Verify Item Defaults
            defaults = frappe.get_all("Item Default", filters={"parent": "BULK-IDEM-VAR"}, fields=["company", "default_warehouse"])
            self.assertEqual(len(defaults), 1)
            self.assertEqual(defaults[0].company, self.company_a)

            # Verify Item Prices
            prices = frappe.get_all("Item Price", filters={"item_code": "BULK-IDEM-VAR"}, fields=["price_list", "price_list_rate"])
            self.assertEqual(len(prices), 2)  # Selling + Buying
        finally:
            os.unlink(csv_path)

    def test_multi_company_import(self):
        """Test import creates correct defaults for both Companies."""
        from korvexcio.retail.bulk_import import execute_import

        csv_content = """item_code,item_name,item_group,stock_uom,is_stock_item,company,warehouse,price_list,price_list_rate,valuation_rate,description,variant_of,sabor,nicotina_mg,tamano_ml,ohmiaje
BULK-MULTI-TMPL,Multi Company Template,Products,Nos,1,{company_a},Stores - TCKA,Standard Selling,100,50,Template A,,,,
BULK-MULTI-TMPL,Multi Company Template,Products,Nos,1,{company_b},Stores - TCKB,Standard Selling,200,80,Template B,,,,
""".format(company_a=self.company_a, company_b=self.company_b)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            result = execute_import(csv_path, "")  # No default company - will use first
            self.assertEqual(len(result.errors), 0)

            # Verify Item Defaults for both companies
            defaults = frappe.get_all("Item Default", filters={"parent": "BULK-MULTI-TMPL"}, fields=["company", "default_warehouse"])
            self.assertEqual(len(defaults), 2)
            companies = {d.company for d in defaults}
            self.assertEqual(companies, {self.company_a, self.company_b})
        finally:
            os.unlink(csv_path)

    def test_variant_with_ohmiaje_attribute(self):
        """Test variant creation with Ohmiaje attribute (Pod coils)."""
        from korvexcio.retail.bulk_import import execute_import

        csv_content = """item_code,item_name,item_group,stock_uom,is_stock_item,company,warehouse,price_list,price_list_rate,valuation_rate,description,variant_of,sabor,nicotina_mg,tamano_ml,ohmiaje
BULK-POD-TMPL,Pod Device,Products,Nos,1,{company_a},Stores - TCKA,Standard Selling,1000,500,Pod device,,,,
BULK-POD-0.3,Pod Coil 0.3ohm,Products,Nos,1,{company_a},Stores - TCKA,Standard Selling,150,70,Coil,BULK-POD-TMPL,,,,0.3ohm
BULK-POD-0.5,Pod Coil 0.5ohm,Products,Nos,1,{company_a},Stores - TCKA,Standard Selling,150,70,Coil,BULK-POD-TMPL,,,,0.5ohm
""".format(company_a=self.company_a)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
            f.write(csv_content)
            csv_path = f.name

        try:
            result = execute_import(csv_path, self.company_a)
            self.assertEqual(len(result.errors), 0)

            # Verify Ohmiaje attribute on variants
            for code in ["BULK-POD-0.3", "BULK-POD-0.5"]:
                variant = frappe.get_doc("Item", code)
                self.assertEqual(variant.variant_of, "BULK-POD-TMPL")
                attrs = {row.attribute: row.attribute_value for row in variant.attributes}
                self.assertIn("Ohmiaje", attrs)
                self.assertEqual(attrs["Ohmiaje"], code.split("-")[-1])
        finally:
            os.unlink(csv_path)

    def test_upsert_item_price_validates_price_list(self):
        """SEC-M07: _upsert_item_price valida que Price List exista para la company."""
        from korvexcio.retail.bulk_import import _upsert_item_price

        # Price List inexistente para la company -> debe fallar
        with self.assertRaises(Exception):  # ValidationError may not be available in test env
            _upsert_item_price("TEST-ITEM", "Price List Inexistente", 100, "Selling", self.company_a)

        # Price List existente (Standard Selling es global) -> debe funcionar
        _upsert_item_price("TEST-ITEM-PL", "Standard Selling", 100, "Selling", self.company_a)
        price = frappe.get_doc("Item Price", {"item_code": "TEST-ITEM-PL", "price_list": "Standard Selling"})
        self.assertEqual(price.price_list_rate, 100)
