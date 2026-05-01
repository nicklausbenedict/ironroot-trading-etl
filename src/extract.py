from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

try:
    from .config import AUDIT_COLUMNS, RAW_DIR, TABLE_SPECS
    from .models import TableSpec
except ImportError:  # pragma: no cover - supports `python src/pipeline.py`
    from config import AUDIT_COLUMNS, RAW_DIR, TABLE_SPECS
    from models import TableSpec


class SourceDataError(ValueError):
    """Raised when a required raw file or source schema is invalid."""


def load_table(
    spec: TableSpec,
    raw_dir: Path = RAW_DIR,
    ingested_at: datetime | None = None,
) -> pd.DataFrame:
    source_path = raw_dir / spec.filename
    if not source_path.exists():
        raise SourceDataError(f"Missing required raw file: {source_path}")

    df = pd.read_csv(source_path, dtype="string", keep_default_na=False)
    actual_columns = tuple(df.columns)
    if actual_columns != spec.columns:
        raise SourceDataError(
            f"Unexpected schema for {spec.filename}. "
            f"Expected {list(spec.columns)}, found {list(actual_columns)}."
        )

    timestamp = (ingested_at or datetime.now(UTC)).isoformat()
    df[AUDIT_COLUMNS[0]] = spec.filename
    df[AUDIT_COLUMNS[1]] = range(2, len(df) + 2)
    df[AUDIT_COLUMNS[2]] = timestamp
    return df


def load_all_tables(
    raw_dir: Path = RAW_DIR,
    specs: dict[str, TableSpec] = TABLE_SPECS,
    ingested_at: datetime | None = None,
) -> dict[str, pd.DataFrame]:
    timestamp = ingested_at or datetime.now(UTC)
    return {
        table_name: load_table(spec, raw_dir=raw_dir, ingested_at=timestamp)
        for table_name, spec in specs.items()
    }
