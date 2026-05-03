from __future__ import annotations

import json
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

import pandas as pd

try:
    from .curate import CURATED_COLUMNS
    from .extract import SourceDataError
    from .extract_s3 import build_s3_key, create_s3_client
except ImportError:  # pragma: no cover - supports `python src/pipeline.py`
    from curate import CURATED_COLUMNS
    from extract import SourceDataError
    from extract_s3 import build_s3_key, create_s3_client


DEFAULT_CURATED_CSV_PREFIX = "curated/csv/"
DEFAULT_CURATED_PARQUET_PREFIX = "curated/parquet/"
DEFAULT_CURATED_PREFIX = DEFAULT_CURATED_CSV_PREFIX
LATEST_MANIFEST_KEY = "curated/latest_manifest.json"


def upload_curated_tables(
    curated: dict[str, pd.DataFrame],
    bucket: str,
    run_timestamp: datetime,
    csv_prefix: str = DEFAULT_CURATED_CSV_PREFIX,
    parquet_prefix: str = DEFAULT_CURATED_PARQUET_PREFIX,
    curated_prefix: str | None = None,
    s3_client: Any | None = None,
) -> dict[str, Any]:
    if not bucket:
        raise SourceDataError("Curated S3 upload requires S3_BUCKET to be set.")

    client = s3_client or create_s3_client()
    run_id = build_run_id(run_timestamp)
    resolved_csv_prefix = curated_prefix or csv_prefix
    csv_run_prefix = build_s3_key(resolved_csv_prefix, run_id) + "/"
    parquet_run_prefix = build_s3_key(parquet_prefix, run_id) + "/"
    manifest_tables: dict[str, dict[str, Any]] = {}

    for table_name in CURATED_COLUMNS:
        if table_name not in curated:
            raise SourceDataError(f"Missing curated table for S3 upload: {table_name}")

        csv_key = f"{csv_run_prefix}{table_name}.csv"
        parquet_key = f"{parquet_run_prefix}{table_name}.parquet"

        csv_body = curated[table_name].to_csv(index=False).encode("utf-8")
        parquet_buffer = BytesIO()
        curated[table_name].to_parquet(parquet_buffer, index=False, engine="pyarrow")

        client.put_object(Bucket=bucket, Key=csv_key, Body=csv_body, ContentType="text/csv")
        client.head_object(Bucket=bucket, Key=csv_key)
        client.put_object(
            Bucket=bucket,
            Key=parquet_key,
            Body=parquet_buffer.getvalue(),
            ContentType="application/vnd.apache.parquet",
        )
        client.head_object(Bucket=bucket, Key=parquet_key)

        manifest_tables[table_name] = {
            "row_count": len(curated[table_name]),
            "csv": {"key": csv_key},
            "parquet": {"key": parquet_key},
        }

    manifest = {
        "run_id": run_id,
        "generated_at": _as_utc(run_timestamp).isoformat(),
        "bucket": bucket,
        "prefixes": {
            "csv": _normalize_prefix(resolved_csv_prefix),
            "parquet": _normalize_prefix(parquet_prefix),
        },
        "run_prefixes": {
            "csv": csv_run_prefix,
            "parquet": parquet_run_prefix,
        },
        "tables": manifest_tables,
    }
    manifest_body = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    client.put_object(
        Bucket=bucket,
        Key=LATEST_MANIFEST_KEY,
        Body=manifest_body,
        ContentType="application/json",
    )
    return manifest


def build_run_id(run_timestamp: datetime) -> str:
    return _as_utc(run_timestamp).strftime("%Y%m%dT%H%M%SZ")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_prefix(prefix: str) -> str:
    normalized = prefix.strip("/")
    if not normalized:
        return ""
    return f"{normalized}/"
