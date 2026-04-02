from __future__ import annotations

from pathlib import Path

from recsys_prd.normalization.customers import customer_schema, normalize_customers
from recsys_prd.normalization.products import (
    build_product_images_manifest,
    image_schema,
    normalize_products,
    product_schema,
)
from recsys_prd.normalization.transactions import normalize_transactions, transaction_schema
from recsys_prd.normalization.writer import write_dataset_bundle
from recsys_prd.paths import NORMALIZED_ROOT, RAW_HM_ROOT


def run_hm_normalization(
    *,
    raw_root: Path = RAW_HM_ROOT,
    normalized_root: Path = NORMALIZED_ROOT,
) -> dict[str, Path]:
    """Normalize raw H&M datasets into the local normalized layer."""
    products_rows = normalize_products(raw_root / "articles" / "articles.csv")
    image_rows = build_product_images_manifest(raw_root / "images")
    customers_rows = normalize_customers(raw_root / "customers" / "customers.csv")
    transactions_rows = normalize_transactions(raw_root / "transactions" / "transactions_train.csv")

    return {
        "products": write_dataset_bundle(
            dataset_dir=normalized_root / "products",
            dataset_filename="products_normalized.csv",
            fieldnames=product_schema(),
            rows=products_rows,
            primary_key="article_id",
        ),
        "images": write_dataset_bundle(
            dataset_dir=normalized_root / "images",
            dataset_filename="product_images_manifest.csv",
            fieldnames=image_schema(),
            rows=image_rows,
            primary_key="image_path",
        ),
        "customers": write_dataset_bundle(
            dataset_dir=normalized_root / "customers",
            dataset_filename="customers_normalized.csv",
            fieldnames=customer_schema(),
            rows=customers_rows,
            primary_key="customer_id",
        ),
        "transactions": write_dataset_bundle(
            dataset_dir=normalized_root / "transactions",
            dataset_filename="transactions_normalized.csv",
            fieldnames=transaction_schema(),
            rows=transactions_rows,
            primary_key="event_id",
        ),
    }
