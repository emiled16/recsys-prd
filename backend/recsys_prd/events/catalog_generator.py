from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from recsys_prd.io.csv_ops import read_csv_rows
from recsys_prd.events.ids import build_event_id


def generate_catalog_events(normalized_root: Path) -> list[dict]:
    """Generate deterministic catalog update events from normalized products."""
    products = read_csv_rows(normalized_root / "products" / "products_normalized.csv")
    events: list[dict] = []
    base_time = datetime(2020, 1, 1, 0, 0, 0)

    for index, product in enumerate(products, start=1):
        article_id = product["article_id"]
        events.extend(
            [
                _catalog_event(
                    event_type="inventory_update",
                    event_time=base_time + timedelta(minutes=index),
                    article_id=article_id,
                    source="synthetic_catalog_updates",
                    ordinal=f"{index}-inventory",
                    inventory_delta=str((index % 5) + 1),
                    inventory_level=str(10 + index),
                ),
                _catalog_event(
                    event_type="price_change",
                    event_time=base_time + timedelta(minutes=index, seconds=10),
                    article_id=article_id,
                    source="synthetic_catalog_updates",
                    ordinal=f"{index}-price",
                    old_price="29.99",
                    new_price="27.99",
                ),
                _catalog_event(
                    event_type="product_metadata_update",
                    event_time=base_time + timedelta(minutes=index, seconds=20),
                    article_id=article_id,
                    source="synthetic_catalog_updates",
                    ordinal=f"{index}-metadata",
                    changed_fields="detail_desc,colour_group_name",
                ),
            ]
        )

    return sorted(events, key=lambda event: (event["event_time"], event["event_id"]))


def _catalog_event(
    *,
    event_type: str,
    event_time: datetime,
    article_id: str,
    source: str,
    ordinal: str,
    inventory_delta: str = "",
    inventory_level: str = "",
    old_price: str = "",
    new_price: str = "",
    changed_fields: str = "",
) -> dict:
    event_time_str = event_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "event_id": build_event_id(event_type, article_id, ordinal),
        "event_type": event_type,
        "event_time": event_time_str,
        "article_id": article_id,
        "inventory_delta": inventory_delta,
        "inventory_level": inventory_level,
        "old_price": old_price,
        "new_price": new_price,
        "changed_fields": changed_fields,
        "source": source,
    }
