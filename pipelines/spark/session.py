from __future__ import annotations

from pyspark.sql import SparkSession


def build_spark_session(*, app_name: str) -> SparkSession:
    """Build a Spark session for local or orchestrated pipeline execution."""
    return SparkSession.builder.appName(app_name).master("local[*]").getOrCreate()
