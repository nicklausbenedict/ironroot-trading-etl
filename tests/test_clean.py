from __future__ import annotations

import unittest

from src.clean import clean_all_tables
from src.config import RAW_DIR
from src.extract import load_all_tables


class CleanTests(unittest.TestCase):
    def test_trims_whitespace_from_sales_store_ids(self) -> None:
        raw_tables = load_all_tables(raw_dir=RAW_DIR)
        raw_sales = raw_tables["sales"]
        padded_raw_count = (raw_sales["StoreId"] != raw_sales["StoreId"].str.strip()).sum()

        cleaned_sales = clean_all_tables(raw_tables)["sales"]
        padded_clean_count = (cleaned_sales["StoreId"] != cleaned_sales["StoreId"].str.strip()).sum()

        self.assertGreaterEqual(padded_raw_count, 1)
        self.assertEqual(padded_clean_count, 0)

    def test_converts_numeric_boolean_and_date_columns(self) -> None:
        cleaned = clean_all_tables(load_all_tables(raw_dir=RAW_DIR))

        self.assertEqual(str(cleaned["sales"]["Quantity"].dtype), "Int64")
        self.assertEqual(str(cleaned["sales"]["UnitPriceGold"].dtype), "Float64")
        self.assertEqual(str(cleaned["products"]["IsPerishable"].dtype), "boolean")
        self.assertTrue(hasattr(cleaned["sales"]["SaleDate"].iloc[0], "isoformat"))


if __name__ == "__main__":
    unittest.main()
