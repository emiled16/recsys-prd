from __future__ import annotations

from pathlib import Path
from typing import Iterable


def read_csv_dataset(spark, path: Path, *, header: bool = True, infer_schema: bool = False):
    """Read a CSV dataset through Spark with explicit header handling."""
    return spark.read.option("header", str(header).lower()).option(
        "inferSchema", str(infer_schema).lower()
    ).csv(str(path))


def read_parquet_dataset(spark, path: Path):
    """Read a Parquet dataset through Spark."""
    return spark.read.parquet(str(path))


def write_parquet_dataset(frame, path: Path, *, mode: str = "overwrite") -> Path:
    """Write a Spark dataframe to Parquet and return the dataset path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.write.mode(mode).parquet(str(path))
    return path


def write_string_rows_as_parquet(
    spark,
    *,
    path: Path,
    fieldnames: list[str],
    rows: Iterable[dict[str, str]],
    mode: str = "overwrite",
) -> Path:
    """Write string-keyed rows to a Parquet dataset through Spark."""
    normalized_rows = [{field: row.get(field, "") for field in fieldnames} for row in rows]
    frame = spark.createDataFrame(normalized_rows)
    ordered_frame = frame.select(*fieldnames)
    return write_parquet_dataset(ordered_frame, path, mode=mode)
