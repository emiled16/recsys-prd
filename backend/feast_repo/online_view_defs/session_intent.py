from __future__ import annotations

from datetime import timedelta

from feast import FeatureView, Field, PushSource
from feast.types import String

from feast_repo.entities import customer_session
from feast_repo.sources import session_intent_snapshot_source

session_intent_push_source = PushSource(
    name="session_intent_push_source",
    batch_source=session_intent_snapshot_source,
    description="Push source for short-horizon customer session intent updates.",
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
