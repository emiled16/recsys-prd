from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def read_parquet_rows(path: Path) -> list[dict[str, str]]:
    """Read a Parquet file into string-keyed rows."""
    table = pq.read_table(path)
    return [
        {key: "" if value is None else str(value) for key, value in row.items()}
        for row in table.to_pylist()
    ]


def write_parquet_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    """Write rows to Parquet using a string-only schema for migration compatibility."""
    path.parent.mkdir(parents=True, exist_ok=True)
    arrays = [
        pa.array([row.get(field, "") for row in rows], type=pa.string())
        for field in fieldnames
    ]
    table = pa.Table.from_arrays(arrays, names=fieldnames)
    pq.write_table(table, path)
