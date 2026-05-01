from __future__ import annotations

import pandas as pd

try:
    from .config import TABLE_SPECS
    from .models import TableSpec
except ImportError:  # pragma: no cover - supports `python src/pipeline.py`
    from config import TABLE_SPECS
    from models import TableSpec


TRUE_VALUES = {"true", "t", "yes", "y", "1"}
FALSE_VALUES = {"false", "f", "no", "n", "0"}


def clean_table(df: pd.DataFrame, spec: TableSpec) -> pd.DataFrame:
    cleaned = df.copy()

    for column in cleaned.select_dtypes(include=["object", "string"]).columns:
        cleaned[column] = cleaned[column].astype("string").str.strip()

    for column in spec.integer_columns:
        cleaned[column] = pd.to_numeric(cleaned[column].replace("", pd.NA), errors="coerce").astype("Int64")

    for column in spec.float_columns:
        cleaned[column] = pd.to_numeric(cleaned[column].replace("", pd.NA), errors="coerce").astype("Float64")

    for column in spec.date_columns:
        values = cleaned[column].replace("", pd.NA)
        cleaned[column] = pd.to_datetime(values, errors="coerce").dt.date

    for column in spec.boolean_columns:
        cleaned[column] = cleaned[column].map(_parse_boolean).astype("boolean")

    return cleaned


def clean_all_tables(
    tables: dict[str, pd.DataFrame],
    specs: dict[str, TableSpec] = TABLE_SPECS,
) -> dict[str, pd.DataFrame]:
    return {table_name: clean_table(df, specs[table_name]) for table_name, df in tables.items()}


def _parse_boolean(value: str) -> object:
    if pd.isna(value):
        return pd.NA
    normalized = str(value).strip().lower()
    if normalized == "":
        return pd.NA
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return pd.NA
