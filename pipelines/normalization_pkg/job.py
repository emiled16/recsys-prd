from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings

from pipelines.normalization_pkg.customers import (
    customer_schema,
    normalize_customer_rows,
    normalize_customers,
)
from pipelines.normalization_pkg.products import (
    build_product_images_manifest,
    image_schema,
    normalize_product_rows,
    normalize_products,
    product_schema,
)
from pipelines.normalization_pkg.transactions import (
    normalize_transaction_rows,
    normalize_transactions,
    transaction_schema,
)
from pipelines.normalization_pkg.writer import write_dataset_bundle
from pipelines.spark.io import read_csv_dataset
from pipelines.spark.session import build_spark_session


def run_hm_normalization(
    *,
    raw_root: Path | None = None,
    normalized_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path]:
    """Normalize raw H&M datasets into the local normalized layer."""
    settings = settings or get_app_settings()
    raw_root = raw_root or settings.paths.raw_hm_root
    normalized_root = normalized_root or settings.paths.normalized_root
    spark = _maybe_build_spark_session(settings)
    if spark is None:
        products_rows = normalize_products(raw_root / "articles" / "articles.csv")
        customers_rows = normalize_customers(raw_root / "customers" / "customers.csv")
        transactions_rows = normalize_transactions(raw_root / "transactions" / "transactions_train.csv")
    else:
        products_rows = normalize_product_rows(
            _spark_rows(read_csv_dataset(spark, raw_root / "articles" / "articles.csv"))
        )
        customers_rows = normalize_customer_rows(
            _spark_rows(read_csv_dataset(spark, raw_root / "customers" / "customers.csv"))
        )
        transactions_rows = normalize_transaction_rows(
            _spark_rows(read_csv_dataset(spark, raw_root / "transactions" / "transactions_train.csv"))
        )
    image_rows = build_product_images_manifest(raw_root / "images")

    return {
        "products": write_dataset_bundle(
            dataset_dir=normalized_root / "products",
            dataset_filename="products_normalized.parquet",
            fieldnames=product_schema(),
            rows=products_rows,
            primary_key="article_id",
            spark=spark,
        ),
        "images": write_dataset_bundle(
            dataset_dir=normalized_root / "images",
            dataset_filename="product_images_manifest.parquet",
            fieldnames=image_schema(),
            rows=image_rows,
            primary_key="image_path",
            spark=spark,
        ),
        "customers": write_dataset_bundle(
            dataset_dir=normalized_root / "customers",
            dataset_filename="customers_normalized.parquet",
            fieldnames=customer_schema(),
            rows=customers_rows,
            primary_key="customer_id",
            spark=spark,
        ),
        "transactions": write_dataset_bundle(
            dataset_dir=normalized_root / "transactions",
            dataset_filename="transactions_normalized.parquet",
            fieldnames=transaction_schema(),
            rows=transactions_rows,
            primary_key="event_id",
            spark=spark,
        ),
    }


def _spark_rows(frame) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in frame.collect():
        rows.append({key: "" if value is None else str(value) for key, value in row.asDict().items()})
    return rows


def _maybe_build_spark_session(settings: AppSettings):
    """Return a Spark session when the local runtime is available, otherwise fall back cleanly."""
    try:
        return build_spark_session(app_name="recsys-prd-normalization", settings=settings)
    except Exception:
        return None
