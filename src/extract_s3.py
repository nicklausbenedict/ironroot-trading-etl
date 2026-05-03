from __future__ import annotations

import os
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

import pandas as pd

try:
    from .config import AUDIT_COLUMNS, TABLE_SPECS
    from .extract import SourceDataError
    from .models import TableSpec
except ImportError:  # pragma: no cover - supports `python src/pipeline.py`
    from config import AUDIT_COLUMNS, TABLE_SPECS
    from extract import SourceDataError
    from models import TableSpec


def load_s3_table(
    spec: TableSpec,
    bucket: str,
    prefix: str = "",
    ingested_at: datetime | None = None,
    s3_client: Any | None = None,
) -> pd.DataFrame:
    if not bucket:
        raise SourceDataError("S3 source requires S3_BUCKET to be set.")

    key = build_s3_key(prefix, spec.filename)
    client = s3_client or create_s3_client()

    try:
        response = client.get_object(Bucket=bucket, Key=key)
    except Exception as exc:  # pragma: no cover - exact boto3 exception types depend on runtime client
        raise SourceDataError(f"Unable to read s3://{bucket}/{key}: {exc}") from exc

    body = response["Body"].read()
    df = pd.read_csv(BytesIO(body), dtype="string", keep_default_na=False)
    actual_columns = tuple(df.columns)
    if actual_columns != spec.columns:
        raise SourceDataError(
            f"Unexpected schema for s3://{bucket}/{key}. "
            f"Expected {list(spec.columns)}, found {list(actual_columns)}."
        )

    timestamp = (ingested_at or datetime.now(UTC)).isoformat()
    df[AUDIT_COLUMNS[0]] = f"s3://{bucket}/{key}"
    df[AUDIT_COLUMNS[1]] = range(2, len(df) + 2)
    df[AUDIT_COLUMNS[2]] = timestamp
    return df


def load_all_s3_tables(
    bucket: str,
    prefix: str = "",
    specs: dict[str, TableSpec] = TABLE_SPECS,
    ingested_at: datetime | None = None,
    s3_client: Any | None = None,
) -> dict[str, pd.DataFrame]:
    if not bucket:
        raise SourceDataError("S3 source requires S3_BUCKET to be set.")

    timestamp = ingested_at or datetime.now(UTC)
    client = s3_client or create_s3_client()
    return {
        table_name: load_s3_table(
            spec,
            bucket=bucket,
            prefix=prefix,
            ingested_at=timestamp,
            s3_client=client,
        )
        for table_name, spec in specs.items()
    }


def build_s3_key(prefix: str, filename: str) -> str:
    normalized_prefix = prefix.strip("/")
    if not normalized_prefix:
        return filename
    return f"{normalized_prefix}/{filename}"


def create_s3_client() -> Any:
    try:
        import boto3
    except ImportError as exc:
        raise SourceDataError("boto3 is required for S3 source mode. Install dependencies from requirements.txt.") from exc

    profile_name = os.getenv("AWS_PROFILE", "").strip()
    if profile_name:
        return boto3.Session(profile_name=profile_name).client("s3")
    return boto3.client("s3")
