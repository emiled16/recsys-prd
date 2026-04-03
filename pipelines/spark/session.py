from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings


def build_spark_session(
    *,
    app_name: str | None = None,
    settings: AppSettings | None = None,
    extra_configs: dict[str, str] | None = None,
):
    """Build a Spark session for local or orchestrated pipeline execution."""
    from pyspark.sql import SparkSession

    settings = settings or get_app_settings()
    spark_settings = settings.spark
    builder = (
        SparkSession.builder.appName(app_name or spark_settings.app_name)
        .master(spark_settings.master)
        .config("spark.sql.warehouse.dir", str(_resolve_warehouse_dir(settings)))
        .config("spark.driver.bindAddress", spark_settings.driver_bind_address)
        .config("spark.ui.enabled", str(spark_settings.ui_enabled).lower())
        .config("spark.sql.shuffle.partitions", str(spark_settings.shuffle_partitions))
    )
    for key, value in (extra_configs or {}).items():
        builder = builder.config(key, value)
    return builder.getOrCreate()


def _resolve_warehouse_dir(settings: AppSettings) -> Path:
    warehouse_dir = Path(settings.spark.warehouse_dir)
    if warehouse_dir.is_absolute():
        return warehouse_dir
    return settings.paths.project_root / warehouse_dir
