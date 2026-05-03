from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from .clean import clean_all_tables
    from .config import CURATED_DIR, PROCESSED_DIR, RAW_DIR, REJECTED_DIR, REPORTS_DIR
    from .curate import build_curated_tables
    from .extract import load_all_tables
    from .extract_s3 import load_all_s3_tables
    from .models import PipelineResult
    from .upload_s3 import DEFAULT_CURATED_CSV_PREFIX, DEFAULT_CURATED_PARQUET_PREFIX, upload_curated_tables
    from .validate import validate_all_tables
    from .write import write_outputs
except ImportError:  # pragma: no cover - supports `python src/pipeline.py`
    from clean import clean_all_tables
    from config import CURATED_DIR, PROCESSED_DIR, RAW_DIR, REJECTED_DIR, REPORTS_DIR
    from curate import build_curated_tables
    from extract import load_all_tables
    from extract_s3 import load_all_s3_tables
    from models import PipelineResult
    from upload_s3 import DEFAULT_CURATED_CSV_PREFIX, DEFAULT_CURATED_PARQUET_PREFIX, upload_curated_tables
    from validate import validate_all_tables
    from write import write_outputs

SOURCE_LOCAL = "local"
SOURCE_S3 = "s3"


def run_pipeline(
    source: str = SOURCE_LOCAL,
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    rejected_dir: Path = REJECTED_DIR,
    curated_dir: Path = CURATED_DIR,
    reports_dir: Path = REPORTS_DIR,
    upload_curated: bool = False,
    s3_curated_csv_prefix: str | None = None,
    s3_curated_parquet_prefix: str | None = None,
    write_files: bool = True,
) -> PipelineResult:
    ingested_at = datetime.now(UTC)
    raw_tables = load_raw_tables(source=source, raw_dir=raw_dir, ingested_at=ingested_at)
    cleaned_tables = clean_all_tables(raw_tables)
    validation = validate_all_tables(cleaned_tables)
    curated_tables = build_curated_tables(validation.accepted)
    summary = build_summary(raw_tables, validation.accepted, validation.rejected, validation.issue_counts, ingested_at)

    if write_files:
        write_outputs(
            validation.accepted,
            validation.rejected,
            curated_tables,
            summary,
            processed_dir=processed_dir,
            rejected_dir=rejected_dir,
            curated_dir=curated_dir,
            reports_dir=reports_dir,
        )

    if upload_curated:
        load_environment()
        bucket = os.getenv("S3_BUCKET", "").strip()
        csv_prefix = (
            s3_curated_csv_prefix
            or os.getenv("S3_CURATED_CSV_PREFIX", "").strip()
            or DEFAULT_CURATED_CSV_PREFIX
        )
        parquet_prefix = (
            s3_curated_parquet_prefix
            or os.getenv("S3_CURATED_PARQUET_PREFIX", "").strip()
            or DEFAULT_CURATED_PARQUET_PREFIX
        )
        upload_curated_tables(
            curated=curated_tables,
            bucket=bucket,
            csv_prefix=csv_prefix,
            parquet_prefix=parquet_prefix,
            run_timestamp=ingested_at,
        )

    return PipelineResult(
        accepted=validation.accepted,
        rejected=validation.rejected,
        curated=curated_tables,
        summary=summary,
    )


def load_raw_tables(
    source: str,
    raw_dir: Path,
    ingested_at: datetime,
) -> dict[str, Any]:
    if source == SOURCE_LOCAL:
        return load_all_tables(raw_dir=raw_dir, ingested_at=ingested_at)

    if source == SOURCE_S3:
        load_environment()
        bucket = os.getenv("S3_BUCKET", "").strip()
        prefix = os.getenv("S3_RAW_PREFIX", "").strip()
        return load_all_s3_tables(bucket=bucket, prefix=prefix, ingested_at=ingested_at)

    raise ValueError(f"Unsupported source: {source}")


def load_environment() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    load_dotenv()


def build_summary(
    raw_tables: dict[str, Any],
    accepted: dict[str, Any],
    rejected: dict[str, Any],
    issue_counts: dict[str, dict[str, int]],
    ingested_at: datetime,
) -> dict[str, Any]:
    table_summaries = {}
    total_raw = 0
    total_accepted = 0
    total_rejected = 0

    for table_name, raw_df in raw_tables.items():
        raw_count = len(raw_df)
        accepted_count = len(accepted[table_name])
        rejected_count = len(rejected[table_name])
        total_raw += raw_count
        total_accepted += accepted_count
        total_rejected += rejected_count
        table_summaries[table_name] = {
            "raw_rows": raw_count,
            "accepted_rows": accepted_count,
            "rejected_rows": rejected_count,
            "issue_counts": issue_counts.get(table_name, {}),
        }

    return {
        "ingested_at": ingested_at.isoformat(),
        "totals": {
            "raw_rows": total_raw,
            "accepted_rows": total_accepted,
            "rejected_rows": total_rejected,
        },
        "tables": table_summaries,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Ironroot raw CSV ingest, clean, and validate stage.")
    parser.add_argument("--source", choices=(SOURCE_LOCAL, SOURCE_S3), default=SOURCE_LOCAL)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--rejected-dir", type=Path, default=REJECTED_DIR)
    parser.add_argument("--curated-dir", type=Path, default=CURATED_DIR)
    parser.add_argument("--reports-dir", type=Path, default=REPORTS_DIR)
    parser.add_argument("--upload-curated", action="store_true")
    parser.add_argument("--s3-curated-csv-prefix")
    parser.add_argument("--s3-curated-parquet-prefix")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_pipeline(
        source=args.source,
        raw_dir=args.raw_dir,
        processed_dir=args.processed_dir,
        rejected_dir=args.rejected_dir,
        curated_dir=args.curated_dir,
        reports_dir=args.reports_dir,
        upload_curated=args.upload_curated,
        s3_curated_csv_prefix=args.s3_curated_csv_prefix,
        s3_curated_parquet_prefix=args.s3_curated_parquet_prefix,
    )
    totals = result.summary["totals"]
    print(
        "Pipeline complete: "
        f"{totals['accepted_rows']} accepted, "
        f"{totals['rejected_rows']} rejected, "
        f"{totals['raw_rows']} raw rows."
    )


if __name__ == "__main__":
    main()
