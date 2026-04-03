from __future__ import annotations

from feast_repo.online_view_defs.article_realtime import (
    article_realtime_features,
    article_realtime_push_source,
)
from feast_repo.online_view_defs.customer_realtime import (
    customer_realtime_features,
    customer_realtime_push_source,
)
from feast_repo.online_view_defs.session_intent import (
    session_intent_features,
    session_intent_push_source,
)

__all__ = [
    "session_intent_push_source",
    "customer_realtime_push_source",
    "article_realtime_push_source",
    "session_intent_features",
    "customer_realtime_features",
    "article_realtime_features",
    "online_feature_views",
]


def online_feature_views() -> list:
    """Return the Feast online feature views in serving-priority order."""
    return [
        session_intent_features,
        customer_realtime_features,
        article_realtime_features,
    ]
