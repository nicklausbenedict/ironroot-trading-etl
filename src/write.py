from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from .config import PROCESSED_DIR, REJECTED_DIR, REPORTS_DIR
except ImportError:  # pragma: no cover - supports `python src/pipeline.py`
    from config import PROCESSED_DIR, REJECTED_DIR, REPORTS_DIR


def write_outputs(
    accepted: dict[str, pd.DataFrame],
    rejected: dict[str, pd.DataFrame],
    summary: dict[str, Any],
    processed_dir: Path = PROCESSED_DIR,
    rejected_dir: Path = REJECTED_DIR,
    reports_dir: Path = REPORTS_DIR,
) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    rejected_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    for table_name, df in accepted.items():
        df.to_csv(processed_dir / f"{table_name}.csv", index=False)

    for table_name, df in rejected.items():
        df.to_csv(rejected_dir / f"{table_name}_rejected.csv", index=False)

    with (reports_dir / "validation_summary.json").open("w", encoding="utf-8") as report_file:
        json.dump(summary, report_file, indent=2, sort_keys=True)
