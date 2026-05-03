from __future__ import annotations

from datetime import UTC, datetime
import json
import unittest

import pandas as pd

from src.extract import SourceDataError
from src.upload_s3 import LATEST_MANIFEST_KEY, build_run_id, upload_curated_tables


class FakeS3Client:
    def __init__(self, fail_put_key: str | None = None, fail_head_key: str | None = None) -> None:
        self.fail_put_key = fail_put_key
        self.fail_head_key = fail_head_key
        self.objects: dict[str, bytes] = {}
        self.head_requests: list[str] = []

    def put_object(self, Bucket: str, Key: str, Body: bytes, ContentType: str) -> None:
        if Key == self.fail_put_key:
            raise RuntimeError(f"put failed for {Key}")
        self.objects[Key] = Body

    def head_object(self, Bucket: str, Key: str) -> None:
        if Key == self.fail_head_key:
            raise RuntimeError(f"head failed for {Key}")
        if Key not in self.objects:
            raise RuntimeError(f"missing object {Key}")
        self.head_requests.append(Key)


class UploadS3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.curated = {
            "dim_store": pd.DataFrame({"StoreId": ["S001"], "StoreName": ["Ironroot"]}),
            "dim_product": pd.DataFrame({"ProductId": ["P001"]}),
            "dim_customer": pd.DataFrame({"CustomerId": ["C001"]}),
            "dim_supplier": pd.DataFrame({"SupplierId": ["SUP001"]}),
            "fact_sales": pd.DataFrame({"SaleId": ["SA0001"]}),
            "fact_inventory_snapshot": pd.DataFrame({"InventoryId": ["I00001"]}),
            "fact_purchase_order": pd.DataFrame({"PurchaseOrderId": ["PO0001"]}),
        }
        self.run_timestamp = datetime(2026, 5, 3, 12, 34, 56, tzinfo=UTC)

    def test_build_run_id_uses_utc_timestamp_format(self) -> None:
        self.assertEqual(build_run_id(self.run_timestamp), "20260503T123456Z")

    def test_uploads_all_curated_files_and_manifest_after_verification(self) -> None:
        client = FakeS3Client()

        manifest = upload_curated_tables(
            self.curated,
            bucket="ironroot-test",
            run_timestamp=self.run_timestamp,
            csv_prefix="curated/csv/",
            parquet_prefix="curated/parquet/",
            s3_client=client,
        )

        csv_run_prefix = "curated/csv/20260503T123456Z/"
        parquet_run_prefix = "curated/parquet/20260503T123456Z/"
        expected_csv_keys = {f"{csv_run_prefix}{table_name}.csv" for table_name in self.curated}
        expected_parquet_keys = {f"{parquet_run_prefix}{table_name}.parquet" for table_name in self.curated}
        expected_data_keys = expected_csv_keys | expected_parquet_keys
        self.assertTrue(expected_csv_keys.issubset(client.objects))
        self.assertTrue(expected_parquet_keys.issubset(client.objects))
        self.assertEqual(set(client.head_requests), expected_data_keys)
        self.assertIn(LATEST_MANIFEST_KEY, client.objects)
        self.assertEqual(manifest["run_id"], "20260503T123456Z")
        self.assertEqual(manifest["run_prefixes"]["csv"], csv_run_prefix)
        self.assertEqual(manifest["run_prefixes"]["parquet"], parquet_run_prefix)
        self.assertEqual(set(manifest["tables"]), set(self.curated))

        manifest_from_s3 = json.loads(client.objects[LATEST_MANIFEST_KEY].decode("utf-8"))
        self.assertEqual(manifest_from_s3["tables"]["dim_store"]["row_count"], 1)
        self.assertEqual(manifest_from_s3["tables"]["dim_store"]["csv"]["key"], f"{csv_run_prefix}dim_store.csv")
        self.assertEqual(
            manifest_from_s3["tables"]["dim_store"]["parquet"]["key"],
            f"{parquet_run_prefix}dim_store.parquet",
        )

    def test_upload_failure_prevents_manifest_upload(self) -> None:
        client = FakeS3Client(fail_put_key="curated/csv/20260503T123456Z/fact_sales.csv")

        with self.assertRaises(RuntimeError):
            upload_curated_tables(
                self.curated,
                bucket="ironroot-test",
                run_timestamp=self.run_timestamp,
                s3_client=client,
            )

        self.assertNotIn(LATEST_MANIFEST_KEY, client.objects)

    def test_verification_failure_prevents_manifest_upload(self) -> None:
        client = FakeS3Client(fail_head_key="curated/csv/20260503T123456Z/fact_sales.csv")

        with self.assertRaises(RuntimeError):
            upload_curated_tables(
                self.curated,
                bucket="ironroot-test",
                run_timestamp=self.run_timestamp,
                s3_client=client,
            )

        self.assertNotIn(LATEST_MANIFEST_KEY, client.objects)

    def test_missing_bucket_raises_source_data_error(self) -> None:
        with self.assertRaises(SourceDataError):
            upload_curated_tables(self.curated, bucket="", run_timestamp=self.run_timestamp)


if __name__ == "__main__":
    unittest.main()
