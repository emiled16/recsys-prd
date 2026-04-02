from __future__ import annotations

from pathlib import Path

from recsys_prd.io.csv_ops import read_csv_rows
from recsys_prd.normalization.cleaning import clean_category, clean_identifier, clean_string
from recsys_prd.normalization.contracts import IMAGE_FIELDS, PRODUCT_FIELDS


def normalize_products(raw_articles_path: Path) -> list[dict[str, str]]:
    """Normalize raw article rows into the product contract."""
    rows = read_csv_rows(raw_articles_path)
    normalized: list[dict[str, str]] = []
    for row in rows:
        normalized.append(
            {
                "article_id": clean_identifier(row.get("article_id")),
                "product_code": clean_identifier(row.get("product_code")),
                "prod_name": clean_string(row.get("prod_name")),
                "product_type_name": clean_category(row.get("product_type_name")),
                "product_group_name": clean_category(row.get("product_group_name")),
                "graphical_appearance_name": clean_category(row.get("graphical_appearance_name")),
                "colour_group_name": clean_category(row.get("colour_group_name")),
                "perceived_colour_value_name": clean_category(row.get("perceived_colour_value_name")),
                "perceived_colour_master_name": clean_category(
                    row.get("perceived_colour_master_name")
                ),
                "department_name": clean_category(row.get("department_name")),
                "index_name": clean_category(row.get("index_name")),
                "index_group_name": clean_category(row.get("index_group_name")),
                "section_name": clean_category(row.get("section_name")),
                "garment_group_name": clean_category(row.get("garment_group_name")),
                "detail_desc": clean_string(row.get("detail_desc")),
            }
        )
    return normalized


def build_product_images_manifest(images_root: Path) -> list[dict[str, str]]:
    """Build a normalized image manifest from ingested product assets."""
    manifest: list[dict[str, str]] = []
    for path in sorted(image_path for image_path in images_root.rglob("*") if image_path.is_file()):
        manifest.append(
            {
                "article_id": clean_identifier(path.stem),
                "image_path": str(path),
                "image_kind": "product",
            }
        )
    return manifest


def product_schema() -> list[str]:
    return PRODUCT_FIELDS.copy()


def image_schema() -> list[str]:
    return IMAGE_FIELDS.copy()
