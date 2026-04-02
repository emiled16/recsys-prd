from __future__ import annotations

from pathlib import Path

from recsys_prd.io.csv_ops import read_csv_rows


def load_customer_profiles(normalized_root: Path) -> dict[str, dict[str, str]]:
    """Load normalized customer rows keyed by customer_id."""
    rows = read_csv_rows(normalized_root / "customers" / "customers_normalized.csv")
    return {row["customer_id"]: row for row in rows}


def load_product_catalog(normalized_root: Path) -> dict[str, dict[str, str]]:
    """Load normalized product rows keyed by article_id."""
    rows = read_csv_rows(normalized_root / "products" / "products_normalized.csv")
    return {row["article_id"]: row for row in rows}


def load_image_presence(normalized_root: Path) -> dict[str, bool]:
    """Load image-manifest presence keyed by article_id."""
    rows = read_csv_rows(normalized_root / "images" / "product_images_manifest.csv")
    return {row["article_id"]: True for row in rows}


def load_image_manifest(normalized_root: Path) -> dict[str, dict[str, str]]:
    """Load image-manifest rows keyed by article_id."""
    rows = read_csv_rows(normalized_root / "images" / "product_images_manifest.csv")
    return {row["article_id"]: row for row in rows}
