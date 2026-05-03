from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
import unittest

from src.config import AUDIT_COLUMNS, TABLE_SPECS
from src.extract import SourceDataError
from src.extract_s3 import build_s3_key, load_s3_table


class FakeS3Client:
    def __init__(self, objects: dict[tuple[str, str], bytes]) -> None:
        self.objects = objects
        self.requests: list[tuple[str, str]] = []

    def get_object(self, Bucket: str, Key: str) -> dict[str, BytesIO]:
        self.requests.append((Bucket, Key))
        return {"Body": BytesIO(self.objects[(Bucket, Key)])}


class ExtractS3Tests(unittest.TestCase):
    def test_loads_s3_table_with_schema_and_audit_columns(self) -> None:
        bucket = "ironroot-test"
        key = "raw/stores.csv"
        csv_bytes = (
            b"StoreId,StoreName,Region,Zone,FactionAlignment\n"
            b"S001,Ironroot Trading Co.,Eastern Kingdoms,Elwynn Forest,Alliance\n"
        )
        client = FakeS3Client({(bucket, key): csv_bytes})

        df = load_s3_table(
            TABLE_SPECS["stores"],
            bucket=bucket,
            prefix="raw/",
            ingested_at=datetime(2026, 5, 2, tzinfo=UTC),
            s3_client=client,
        )

        self.assertEqual(len(df), 1)
        self.assertEqual(tuple(df.columns[: len(TABLE_SPECS["stores"].columns)]), TABLE_SPECS["stores"].columns)
        self.assertEqual(df[AUDIT_COLUMNS[0]].iloc[0], f"s3://{bucket}/{key}")
        self.assertEqual(df[AUDIT_COLUMNS[1]].iloc[0], 2)
        self.assertEqual(client.requests, [(bucket, key)])

    def test_schema_mismatch_raises_source_data_error(self) -> None:
        bucket = "ironroot-test"
        key = "stores.csv"
        client = FakeS3Client({(bucket, key): b"WrongColumn\nvalue\n"})

        with self.assertRaises(SourceDataError):
            load_s3_table(TABLE_SPECS["stores"], bucket=bucket, s3_client=client)

    def test_build_s3_key_handles_optional_prefix(self) -> None:
        self.assertEqual(build_s3_key("", "stores.csv"), "stores.csv")
        self.assertEqual(build_s3_key("raw", "stores.csv"), "raw/stores.csv")
        self.assertEqual(build_s3_key("/raw/", "stores.csv"), "raw/stores.csv")


if __name__ == "__main__":
    unittest.main()
