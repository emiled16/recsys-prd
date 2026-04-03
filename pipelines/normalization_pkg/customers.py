from __future__ import annotations

from pathlib import Path

from recsys_prd.io.csv_ops import read_csv_rows

from pipelines.normalization_pkg.cleaning import (
    clean_category,
    clean_identifier,
    clean_numeric_string,
    clean_string,
)
from pipelines.normalization_pkg.contracts import CUSTOMER_FIELDS


def normalize_customers(raw_customers_path: Path) -> list[dict[str, str]]:
    """Normalize raw customer rows into the customer contract."""
    return normalize_customer_rows(read_csv_rows(raw_customers_path))


def normalize_customer_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Normalize raw customer rows already loaded into memory."""
    normalized: list[dict[str, str]] = []
    for row in rows:
        normalized.append(
            {
                "customer_id": clean_identifier(row.get("customer_id")),
                "fn_flag": clean_string(row.get("FN")),
                "active_flag": clean_string(row.get("Active")),
                "club_member_status": clean_category(row.get("club_member_status")),
                "fashion_news_frequency": clean_category(row.get("fashion_news_frequency")),
                "age": clean_numeric_string(row.get("age")),
                "postal_code": clean_string(row.get("postal_code")),
            }
        )
    return normalized


def customer_schema() -> list[str]:
    return CUSTOMER_FIELDS.copy()
