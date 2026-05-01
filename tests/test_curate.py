from __future__ import annotations

import unittest

from src.curate import CURATED_COLUMNS
from src.pipeline import run_pipeline


class CurateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = run_pipeline(write_files=False)
        cls.curated = cls.result.curated

    def test_curated_tables_have_expected_columns(self) -> None:
        self.assertEqual(set(CURATED_COLUMNS), set(self.curated))
        for table_name, columns in CURATED_COLUMNS.items():
            with self.subTest(table=table_name):
                self.assertEqual(tuple(self.curated[table_name].columns), columns)

    def test_dimension_counts_match_accepted_sources(self) -> None:
        expectations = {
            "dim_store": "stores",
            "dim_product": "products",
            "dim_customer": "customers",
            "dim_supplier": "suppliers",
        }
        for dimension_table, source_table in expectations.items():
            with self.subTest(table=dimension_table):
                self.assertEqual(len(self.curated[dimension_table]), len(self.result.accepted[source_table]))

    def test_fact_sales_derived_fields(self) -> None:
        fact_sales = self.curated["fact_sales"]
        first_sale = fact_sales.iloc[0]
        product = self.result.accepted["products"][
            self.result.accepted["products"]["ProductId"] == first_sale["ProductId"]
        ].iloc[0]

        expected_revenue = first_sale["Quantity"] * first_sale["UnitPriceGold"]
        expected_variance = first_sale["UnitPriceGold"] - product["BasePriceGold"]
        expected_variance_percent = expected_variance / product["BasePriceGold"]

        self.assertEqual(len(fact_sales), len(self.result.accepted["sales"]))
        self.assertAlmostEqual(first_sale["RevenueGold"], expected_revenue)
        self.assertAlmostEqual(first_sale["PriceVarianceGold"], expected_variance)
        self.assertAlmostEqual(first_sale["PriceVariancePercent"], expected_variance_percent)

    def test_fact_inventory_snapshot_derived_field(self) -> None:
        inventory = self.curated["fact_inventory_snapshot"]

        below_row = inventory[inventory["QuantityOnHand"] < inventory["ReorderThreshold"]].iloc[0]
        not_below_row = inventory[inventory["QuantityOnHand"] >= inventory["ReorderThreshold"]].iloc[0]

        self.assertTrue(below_row["IsBelowReorderThreshold"])
        self.assertFalse(not_below_row["IsBelowReorderThreshold"])

    def test_fact_purchase_order_late_fields(self) -> None:
        purchase_orders = self.curated["fact_purchase_order"]
        on_time = purchase_orders[purchase_orders["PurchaseOrderId"] == "PO0001"].iloc[0]
        late = purchase_orders[purchase_orders["PurchaseOrderId"] == "PO0002"].iloc[0]

        self.assertEqual(on_time["DaysLate"], 0)
        self.assertFalse(on_time["WasLate"])
        self.assertEqual(late["DaysLate"], 2)
        self.assertTrue(late["WasLate"])


if __name__ == "__main__":
    unittest.main()
