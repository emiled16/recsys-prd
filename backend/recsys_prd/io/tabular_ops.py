from __future__ import annotations

from pathlib import Path

from recsys_prd.io.csv_ops import read_csv_rows, write_csv_rows
from recsys_prd.io.parquet_ops import read_parquet_rows, write_parquet_rows


def resolve_tabular_path(path: Path) -> Path:
    """Resolve a CSV or Parquet path across migration-compatible variants."""
    if path.exists():
        return path
    if path.suffix == ".csv":
        candidate = path.with_suffix(".parquet")
        if candidate.exists():
            return candidate
    if path.suffix == ".parquet":
        candidate = path.with_suffix(".csv")
        if candidate.exists():
            return candidate
    return path


def read_tabular_rows(path: Path) -> list[dict[str, str]]:
    """Read a CSV or Parquet dataset using compatibility path resolution."""
    resolved_path = resolve_tabular_path(path)
    if not resolved_path.exists():
        return []
    if resolved_path.suffix == ".parquet":
        return read_parquet_rows(resolved_path)
    return read_csv_rows(resolved_path)


def write_dual_tabular_outputs(
    *,
    dataset_dir: Path,
    dataset_filename: str,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> tuple[Path, Path]:
    """Write Parquet as the primary format and CSV as a compatibility sidecar."""
    dataset_stem = Path(dataset_filename).stem
    parquet_path = dataset_dir / f"{dataset_stem}.parquet"
    csv_path = dataset_dir / f"{dataset_stem}.csv"
    write_parquet_rows(parquet_path, fieldnames, rows)
    write_csv_rows(csv_path, fieldnames, rows)
    return parquet_path, csv_path
