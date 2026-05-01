from __future__ import annotations

from collections.abc import Hashable
from collections import Counter

import pandas as pd

try:
    from .config import (
        FOREIGN_KEYS,
        NONNEGATIVE_COLUMNS,
        POSITIVE_COLUMNS,
        REJECTION_REASONS_COLUMN,
        TABLE_SPECS,
        VALIDATION_STATUS_COLUMN,
    )
    from .models import ForeignKeySpec, TableSpec, ValidationResult
except ImportError:  # pragma: no cover - supports `python src/pipeline.py`
    from config import (
        FOREIGN_KEYS,
        NONNEGATIVE_COLUMNS,
        POSITIVE_COLUMNS,
        REJECTION_REASONS_COLUMN,
        TABLE_SPECS,
        VALIDATION_STATUS_COLUMN,
    )
    from models import ForeignKeySpec, TableSpec, ValidationResult


ReasonMap = dict[Hashable, list[str]]


def validate_all_tables(
    tables: dict[str, pd.DataFrame],
    specs: dict[str, TableSpec] = TABLE_SPECS,
    foreign_keys: tuple[ForeignKeySpec, ...] = FOREIGN_KEYS,
) -> ValidationResult:
    reasons = {table_name: _empty_reasons(df) for table_name, df in tables.items()}

    for table_name, df in tables.items():
        spec = specs[table_name]
        _validate_required_fields(df, spec, reasons[table_name])
        _validate_duplicate_primary_key(df, spec, reasons[table_name])
        _validate_type_conversions(df, spec, reasons[table_name])
        _validate_domain_rules(table_name, df, reasons[table_name])

    _validate_foreign_keys(tables, foreign_keys, reasons)

    accepted: dict[str, pd.DataFrame] = {}
    rejected: dict[str, pd.DataFrame] = {}
    issue_counts: dict[str, dict[str, int]] = {}

    for table_name, df in tables.items():
        row_reasons = reasons[table_name]
        reject_mask = df.index.to_series().map(lambda index: bool(row_reasons[index]))

        accepted_df = df.loc[~reject_mask].copy()
        accepted_df[VALIDATION_STATUS_COLUMN] = "accepted"

        rejected_df = df.loc[reject_mask].copy()
        if not rejected_df.empty:
            rejected_df[VALIDATION_STATUS_COLUMN] = "rejected"
            rejected_df[REJECTION_REASONS_COLUMN] = rejected_df.index.to_series().map(
                lambda index: ";".join(row_reasons[index])
            )
        else:
            rejected_df[VALIDATION_STATUS_COLUMN] = pd.Series(dtype="string")
            rejected_df[REJECTION_REASONS_COLUMN] = pd.Series(dtype="string")

        accepted[table_name] = accepted_df
        rejected[table_name] = rejected_df
        issue_counts[table_name] = dict(Counter(reason for values in row_reasons.values() for reason in values))

    return ValidationResult(accepted=accepted, rejected=rejected, issue_counts=issue_counts)


def _empty_reasons(df: pd.DataFrame) -> ReasonMap:
    return {index: [] for index in df.index}


def _add_reason(reasons: ReasonMap, mask: pd.Series, reason: str) -> None:
    for index, is_invalid in mask.fillna(False).items():
        if bool(is_invalid) and reason not in reasons[index]:
            reasons[index].append(reason)


def _validate_required_fields(df: pd.DataFrame, spec: TableSpec, reasons: ReasonMap) -> None:
    for column in spec.required_columns:
        values = df[column]
        if _is_datetime_like(values):
            missing = values.isna()
        else:
            missing = values.isna() | (values.astype("string").str.strip() == "")
        _add_reason(reasons, missing, "missing_required_id" if column.endswith("Id") else "missing_required_value")


def _validate_duplicate_primary_key(df: pd.DataFrame, spec: TableSpec, reasons: ReasonMap) -> None:
    valid_key = df[spec.primary_key].astype("string").str.strip() != ""
    duplicates = df[spec.primary_key].duplicated(keep=False) & valid_key
    _add_reason(reasons, duplicates, "duplicate_primary_key")


def _validate_type_conversions(df: pd.DataFrame, spec: TableSpec, reasons: ReasonMap) -> None:
    for column in (*spec.integer_columns, *spec.float_columns, *spec.boolean_columns):
        _add_reason(reasons, df[column].isna(), "invalid_type")

    for column in spec.date_columns:
        if column in spec.required_columns:
            _add_reason(reasons, pd.Series(df[column].isna(), index=df.index), "invalid_type")


def _validate_domain_rules(table_name: str, df: pd.DataFrame, reasons: ReasonMap) -> None:
    for column in NONNEGATIVE_COLUMNS.get(table_name, ()):
        _add_reason(reasons, df[column].notna() & (df[column] < 0), "invalid_domain")

    for column in POSITIVE_COLUMNS.get(table_name, ()):
        _add_reason(reasons, df[column].notna() & (df[column] <= 0), "invalid_domain")

    if table_name == "suppliers":
        score = df["ReliabilityScore"]
        _add_reason(reasons, score.notna() & ((score < 0) | (score > 1)), "invalid_domain")

    if table_name == "purchase_orders":
        expected_before_order = (
            df["ExpectedDeliveryDate"].notna()
            & df["OrderDate"].notna()
            & (df["ExpectedDeliveryDate"] < df["OrderDate"])
        )
        actual_before_order = (
            df["ActualDeliveryDate"].notna()
            & df["OrderDate"].notna()
            & (df["ActualDeliveryDate"] < df["OrderDate"])
        )
        _add_reason(reasons, expected_before_order | actual_before_order, "invalid_domain")


def _validate_foreign_keys(
    tables: dict[str, pd.DataFrame],
    foreign_keys: tuple[ForeignKeySpec, ...],
    reasons: dict[str, ReasonMap],
) -> None:
    for fk in foreign_keys:
        reference_values = set(
            tables[fk.reference_table][fk.reference_column]
            .astype("string")
            .str.strip()
            .dropna()
        )
        values = tables[fk.table][fk.column].astype("string").str.strip()
        invalid = (values != "") & ~values.isin(reference_values)
        _add_reason(reasons[fk.table], invalid, "invalid_foreign_key")


def _is_datetime_like(values: pd.Series) -> bool:
    return pd.api.types.is_datetime64_any_dtype(values)
