from __future__ import annotations

from datetime import timedelta

from feast import FeatureView, Field, PushSource
from feast.types import String

from feast_repo.entities import article, customer, customer_session
from feast_repo.sources import (
    article_realtime_snapshot_source,
    customer_realtime_snapshot_source,
    session_intent_snapshot_source,
)

session_intent_push_source = PushSource(
    name="session_intent_push_source",
    batch_source=session_intent_snapshot_source,
    description="Push source for short-horizon customer session intent updates.",
)

customer_realtime_push_source = PushSource(
    name="customer_realtime_push_source",
    batch_source=customer_realtime_snapshot_source,
    description="Push source for near-real-time customer behavior aggregates.",
)

article_realtime_push_source = PushSource(
    name="article_realtime_push_source",
    batch_source=article_realtime_snapshot_source,
    description="Push source for near-real-time article demand and catalog updates.",
)

session_intent_features = FeatureView(
    name="session_intent_features",
    entities=[customer_session],
    ttl=timedelta(minutes=30),
    schema=[
        Field(name="recent_viewed_article_ids", dtype=String),
        Field(name="recent_clicked_article_ids", dtype=String),
        Field(name="recent_search_terms", dtype=String),
        Field(name="cart_add_count_30m", dtype=String),
        Field(name="wishlist_add_count_7d", dtype=String),
        Field(name="last_event_time", dtype=String),
    ],
    online=True,
    source=session_intent_push_source,
    tags={"freshness_target_seconds": "60"},
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


def online_feature_views() -> list:
    """Return the Feast online feature views in serving-priority order."""
    return [
        session_intent_features,
        customer_realtime_features,
        article_realtime_features,
    ]
