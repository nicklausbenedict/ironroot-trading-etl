from __future__ import annotations

import shutil
import unittest
from pathlib import Path

import pandas as pd

from src.write import write_curated_outputs


class WriteTests(unittest.TestCase):
    def test_write_curated_outputs_writes_csv_and_parquet(self) -> None:
        output_dir = Path("tmp_test_outputs") / "curated"
        self.addCleanup(lambda: shutil.rmtree("tmp_test_outputs", ignore_errors=True))
        curated = {
            "dim_store": pd.DataFrame(
                {
                    "StoreId": ["S001"],
                    "StoreName": ["Ironroot Trading Co."],
                }
            )
        }

        write_curated_outputs(curated, curated_dir=output_dir)

        csv_path = output_dir / "csv" / "dim_store.csv"
        parquet_path = output_dir / "parquet" / "dim_store.parquet"
        self.assertTrue(csv_path.exists())
        self.assertTrue(parquet_path.exists())

        parquet = pd.read_parquet(parquet_path, engine="pyarrow")
        self.assertEqual(len(parquet), 1)
        self.assertEqual(tuple(parquet.columns), ("StoreId", "StoreName"))


if __name__ == "__main__":
    unittest.main()
