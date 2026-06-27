from __future__ import annotations

import os
import sys
from collections.abc import Sequence

from src.pipeline import SOURCE_S3, run_pipeline

GLUE_ENV_KEYS = (
    "S3_BUCKET",
    "S3_RAW_PREFIX",
    "S3_CURATED_CSV_PREFIX",
    "S3_CURATED_PARQUET_PREFIX",
)


def parse_glue_args(argv: Sequence[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    index = 0
    while index < len(argv):
        token = argv[index]
        if token.startswith("--"):
            key = token[2:]
            if key in GLUE_ENV_KEYS:
                if index + 1 >= len(argv) or argv[index + 1].startswith("--"):
                    raise ValueError(f"Missing value for Glue argument: {token}")
                parsed[key] = argv[index + 1]
                index += 2
                continue
        index += 1
    return parsed


def apply_environment(args: dict[str, str]) -> None:
    for key, value in args.items():
        cleaned_value = value.strip()
        if cleaned_value:
            os.environ[key] = cleaned_value


def main(argv: Sequence[str] | None = None) -> None:
    glue_args = parse_glue_args(argv if argv is not None else sys.argv[1:])
    apply_environment(glue_args)

    result = run_pipeline(
        source=SOURCE_S3,
        upload_curated=True,
        write_files=False,
    )
    totals = result.summary["totals"]
    print(
        "Glue pipeline complete: "
        f"{totals['accepted_rows']} accepted, "
        f"{totals['rejected_rows']} rejected, "
        f"{totals['raw_rows']} raw rows."
    )


if __name__ == "__main__":
    main()
