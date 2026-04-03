"""Shared Spark runtime helpers for pipeline-owned jobs."""

from pipelines.spark.session import build_spark_session

__all__ = ["build_spark_session"]
