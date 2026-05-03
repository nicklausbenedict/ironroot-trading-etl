from __future__ import annotations

from datetime import UTC, datetime
import json
from os import environ
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from src.config import RAW_DIR, TABLE_SPECS
from src.extract import SourceDataError
from src.pipeline import SOURCE_LOCAL, SOURCE_S3, load_raw_tables
from src.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_outputs_and_preserves_row_counts(self) -> None:
        base_dir = Path("tmp_test_outputs")
        self.addCleanup(lambda: shutil.rmtree(base_dir, ignore_errors=True))
        processed_dir = base_dir / "processed"
        rejected_dir = base_dir / "rejected"
        curated_dir = base_dir / "curated"
        reports_dir = base_dir / "reports"
        for output_dir in (processed_dir, rejected_dir, curated_dir, reports_dir):
            output_dir.mkdir(parents=True, exist_ok=True)

        result = run_pipeline(
            raw_dir=RAW_DIR,
            processed_dir=processed_dir,
            rejected_dir=rejected_dir,
            curated_dir=curated_dir,
            reports_dir=reports_dir,
        )

        for table_name in TABLE_SPECS:
            with self.subTest(table=table_name):
                summary = result.summary["tables"][table_name]
                self.assertEqual(summary["raw_rows"], summary["accepted_rows"] + summary["rejected_rows"])
                self.assertTrue((processed_dir / f"{table_name}.csv").exists())
                self.assertTrue((rejected_dir / f"{table_name}_rejected.csv").exists())

        expected_curated_tables = {
            "dim_store",
            "dim_product",
            "dim_customer",
            "dim_supplier",
            "fact_sales",
            "fact_inventory_snapshot",
            "fact_purchase_order",
        }
        self.assertEqual(expected_curated_tables, set(result.curated))
        for table_name in expected_curated_tables:
            with self.subTest(curated_table=table_name):
                self.assertTrue((curated_dir / "csv" / f"{table_name}.csv").exists())
                self.assertTrue((curated_dir / "parquet" / f"{table_name}.parquet").exists())

        report_path = reports_dir / "validation_summary.json"
        self.assertTrue(report_path.exists())
        with report_path.open(encoding="utf-8") as report_file:
            report = json.load(report_file)
        self.assertEqual(report["totals"], result.summary["totals"])

    def test_local_source_uses_local_loader(self) -> None:
        expected = {"stores": object()}

        with patch("src.pipeline.load_all_tables", return_value=expected) as loader:
            result = load_raw_tables(SOURCE_LOCAL, RAW_DIR, datetime(2026, 5, 2, tzinfo=UTC))

        self.assertIs(result, expected)
        loader.assert_called_once()

    def test_s3_source_uses_environment_config(self) -> None:
        expected = {"stores": object()}

        with patch.dict(environ, {"S3_BUCKET": "ironroot-test", "S3_RAW_PREFIX": "raw/"}, clear=True):
            with patch("src.pipeline.load_all_s3_tables", return_value=expected) as loader:
                result = load_raw_tables(SOURCE_S3, RAW_DIR, datetime(2026, 5, 2, tzinfo=UTC))

        self.assertIs(result, expected)
        loader.assert_called_once()
        self.assertEqual(loader.call_args.kwargs["bucket"], "ironroot-test")
        self.assertEqual(loader.call_args.kwargs["prefix"], "raw/")

    def test_s3_source_requires_bucket(self) -> None:
        with patch.dict(environ, {}, clear=True):
            with patch("src.pipeline.load_environment"):
                with self.assertRaises(SourceDataError):
                    load_raw_tables(SOURCE_S3, RAW_DIR, datetime(2026, 5, 2, tzinfo=UTC))

    def test_pipeline_does_not_upload_curated_by_default(self) -> None:
        with patch("src.pipeline.upload_curated_tables") as uploader:
            run_pipeline(write_files=False)

        uploader.assert_not_called()

    def test_pipeline_uploads_curated_when_enabled(self) -> None:
        with patch.dict(
            environ,
            {
                "S3_BUCKET": "ironroot-test",
                "S3_CURATED_CSV_PREFIX": "curated/csv/",
                "S3_CURATED_PARQUET_PREFIX": "curated/parquet/",
            },
            clear=True,
        ):
            with patch("src.pipeline.load_environment"):
                with patch("src.pipeline.upload_curated_tables") as uploader:
                    result = run_pipeline(write_files=False, upload_curated=True)

        uploader.assert_called_once()
        self.assertIs(uploader.call_args.kwargs["curated"], result.curated)
        self.assertEqual(uploader.call_args.kwargs["bucket"], "ironroot-test")
        self.assertEqual(uploader.call_args.kwargs["csv_prefix"], "curated/csv/")
        self.assertEqual(uploader.call_args.kwargs["parquet_prefix"], "curated/parquet/")

    def test_pipeline_upload_curated_requires_bucket(self) -> None:
        with patch.dict(environ, {}, clear=True):
            with patch("src.pipeline.load_environment"):
                with self.assertRaises(SourceDataError):
                    run_pipeline(write_files=False, upload_curated=True)


if __name__ == "__main__":
    unittest.main()
