from __future__ import annotations

from datetime import timedelta

from feast import FeatureView, Field, PushSource
from feast.types import String

from feast_repo.entities import article
from feast_repo.sources import article_realtime_snapshot_source

article_realtime_push_source = PushSource(
    name="article_realtime_push_source",
    batch_source=article_realtime_snapshot_source,
    description="Push source for near-real-time article demand and catalog updates.",
)

article_realtime_features = FeatureView(
    name="article_realtime_features",
    entities=[article],
    ttl=timedelta(days=7),
    schema=[
        Field(name="purchase_count_1d_rt", dtype=String),
        Field(name="purchase_count_7d_rt", dtype=String),
        Field(name="inventory_level_rt", dtype=String),
        Field(name="is_in_stock_rt", dtype=String),
        Field(name="current_price_rt", dtype=String),
        Field(name="minutes_since_last_catalog_update", dtype=String),
    ],
    online=True,
    source=article_realtime_push_source,
    tags={"freshness_target_seconds": "120"},
)
