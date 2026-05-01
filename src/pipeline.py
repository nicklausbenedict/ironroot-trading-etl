from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from .clean import clean_all_tables
    from .config import CURATED_DIR, PROCESSED_DIR, RAW_DIR, REJECTED_DIR, REPORTS_DIR
    from .curate import build_curated_tables
    from .extract import load_all_tables
    from .models import PipelineResult
    from .validate import validate_all_tables
    from .write import write_outputs
except ImportError:  # pragma: no cover - supports `python src/pipeline.py`
    from clean import clean_all_tables
    from config import CURATED_DIR, PROCESSED_DIR, RAW_DIR, REJECTED_DIR, REPORTS_DIR
    from curate import build_curated_tables
    from extract import load_all_tables
    from models import PipelineResult
    from validate import validate_all_tables
    from write import write_outputs


def run_pipeline(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    rejected_dir: Path = REJECTED_DIR,
    curated_dir: Path = CURATED_DIR,
    reports_dir: Path = REPORTS_DIR,
    write_files: bool = True,
) -> PipelineResult:
    ingested_at = datetime.now(UTC)
    raw_tables = load_all_tables(raw_dir=raw_dir, ingested_at=ingested_at)
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

    return PipelineResult(
        accepted=validation.accepted,
        rejected=validation.rejected,
        curated=curated_tables,
        summary=summary,
    )


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
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--processed-dir", type=Path, default=PROCESSED_DIR)
    parser.add_argument("--rejected-dir", type=Path, default=REJECTED_DIR)
    parser.add_argument("--curated-dir", type=Path, default=CURATED_DIR)
    parser.add_argument("--reports-dir", type=Path, default=REPORTS_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_pipeline(
        raw_dir=args.raw_dir,
        processed_dir=args.processed_dir,
        rejected_dir=args.rejected_dir,
        curated_dir=args.curated_dir,
        reports_dir=args.reports_dir,
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
