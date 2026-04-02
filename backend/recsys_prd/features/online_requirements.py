from __future__ import annotations

from recsys_prd.features.online_contracts import OnlineFeatureRequirement


SESSION_INTENT_REQUIREMENT = OnlineFeatureRequirement(
    name="session_intent_features",
    entity_name="customer_session",
    join_keys=("customer_id", "session_id"),
    freshness_target_seconds=60,
    streaming_inputs=(
        "product_view",
        "product_click",
        "add_to_cart",
        "wishlist_add",
        "search_query",
    ),
    feature_fields=(
        "recent_viewed_article_ids",
        "recent_clicked_article_ids",
        "recent_search_terms",
        "cart_add_count_30m",
        "wishlist_add_count_7d",
        "last_event_time",
    ),
    description="Short-horizon session intent signals for retrieval and ranking.",
)

CUSTOMER_REALTIME_REQUIREMENT = OnlineFeatureRequirement(
    name="customer_realtime_features",
    entity_name="customer",
    join_keys=("customer_id",),
    freshness_target_seconds=300,
    streaming_inputs=("purchase", "add_to_cart", "wishlist_add"),
    feature_fields=(
        "purchase_count_30d_rt",
        "purchase_count_7d_rt",
        "days_since_last_purchase_rt",
        "cart_add_count_7d_rt",
        "wishlist_add_count_30d_rt",
    ),
    description="Near-real-time customer behavior aggregates for ranking.",
)

ARTICLE_REALTIME_REQUIREMENT = OnlineFeatureRequirement(
    name="article_realtime_features",
    entity_name="article",
    join_keys=("article_id",),
    freshness_target_seconds=120,
    streaming_inputs=("purchase", "inventory_update", "price_change", "product_metadata_update"),
    feature_fields=(
        "purchase_count_1d_rt",
        "purchase_count_7d_rt",
        "inventory_level_rt",
        "is_in_stock_rt",
        "current_price_rt",
        "minutes_since_last_catalog_update",
    ),
    description="Near-real-time article demand and catalog-state features.",
)


def online_feature_requirements() -> list[OnlineFeatureRequirement]:
    """Return the online feature requirements in registry order."""
    return [
        SESSION_INTENT_REQUIREMENT,
        CUSTOMER_REALTIME_REQUIREMENT,
        ARTICLE_REALTIME_REQUIREMENT,
    ]
