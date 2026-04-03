from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from pipelines.spark.io import (
    read_csv_dataset,
    read_parquet_dataset,
    write_parquet_dataset,
    write_string_rows_as_parquet,
)
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


def test_read_csv_dataset_configures_header_and_schema_flags() -> None:
    spark = MagicMock()
    reader = spark.read.option.return_value.option.return_value
    reader.csv.return_value = "frame"

    frame = read_csv_dataset(spark, Path("/tmp/input.csv"), header=False, infer_schema=True)

    assert frame == "frame"
    spark.read.option.assert_any_call("header", "false")
    spark.read.option.return_value.option.assert_called_once_with("inferSchema", "true")
    reader.csv.assert_called_once_with("/tmp/input.csv")


def test_read_parquet_dataset_reads_expected_path() -> None:
    spark = MagicMock()
    spark.read.parquet.return_value = "frame"

    frame = read_parquet_dataset(spark, Path("/tmp/dataset.parquet"))

    assert frame == "frame"
    spark.read.parquet.assert_called_once_with("/tmp/dataset.parquet")


def test_write_parquet_dataset_writes_overwrite_mode(tmp_path: Path) -> None:
    frame = MagicMock()
    writer = frame.write.mode.return_value
    path = tmp_path / "dataset.parquet"

    returned_path = write_parquet_dataset(frame, path)

    assert returned_path == path
    frame.write.mode.assert_called_once_with("overwrite")
    writer.parquet.assert_called_once_with(str(path))


def test_write_string_rows_as_parquet_orders_columns() -> None:
    spark = MagicMock()
    frame = MagicMock()
    selected_frame = MagicMock()
    spark.createDataFrame.return_value = frame
    frame.select.return_value = selected_frame

    path = Path("/tmp/normalized/products.parquet")
    returned_path = write_string_rows_as_parquet(
        spark,
        path=path,
        fieldnames=["article_id", "product_name"],
        rows=[{"product_name": "Shirt", "article_id": "1"}],
    )

    assert returned_path == path
    spark.createDataFrame.assert_called_once_with(
        [{"article_id": "1", "product_name": "Shirt"}]
    )
    frame.select.assert_called_once_with("article_id", "product_name")
    selected_frame.write.mode.assert_called_once_with("overwrite")
    selected_frame.write.mode.return_value.parquet.assert_called_once_with(str(path))
