"""Tests para S5.2 — Script inventario inicial (stock_initial.py)."""

import json
import tempfile
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase


class TestStockInitial(IntegrationTestCase):
    """Tests del script de inventario inicial."""

    def setUp(self):
        frappe.set_user("Administrator")
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests

        before_tests()

        # Sufijo único para aislamiento
        self.test_hash = frappe.generate_hash(8)
        self.company = f"_Test Company KORVEXCIO A {self.test_hash}"
        self.abbr = f"_TCKA-{self.test_hash}"

        # Crear items de prueba
        self.item1 = f"_Test Stock Item 1 {self.test_hash}"
        self.item2 = f"_Test Stock Item 2 {self.test_hash}"

        for item_code in [self.item1, self.item2]:
            frappe.get_doc(
                {
                    "doctype": "Item",
                    "item_code": item_code,
                    "item_name": item_code,
                    "item_group": "All Item Groups",
                    "is_stock_item": 1,
                    "stock_uom": "Nos",
                }
            ).insert()

        # Crear warehouse
        self.warehouse = f"Stores - {self.abbr}"
        frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": f"Stores Test {self.test_hash}",
                "company": self.company,
            }
        ).insert()

    def tearDown(self):
        frappe.set_user("Administrator")
        try:
            # Cleanup Stock Entries
            for se_name in frappe.get_all(
                "Stock Entry",
                filters={"company": self.company, "stock_entry_type": "Material Receipt"},
                pluck="name",
            ):
                doc = frappe.get_doc("Stock Entry", se_name)
                if doc.docstatus == 1:
                    doc.cancel()
                frappe.delete_doc("Stock Entry", se_name, force=True, ignore_permissions=True)

            # Cleanup items
            for item_code in [self.item1, self.item2]:
                if frappe.db.exists("Item", item_code):
                    frappe.delete_doc("Item", item_code, force=True, ignore_permissions=True)

            # Cleanup warehouse
            if frappe.db.exists("Warehouse", self.warehouse):
                frappe.delete_doc("Warehouse", self.warehouse, force=True, ignore_permissions=True)

        except (frappe.DoesNotExistError, frappe.ValidationError):
            pass

    def test_run_creates_material_receipt(self):
        """Test que run() crea Stock Entry Material Receipt válido."""
        from korvexcio.retail.stock_initial import run

        # Crear archivo origen temporal
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "items": [
                        {
                            "item_code": self.item1,
                            "warehouse": self.warehouse,
                            "qty": 50,
                            "basic_rate": 100,
                        }
                    ]
                },
                f,
            )
            source_path = f.name

        try:
            result = run(source_path)

            self.assertEqual(len(result["created"]), 1)
            self.assertEqual(len(result["skipped"]), 0)

            se_name = result["created"][0]
            se_doc = frappe.get_doc("Stock Entry", se_name)

            self.assertEqual(se_doc.stock_entry_type, "Material Receipt")
            self.assertEqual(se_doc.company, self.company)
            self.assertEqual(se_doc.docstatus, 1)
            self.assertEqual(len(se_doc.items), 1)
            self.assertEqual(se_doc.items[0].item_code, self.item1)
            self.assertEqual(se_doc.items[0].qty, 50)
            self.assertEqual(se_doc.items[0].t_warehouse, self.warehouse)
            self.assertEqual(se_doc.items[0].basic_rate, 100)

            # Verificar que el stock subió
            actual_qty = frappe.db.get_value(
                "Bin", {"item_code": self.item1, "warehouse": self.warehouse}, "actual_qty"
            )
            self.assertEqual(actual_qty, 50)

        finally:
            Path(source_path).unlink(missing_ok=True)

    def test_idempotent_skip_existing(self):
        """Test idempotencia: no duplica si ya existe Stock Entry idéntico."""
        from korvexcio.retail.stock_initial import run

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "items": [
                        {
                            "item_code": self.item1,
                            "warehouse": self.warehouse,
                            "qty": 25,
                            "basic_rate": 50,
                        }
                    ]
                },
                f,
            )
            source_path = f.name

        try:
            # Primera corrida
            result1 = run(source_path)
            self.assertEqual(len(result1["created"]), 1)
            self.assertEqual(len(result1["skipped"]), 0)

            # Segunda corrida con mismo archivo
            result2 = run(source_path)
            self.assertEqual(len(result2["created"]), 0)
            self.assertEqual(len(result2["skipped"]), 1)
            self.assertEqual(result2["skipped"][0], result1["created"][0])

            # Stock no debe duplicarse
            actual_qty = frappe.db.get_value(
                "Bin", {"item_code": self.item1, "warehouse": self.warehouse}, "actual_qty"
            )
            self.assertEqual(actual_qty, 25)

        finally:
            Path(source_path).unlink(missing_ok=True)

    def test_rollback_on_error(self):
        """Test rollback: si una fila falla al crear, se revierte todo lo creado.

        La primera fila es válida y se crea; la segunda es un item no-stock,
        que Stock Entry rechaza al submit() — falla en la FASE 2 (creación),
        no en la validación. El rollback debe revertir la primera.
        """
        from korvexcio.retail.stock_initial import run

        # Item no-stock: pasa validate_row (existe), pero Stock Entry lo rechaza
        non_stock_item = f"_Test NonStock {self.test_hash}"
        frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": non_stock_item,
                "item_name": non_stock_item,
                "item_group": "All Item Groups",
                "is_stock_item": 0,
                "stock_uom": "Nos",
            }
        ).insert()
        self.addCleanup(self._cleanup_non_stock_item, non_stock_item)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "items": [
                        {
                            "item_code": self.item1,
                            "warehouse": self.warehouse,
                            "qty": 10,
                            "basic_rate": 10,
                        },
                        {
                            "item_code": non_stock_item,  # Falla en submit() (FASE 2)
                            "warehouse": self.warehouse,
                            "qty": 10,
                            "basic_rate": 10,
                        },
                    ]
                },
                f,
            )
            source_path = f.name

        try:
            with self.assertRaises(RuntimeError):
                run(source_path)

            # Verificar que NO quedó ningún Stock Entry (rollback)
            ses = frappe.get_all(
                "Stock Entry",
                filters={"company": self.company, "stock_entry_type": "Material Receipt"},
                pluck="name",
            )
            self.assertEqual(len(ses), 0)

            # Stock de item1 debe ser 0 (la primera creación se revirtió)
            actual_qty = frappe.db.get_value(
                "Bin", {"item_code": self.item1, "warehouse": self.warehouse}, "actual_qty"
            )
            self.assertEqual(actual_qty or 0, 0)

        finally:
            Path(source_path).unlink(missing_ok=True)

    def test_skip_invalid_qty(self):
        """Test que qty <= 0 se rechaza abortando la carga (antes de crear nada)."""
        from korvexcio.retail.stock_initial import run

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "items": [
                        {
                            "item_code": self.item1,
                            "warehouse": self.warehouse,
                            "qty": 0,  # Inválido
                            "basic_rate": 10,
                        }
                    ]
                },
                f,
            )
            source_path = f.name

        try:
            with self.assertRaises(ValueError):
                run(source_path)

            # Nada debió crearse (validación aborta antes de tocar la DB)
            ses = frappe.get_all(
                "Stock Entry",
                filters={"company": self.company, "stock_entry_type": "Material Receipt"},
                pluck="name",
            )
            self.assertEqual(len(ses), 0)

        finally:
            Path(source_path).unlink(missing_ok=True)

    def test_multiple_items_different_warehouses(self):
        """Test múltiples items y warehouses en una corrida."""
        from korvexcio.retail.stock_initial import run

        # Crear segunda company/warehouse
        company2 = f"_Test Company KORVEXCIO B {self.test_hash}"
        abbr2 = f"_TCKB-{self.test_hash}"
        warehouse2 = f"Stores - {abbr2}"

        frappe.get_doc(
            {
                "doctype": "Company",
                "company_name": company2,
                "abbr": abbr2,
                "default_currency": "DOP",
                "country": "Dominican Republic",
                "tax_id": "000-0000003-3",
            }
        ).insert()

        frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": f"Stores Test {self.test_hash}",
                "company": company2,
            }
        ).insert()

        self.addCleanup(lambda: self._cleanup_company2(company2, warehouse2))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "items": [
                        {
                            "item_code": self.item1,
                            "warehouse": self.warehouse,
                            "qty": 30,
                            "basic_rate": 100,
                        },
                        {
                            "item_code": self.item2,
                            "warehouse": warehouse2,
                            "qty": 40,
                            "basic_rate": 200,
                        },
                    ]
                },
                f,
            )
            source_path = f.name

        try:
            result = run(source_path)
            self.assertEqual(len(result["created"]), 2)
            self.assertEqual(len(result["skipped"]), 0)

            # Verificar stock en ambos warehouses
            qty1 = frappe.db.get_value(
                "Bin", {"item_code": self.item1, "warehouse": self.warehouse}, "actual_qty"
            )
            qty2 = frappe.db.get_value(
                "Bin", {"item_code": self.item2, "warehouse": warehouse2}, "actual_qty"
            )
            self.assertEqual(qty1, 30)
            self.assertEqual(qty2, 40)

        finally:
            Path(source_path).unlink(missing_ok=True)

    def _cleanup_company2(self, company2: str, warehouse2: str):
        try:
            for se_name in frappe.get_all(
                "Stock Entry",
                filters={"company": company2, "stock_entry_type": "Material Receipt"},
                pluck="name",
            ):
                doc = frappe.get_doc("Stock Entry", se_name)
                if doc.docstatus == 1:
                    doc.cancel()
                frappe.delete_doc("Stock Entry", se_name, force=True, ignore_permissions=True)

            if frappe.db.exists("Warehouse", warehouse2):
                frappe.delete_doc("Warehouse", warehouse2, force=True, ignore_permissions=True)
            if frappe.db.exists("Company", company2):
                frappe.delete_doc("Company", company2, force=True, ignore_permissions=True)
        except (frappe.DoesNotExistError, frappe.ValidationError):
            pass

    def _cleanup_non_stock_item(self, item_code: str):
        try:
            if frappe.db.exists("Item", item_code):
                frappe.delete_doc("Item", item_code, force=True, ignore_permissions=True)
        except (frappe.DoesNotExistError, frappe.ValidationError):
            pass

    def test_csv_source(self):
        """Test carga desde CSV."""
        from korvexcio.retail.stock_initial import run

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("item_code,warehouse,qty,basic_rate\n")
            f.write(f"{self.item1},{self.warehouse},60,75\n")
            source_path = f.name

        try:
            result = run(source_path)
            self.assertEqual(len(result["created"]), 1)
            self.assertEqual(result["details"][0]["basic_rate"], 75)

        finally:
            Path(source_path).unlink(missing_ok=True)
