from __future__ import annotations

from datetime import timedelta

from feast import FeatureView, Field, PushSource
from feast.types import String

from feast_repo.entities import customer
from feast_repo.sources import customer_realtime_snapshot_source

customer_realtime_push_source = PushSource(
    name="customer_realtime_push_source",
    batch_source=customer_realtime_snapshot_source,
    description="Push source for near-real-time customer behavior aggregates.",
)

customer_realtime_features = FeatureView(
    name="customer_realtime_features",
    entities=[customer],
    ttl=timedelta(days=30),
    schema=[
        Field(name="purchase_count_30d_rt", dtype=String),
        Field(name="purchase_count_7d_rt", dtype=String),
        Field(name="days_since_last_purchase_rt", dtype=String),
        Field(name="cart_add_count_7d_rt", dtype=String),
        Field(name="wishlist_add_count_30d_rt", dtype=String),
    ],
    online=True,
    source=customer_realtime_push_source,
    tags={"freshness_target_seconds": "300"},
)
