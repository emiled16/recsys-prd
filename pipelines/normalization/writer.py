from __future__ import annotations

from pathlib import Path

from recsys_prd.io.json_ops import write_json
from recsys_prd.io.tabular_ops import write_dual_tabular_outputs

from pipelines.normalization.profile import build_profile


def write_dataset_bundle(
    *,
    dataset_dir: Path,
    dataset_filename: str,
    fieldnames: list[str],
    rows: list[dict[str, str]],
    primary_key: str,
) -> Path:
    """Write a normalized dataset together with schema and profile metadata."""
    dataset_path, csv_path = write_dual_tabular_outputs(
        dataset_dir=dataset_dir,
        dataset_filename=dataset_filename,
        fieldnames=fieldnames,
        rows=rows,
    )
    profile = build_profile(rows, fieldnames=fieldnames, primary_key=primary_key)
    write_json(
        dataset_dir / "schema.json",
        {
            "fields": fieldnames,
            "primary_key": primary_key,
            "primary_format": "parquet",
            "compatibility_formats": ["csv"],
            "dataset_path": str(dataset_path),
            "compatibility_csv_path": str(csv_path),
        },
    )
    write_json(dataset_dir / "profile.json", profile)
    return dataset_path
