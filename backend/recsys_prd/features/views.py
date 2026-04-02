from __future__ import annotations

from recsys_prd.features.contracts import FeatureView


CUSTOMER_PROFILE_VIEW = FeatureView(
    name="customer_profile_features",
    entity_name="customer",
    source_datasets=("customers_normalized",),
    timestamp_field=None,
    feature_fields=(
        "age",
        "club_member_status",
        "fashion_news_frequency",
        "has_fn_flag",
        "has_active_flag",
    ),
    description="Static or slowly changing customer profile features.",
)

ARTICLE_CATALOG_VIEW = FeatureView(
    name="article_catalog_features",
    entity_name="article",
    source_datasets=("products_normalized", "product_images_manifest"),
    timestamp_field=None,
    feature_fields=(
        "product_type_name",
        "product_group_name",
        "colour_group_name",
        "department_name",
        "index_group_name",
        "has_detail_desc",
        "has_image",
    ),
    description="Structured product and image-availability features for batch use.",
)

CUSTOMER_ACTIVITY_VIEW = FeatureView(
    name="customer_activity_features",
    entity_name="customer",
    source_datasets=("transactions_normalized",),
    timestamp_field="event_time",
    feature_fields=(
        "purchase_count_30d",
        "purchase_count_all_time",
        "days_since_last_purchase",
        "distinct_articles_purchased_30d",
        "avg_purchase_price_30d",
    ),
    description="Time-aware customer aggregates for training and batch scoring.",
)

ARTICLE_DEMAND_VIEW = FeatureView(
    name="article_demand_features",
    entity_name="article",
    source_datasets=("transactions_normalized",),
    timestamp_field="event_time",
    feature_fields=(
        "purchase_count_7d",
        "purchase_count_30d",
        "unique_customers_30d",
        "avg_article_price_30d",
        "days_since_last_article_purchase",
    ),
    description="Time-aware article demand and popularity features.",
)

CUSTOMER_ARTICLE_AFFINITY_VIEW = FeatureView(
    name="customer_article_affinity_features",
    entity_name="customer_article",
    source_datasets=("transactions_normalized",),
    timestamp_field="event_time",
    feature_fields=(
        "historical_purchase_count",
        "days_since_last_purchase",
        "has_purchased_before",
        "last_purchase_price",
    ),
    description="Historical affinity features for a customer-article pair.",
)
