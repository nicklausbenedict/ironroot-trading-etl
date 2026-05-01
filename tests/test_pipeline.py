from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path

from src.config import RAW_DIR, TABLE_SPECS
from src.pipeline import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_outputs_and_preserves_row_counts(self) -> None:
        base_dir = Path("tmp_test_outputs")
        self.addCleanup(lambda: shutil.rmtree(base_dir, ignore_errors=True))
        processed_dir = base_dir / "processed"
        rejected_dir = base_dir / "rejected"
        reports_dir = base_dir / "reports"
        for output_dir in (processed_dir, rejected_dir, reports_dir):
            output_dir.mkdir(parents=True, exist_ok=True)

        result = run_pipeline(
            raw_dir=RAW_DIR,
            processed_dir=processed_dir,
            rejected_dir=rejected_dir,
            reports_dir=reports_dir,
        )

        for table_name in TABLE_SPECS:
            with self.subTest(table=table_name):
                summary = result.summary["tables"][table_name]
                self.assertEqual(summary["raw_rows"], summary["accepted_rows"] + summary["rejected_rows"])
                self.assertTrue((processed_dir / f"{table_name}.csv").exists())
                self.assertTrue((rejected_dir / f"{table_name}_rejected.csv").exists())

        report_path = reports_dir / "validation_summary.json"
        self.assertTrue(report_path.exists())
        with report_path.open(encoding="utf-8") as report_file:
            report = json.load(report_file)
        self.assertEqual(report["totals"], result.summary["totals"])


if __name__ == "__main__":
    unittest.main()
