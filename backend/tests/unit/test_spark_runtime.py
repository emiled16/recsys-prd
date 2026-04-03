from __future__ import annotations

from pathlib import Path

from pipelines.spark.session import _resolve_warehouse_dir

from recsys_prd.config import AppSettings, PathSettings, SparkSettings


def test_resolve_warehouse_dir_uses_project_root_for_relative_paths(tmp_path: Path) -> None:
    settings = AppSettings(
        paths=PathSettings(project_root=tmp_path, backend_root=tmp_path / "backend"),
        spark=SparkSettings(warehouse_dir="data/_spark/warehouse"),
    )

    assert _resolve_warehouse_dir(settings) == tmp_path / "data" / "_spark" / "warehouse"


def test_resolve_warehouse_dir_preserves_absolute_paths(tmp_path: Path) -> None:
    warehouse_dir = tmp_path / "spark-warehouse"
    settings = AppSettings(
        paths=PathSettings(project_root=tmp_path, backend_root=tmp_path / "backend"),
        spark=SparkSettings(warehouse_dir=str(warehouse_dir)),
    )

    assert _resolve_warehouse_dir(settings) == warehouse_dir
