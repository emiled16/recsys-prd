from __future__ import annotations

from pathlib import Path

from recsys_prd.io.csv_ops import write_csv_rows
from recsys_prd.io.json_ops import write_json
from recsys_prd.normalization.profile import build_profile


def write_dataset_bundle(
    *,
    dataset_dir: Path,
    dataset_filename: str,
    fieldnames: list[str],
    rows: list[dict[str, str]],
    primary_key: str,
) -> Path:
    """Write a normalized dataset together with schema and profile metadata."""
    dataset_path = dataset_dir / dataset_filename
    write_csv_rows(dataset_path, fieldnames, rows)
    profile = build_profile(rows, fieldnames=fieldnames, primary_key=primary_key)
    write_json(dataset_dir / "schema.json", {"fields": fieldnames, "primary_key": primary_key})
    write_json(dataset_dir / "profile.json", profile)
    return dataset_path
