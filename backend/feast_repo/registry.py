from __future__ import annotations

from feast_repo.entities import article, customer, customer_session
from feast_repo.offline_view_defs.article_demand import (
    article_demand_base,
    article_demand_features,
)
from feast_repo.offline_view_defs.customer_activity import (
    customer_activity_base,
    customer_activity_features,
)
from feast_repo.offline_view_defs.customer_article_affinity import (
    customer_article_affinity_base,
    customer_article_affinity_features,
)
from feast_repo.offline_view_defs.customer_profile import (
    customer_profile_base,
    customer_profile_features,
)
from feast_repo.offline_view_defs.product_catalog import (
    article_catalog_features,
    product_catalog_base,
)
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
from feast_repo.sources import (
    article_realtime_snapshot_source,
    customer_realtime_snapshot_source,
    point_in_time_training_dataset_source,
    session_intent_snapshot_source,
)


def offline_objects() -> list:
    return [
        customer,
        article,
        customer_session,
        point_in_time_training_dataset_source,
        customer_profile_base,
        product_catalog_base,
        customer_activity_base,
        article_demand_base,
        customer_article_affinity_base,
        customer_profile_features,
        article_catalog_features,
        customer_activity_features,
        article_demand_features,
        customer_article_affinity_features,
    ]


def online_objects() -> list:
    return [
        session_intent_snapshot_source,
        customer_realtime_snapshot_source,
        article_realtime_snapshot_source,
        session_intent_push_source,
        customer_realtime_push_source,
        article_realtime_push_source,
        session_intent_features,
        customer_realtime_features,
        article_realtime_features,
    ]
