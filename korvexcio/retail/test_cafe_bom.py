"""Integration test for the blueprint's real S3.4 criterion: "vender un
cafe que descuenta insumos del inventario" -- the existing test_cafe.py
only unit-tested that the catalog sync is off by default, never that the
BOM it builds actually deducts ingredient stock when the recipe is made.
A BOM inserted but never exercised could have the wrong item/qty and
nobody would notice until a real sale tried to use it."""

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from korvexcio.retail.cafe import sync_cafe_catalog

COMPANY_A = "_Test Company KORVEXCIO A"
ABBR_A = "_TCKA"
WAREHOUSE = f"Stores - {ABBR_A}"

CONFIG = {
    "enabled": True,
    "cafe": {
        "enabled": True,
        "company": COMPANY_A,
        "products": [
            {
                "item_code": "_Test Cafe Americano",
                "item_name": "Cafe Americano",
                "item_group": "All Item Groups",
                "quantity": 1,
                "ingredients": [
                    # cafe.py fija stock_uom="Nos" (entero) para todo
                    # ingrediente hoy -- cantidades fraccionarias (ej.
                    # 0.02 kg de cafe molido) necesitarian UOM por peso,
                    # fuera del alcance actual (D14: cafeteria mostrador
                    # basico). Cantidades enteras, honesto a lo que el
                    # codigo soporta de verdad.
                    {
                        "item_code": "_Test Cafe Molido",
                        "item_name": "Cafe Molido",
                        "item_group": "All Item Groups",
                        "qty": 2,
                    },
                    {
                        "item_code": "_Test Cafe Vaso",
                        "item_name": "Vaso Desechable",
                        "item_group": "All Item Groups",
                        "qty": 1,
                    },
                ],
            }
        ],
    },
}


class TestCafeBomConsumesStock(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not frappe.local.lang:
            frappe.local.lang = "en"

        from korvexcio.install import before_tests

        before_tests()

        with (
            patch("korvexcio.retail.cafe.get_retail_config", return_value=CONFIG),
            patch("korvexcio.retail.cafe.is_vertical_enabled", return_value=True),
        ):
            sync_cafe_catalog()

    def setUp(self):
        frappe.set_user("Administrator")
        for item_code, qty in (("_Test Cafe Molido", 10), ("_Test Cafe Vaso", 50)):
            self._receive_stock(item_code, qty)

    def _receive_stock(self, item_code: str, qty: float) -> None:
        entry = frappe.get_doc(
            {
                "doctype": "Stock Entry",
                "stock_entry_type": "Material Receipt",
                "company": COMPANY_A,
                "items": [
                    {
                        "item_code": item_code,
                        "qty": qty,
                        "t_warehouse": WAREHOUSE,
                        "basic_rate": 10,
                    }
                ],
            }
        )
        entry.insert()
        entry.submit()

    def _stock(self, item_code: str) -> float:
        return frappe.db.get_value(
            "Bin", {"item_code": item_code, "warehouse": WAREHOUSE}, "actual_qty"
        ) or 0

    def test_manufacturing_the_recipe_deducts_ingredients_and_adds_finished_good(self):
        # Mismo patron que usa el propio ERPNext en
        # test_stock_entry.py::test_manufacture_entry_without_wo -- mi
        # primer intento armando el Stock Entry a mano (sin production_item)
        # dejaba get_items() sin saber cual fila era el producto terminado
        # ("There must be atleast 1 Finished Good in this Stock Entry").
        from erpnext.stock.doctype.stock_entry.test_stock_entry import make_stock_entry

        coffee_before = self._stock("_Test Cafe Americano")
        beans_before = self._stock("_Test Cafe Molido")
        cups_before = self._stock("_Test Cafe Vaso")

        bom_name = frappe.db.exists(
            "BOM", {"item": "_Test Cafe Americano", "is_active": 1, "is_default": 1}
        )
        self.assertIsNotNone(bom_name, "sync_cafe_catalog no creo el BOM del producto")

        manufacture = make_stock_entry(
            item_code="_Test Cafe Americano",
            qty=1,
            purpose="Manufacture",
            company=COMPANY_A,
            do_not_save=True,
        )
        manufacture.from_bom = 1
        manufacture.bom_no = bom_name
        manufacture.fg_completed_qty = 1
        manufacture.from_warehouse = WAREHOUSE
        manufacture.to_warehouse = WAREHOUSE
        manufacture.get_items()
        manufacture.calculate_rate_and_amount()
        manufacture.save()
        manufacture.submit()

        self.assertEqual(self._stock("_Test Cafe Americano"), coffee_before + 1)
        self.assertEqual(self._stock("_Test Cafe Molido"), beans_before - 2)
        self.assertEqual(self._stock("_Test Cafe Vaso"), cups_before - 1)
