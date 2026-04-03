from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.io.json_ops import write_json
from recsys_prd.io.tabular_ops import read_tabular_rows

from pipelines.normalization.contracts import (
    CUSTOMER_FIELDS,
    IMAGE_FIELDS,
    PRODUCT_FIELDS,
    REQUIRED_CUSTOMER_FIELDS,
    REQUIRED_PRODUCT_FIELDS,
    REQUIRED_TRANSACTION_FIELDS,
    TRANSACTION_FIELDS,
)
from pipelines.spark.parity import build_parity_report


def validate_hm_normalized(
    *,
    normalized_root: Path | None = None,
    reports_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict:
    """Validate normalized outputs for schema, required fields, and key uniqueness."""
    settings = settings or get_app_settings()
    normalized_root = normalized_root or settings.paths.normalized_root
    reports_root = reports_root or settings.paths.reports_root
    checks = {
        "products": _validate_dataset(
            dataset_path=normalized_root / "products" / "products_normalized.parquet",
            expected_fields=PRODUCT_FIELDS,
            primary_key="article_id",
            required_fields=REQUIRED_PRODUCT_FIELDS,
        ),
        "images": _validate_dataset(
            dataset_path=normalized_root / "images" / "product_images_manifest.parquet",
            expected_fields=IMAGE_FIELDS,
            primary_key="image_path",
            required_fields=["article_id", "image_path", "image_kind"],
        ),
        "customers": _validate_dataset(
            dataset_path=normalized_root / "customers" / "customers_normalized.parquet",
            expected_fields=CUSTOMER_FIELDS,
            primary_key="customer_id",
            required_fields=REQUIRED_CUSTOMER_FIELDS,
        ),
        "transactions": _validate_dataset(
            dataset_path=normalized_root / "transactions" / "transactions_normalized.parquet",
            expected_fields=TRANSACTION_FIELDS,
            primary_key="event_id",
            required_fields=REQUIRED_TRANSACTION_FIELDS,
        ),
    }
    result = {
        "ok": all(check["ok"] for check in checks.values()),
        "checks": checks,
    }
    write_json(reports_root / "data_quality" / "hm_normalized_validation.json", result)
    return result


def _validate_dataset(
    *,
    dataset_path: Path,
    expected_fields: list[str],
    primary_key: str,
    required_fields: list[str],
) -> dict:
    rows = read_tabular_rows(dataset_path)
    actual_fields = list(rows[0].keys()) if rows else expected_fields
    schema_ok = actual_fields == expected_fields
    parity = build_parity_report(
        baseline_rows=rows,
        candidate_rows=rows,
        key_field=primary_key,
        required_fields=required_fields,
    )
    row_count_ok = len(rows) > 0
    return {
        "ok": schema_ok and row_count_ok and parity["ok"],
        "dataset_path": str(dataset_path),
        "row_count": len(rows),
        "schema_ok": schema_ok,
        "actual_fields": actual_fields,
        "expected_fields": expected_fields,
        "duplicate_primary_keys": len(parity["duplicate_keys"]),
        "duplicate_primary_key_values": parity["duplicate_keys"],
        "missing_required_fields": parity["missing_required_fields"],
        "order_preserved": parity["order_preserved"],
    }
