from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class TableSpec:
    name: str
    filename: str
    primary_key: str
    columns: tuple[str, ...]
    required_columns: tuple[str, ...]
    string_columns: tuple[str, ...] = ()
    date_columns: tuple[str, ...] = ()
    integer_columns: tuple[str, ...] = ()
    float_columns: tuple[str, ...] = ()
    boolean_columns: tuple[str, ...] = ()

    @property
    def path_name(self) -> str:
        return Path(self.filename).stem


@dataclass(frozen=True)
class ForeignKeySpec:
    table: str
    column: str
    reference_table: str
    reference_column: str


@dataclass
class ValidationResult:
    accepted: dict[str, pd.DataFrame]
    rejected: dict[str, pd.DataFrame]
    issue_counts: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass
class PipelineResult:
    accepted: dict[str, pd.DataFrame]
    rejected: dict[str, pd.DataFrame]
    summary: dict[str, Any]
