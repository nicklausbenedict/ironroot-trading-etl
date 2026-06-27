from __future__ import annotations

from os import environ
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from glue.ironroot_glue_job import apply_environment, main, parse_glue_args
from src.pipeline import SOURCE_S3


class GlueJobTests(unittest.TestCase):
    def test_parse_glue_args_reads_known_pipeline_settings(self) -> None:
        args = parse_glue_args(
            [
                "--JOB_NAME",
                "ironroot",
                "--S3_BUCKET",
                "ironroot-test",
                "--S3_RAW_PREFIX",
                "raw/",
                "--S3_CURATED_CSV_PREFIX",
                "curated/csv/",
                "--S3_CURATED_PARQUET_PREFIX",
                "curated/parquet/",
            ]
        )

        self.assertEqual(args["S3_BUCKET"], "ironroot-test")
        self.assertEqual(args["S3_RAW_PREFIX"], "raw/")
        self.assertEqual(args["S3_CURATED_CSV_PREFIX"], "curated/csv/")
        self.assertEqual(args["S3_CURATED_PARQUET_PREFIX"], "curated/parquet/")
        self.assertNotIn("JOB_NAME", args)

    def test_parse_glue_args_rejects_missing_known_value(self) -> None:
        with self.assertRaises(ValueError):
            parse_glue_args(["--S3_BUCKET"])

    def test_apply_environment_sets_nonblank_values(self) -> None:
        with patch.dict(environ, {}, clear=True):
            apply_environment({"S3_BUCKET": " ironroot-test ", "S3_RAW_PREFIX": " "})

            self.assertEqual(environ["S3_BUCKET"], "ironroot-test")
            self.assertNotIn("S3_RAW_PREFIX", environ)

    def test_main_runs_s3_pipeline_without_local_file_outputs(self) -> None:
        result = SimpleNamespace(
            summary={
                "totals": {
                    "accepted_rows": 1,
                    "rejected_rows": 0,
                    "raw_rows": 1,
                }
            }
        )

        with patch.dict(environ, {}, clear=True):
            with patch("glue.ironroot_glue_job.run_pipeline", return_value=result) as pipeline:
                main(["--S3_BUCKET", "ironroot-test", "--S3_RAW_PREFIX", "raw/"])

        pipeline.assert_called_once_with(
            source=SOURCE_S3,
            upload_curated=True,
            write_files=False,
        )


if __name__ == "__main__":
    unittest.main()
