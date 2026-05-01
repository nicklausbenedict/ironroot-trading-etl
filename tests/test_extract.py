from __future__ import annotations

import unittest

from src.config import AUDIT_COLUMNS, RAW_DIR, TABLE_SPECS
from src.extract import load_all_tables


class ExtractTests(unittest.TestCase):
    def test_loads_all_expected_raw_tables_with_audit_columns(self) -> None:
        tables = load_all_tables(raw_dir=RAW_DIR)

        self.assertEqual(set(TABLE_SPECS), set(tables))
        for table_name, spec in TABLE_SPECS.items():
            with self.subTest(table=table_name):
                df = tables[table_name]
                self.assertGreater(len(df), 0)
                self.assertEqual(tuple(df.columns[: len(spec.columns)]), spec.columns)
                for audit_column in AUDIT_COLUMNS:
                    self.assertIn(audit_column, df.columns)
                self.assertEqual(df[AUDIT_COLUMNS[0]].iloc[0], spec.filename)


if __name__ == "__main__":
    unittest.main()
