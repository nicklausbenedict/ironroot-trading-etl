from __future__ import annotations

import unittest

from src.clean import clean_all_tables
from src.config import RAW_DIR, REJECTION_REASONS_COLUMN
from src.extract import load_all_tables
from src.validate import validate_all_tables


class ValidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cleaned = clean_all_tables(load_all_tables(raw_dir=RAW_DIR))
        cls.validation = validate_all_tables(cleaned)

    def test_rejects_blank_sales_customer_id(self) -> None:
        rejected_sales = self.validation.rejected["sales"]
        blank_customer_rows = rejected_sales[rejected_sales["CustomerId"].astype("string").str.strip() == ""]

        self.assertGreaterEqual(len(blank_customer_rows), 1)
        self.assertTrue(blank_customer_rows[REJECTION_REASONS_COLUMN].str.contains("missing_required_id").all())

    def test_rejects_duplicate_sales_primary_key(self) -> None:
        rejected_sales = self.validation.rejected["sales"]
        duplicate_rows = rejected_sales[rejected_sales["SaleId"].duplicated(keep=False)]

        self.assertGreaterEqual(len(duplicate_rows), 2)
        self.assertTrue(duplicate_rows[REJECTION_REASONS_COLUMN].str.contains("duplicate_primary_key").all())

    def test_rejects_known_invalid_foreign_keys(self) -> None:
        rejected_sales = self.validation.rejected["sales"]
        rejected_inventory = self.validation.rejected["inventory"]
        rejected_purchase_orders = self.validation.rejected["purchase_orders"]

        self.assert_reason_for_value(rejected_sales, "ProductId", "P999", "invalid_foreign_key")
        self.assert_reason_for_value(rejected_inventory, "StoreId", "S404", "invalid_foreign_key")
        self.assert_reason_for_value(rejected_inventory, "ProductId", "P404", "invalid_foreign_key")
        self.assert_reason_for_value(rejected_purchase_orders, "SupplierId", "SUP404", "invalid_foreign_key")

    def assert_reason_for_value(self, df, column: str, value: str, reason: str) -> None:
        rows = df[df[column].astype("string").str.strip() == value]
        self.assertGreaterEqual(len(rows), 1, f"Expected rejected row for {column}={value}")
        self.assertTrue(rows[REJECTION_REASONS_COLUMN].str.contains(reason).all())


if __name__ == "__main__":
    unittest.main()
