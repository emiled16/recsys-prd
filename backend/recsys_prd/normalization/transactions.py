from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

from recsys_prd.io.csv_ops import read_csv_rows
from recsys_prd.normalization.cleaning import clean_identifier, clean_numeric_string, clean_string
from recsys_prd.normalization.contracts import TRANSACTION_FIELDS


def normalize_transactions(raw_transactions_path: Path) -> list[dict[str, str]]:
    """Normalize raw transaction rows into deterministic event rows."""
    rows = read_csv_rows(raw_transactions_path)
    normalized: list[dict[str, str]] = []
    for row in rows:
        event_time = _normalize_event_time(row.get("t_dat"))
        customer_id = clean_identifier(row.get("customer_id"))
        article_id = clean_identifier(row.get("article_id"))
        price = clean_numeric_string(row.get("price"))
        sales_channel_id = clean_string(row.get("sales_channel_id"))
        normalized.append(
            {
                "event_id": _build_event_id(
                    event_time=event_time,
                    customer_id=customer_id,
                    article_id=article_id,
                    price=price,
                    sales_channel_id=sales_channel_id,
                ),
                "event_time": event_time,
                "customer_id": customer_id,
                "article_id": article_id,
                "price": price,
                "sales_channel_id": sales_channel_id,
            }
        )
    return normalized


def transaction_schema() -> list[str]:
    return TRANSACTION_FIELDS.copy()


def _normalize_event_time(value: str | None) -> str:
    normalized = clean_string(value)
    if not normalized:
        return ""
    return datetime.strptime(normalized, "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00Z")


def _build_event_id(
    *,
    event_time: str,
    customer_id: str,
    article_id: str,
    price: str,
    sales_channel_id: str,
) -> str:
    raw_key = "|".join([event_time, customer_id, article_id, price, sales_channel_id])
    return hashlib.sha1(raw_key.encode("utf-8")).hexdigest()
