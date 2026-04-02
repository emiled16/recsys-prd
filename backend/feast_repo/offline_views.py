from __future__ import annotations

from datetime import timedelta

import pandas as pd
from feast import FeatureView, Field
from feast.on_demand_feature_view import on_demand_feature_view
from feast.types import String

from feast_repo.entities import article, customer
from feast_repo.sources import (
    point_in_time_training_dataset_source,
)

customer_profile_base = FeatureView(
    name="customer_profile_base",
    entities=[customer],
    ttl=timedelta(days=3650),
    schema=[
        Field(name="customer_age", dtype=String),
        Field(name="customer_club_member_status", dtype=String),
        Field(name="customer_fashion_news_frequency", dtype=String),
        Field(name="customer_has_fn_flag", dtype=String),
        Field(name="customer_has_active_flag", dtype=String),
    ],
    online=False,
    source=point_in_time_training_dataset_source,
)

product_catalog_base = FeatureView(
    name="product_catalog_base",
    entities=[article],
    ttl=timedelta(days=3650),
    schema=[
        Field(name="article_product_type_name", dtype=String),
        Field(name="article_product_group_name", dtype=String),
        Field(name="article_colour_group_name", dtype=String),
        Field(name="article_department_name", dtype=String),
        Field(name="article_index_group_name", dtype=String),
        Field(name="article_has_detail_desc", dtype=String),
        Field(name="article_has_image", dtype=String),
    ],
    online=False,
    source=point_in_time_training_dataset_source,
)

customer_activity_base = FeatureView(
    name="customer_activity_base",
    entities=[customer],
    ttl=timedelta(days=30),
    schema=[
        Field(name="customer_purchase_count_30d", dtype=String),
        Field(name="customer_purchase_count_all_time", dtype=String),
        Field(name="customer_days_since_last_purchase", dtype=String),
        Field(name="customer_distinct_articles_purchased_30d", dtype=String),
        Field(name="customer_avg_purchase_price_30d", dtype=String),
    ],
    online=False,
    source=point_in_time_training_dataset_source,
)

article_demand_base = FeatureView(
    name="article_demand_base",
    entities=[article],
    ttl=timedelta(days=30),
    schema=[
        Field(name="article_purchase_count_7d", dtype=String),
        Field(name="article_purchase_count_30d", dtype=String),
        Field(name="article_unique_customers_30d", dtype=String),
        Field(name="article_avg_article_price_30d", dtype=String),
        Field(name="article_days_since_last_article_purchase", dtype=String),
    ],
    online=False,
    source=point_in_time_training_dataset_source,
)

customer_article_affinity_base = FeatureView(
    name="customer_article_affinity_base",
    entities=[customer, article],
    ttl=timedelta(days=3650),
    schema=[
        Field(name="customer_article_historical_purchase_count", dtype=String),
        Field(name="customer_article_days_since_last_purchase", dtype=String),
        Field(name="customer_article_has_purchased_before", dtype=String),
        Field(name="customer_article_last_purchase_price", dtype=String),
    ],
    online=False,
    source=point_in_time_training_dataset_source,
)


@on_demand_feature_view(
    sources=[customer_profile_base],
    schema=[
        Field(name="age", dtype=String),
        Field(name="club_member_status", dtype=String),
        Field(name="fashion_news_frequency", dtype=String),
        Field(name="has_fn_flag", dtype=String),
        Field(name="has_active_flag", dtype=String),
    ],
)
def customer_profile_features(inputs: pd.DataFrame) -> pd.DataFrame:
    """Expose the logical customer profile fields expected by the current registry."""
    return pd.DataFrame(
        {
            "age": inputs["customer_age"].fillna(""),
            "club_member_status": inputs["customer_club_member_status"].fillna(""),
            "fashion_news_frequency": inputs["customer_fashion_news_frequency"].fillna(""),
            "has_fn_flag": inputs["customer_has_fn_flag"].fillna("").replace("", "0"),
            "has_active_flag": inputs["customer_has_active_flag"]
            .fillna("")
            .replace("", "0"),
        }
    )


@on_demand_feature_view(
    sources=[product_catalog_base],
    schema=[
        Field(name="product_type_name", dtype=String),
        Field(name="product_group_name", dtype=String),
        Field(name="colour_group_name", dtype=String),
        Field(name="department_name", dtype=String),
        Field(name="index_group_name", dtype=String),
        Field(name="has_detail_desc", dtype=String),
        Field(name="has_image", dtype=String),
    ],
)
def article_catalog_features(inputs: pd.DataFrame) -> pd.DataFrame:
    """Expose the logical article catalog fields expected by the current registry."""
    return pd.DataFrame(
        {
            "product_type_name": inputs["article_product_type_name"].fillna(""),
            "product_group_name": inputs["article_product_group_name"].fillna(""),
            "colour_group_name": inputs["article_colour_group_name"].fillna(""),
            "department_name": inputs["article_department_name"].fillna(""),
            "index_group_name": inputs["article_index_group_name"].fillna(""),
            "has_detail_desc": inputs["article_has_detail_desc"].fillna("").replace("", "0"),
            "has_image": inputs["article_has_image"].fillna("").replace("", "0"),
        }
    )


@on_demand_feature_view(
    sources=[customer_activity_base],
    schema=[
        Field(name="purchase_count_30d", dtype=String),
        Field(name="purchase_count_all_time", dtype=String),
        Field(name="days_since_last_purchase", dtype=String),
        Field(name="distinct_articles_purchased_30d", dtype=String),
        Field(name="avg_purchase_price_30d", dtype=String),
    ],
)
def customer_activity_features(inputs: pd.DataFrame) -> pd.DataFrame:
    """Expose the logical customer activity fields expected by the current registry."""
    return pd.DataFrame(
        {
            "purchase_count_30d": inputs["customer_purchase_count_30d"].fillna("0"),
            "purchase_count_all_time": inputs["customer_purchase_count_all_time"].fillna("0"),
            "days_since_last_purchase": inputs["customer_days_since_last_purchase"].fillna("-1"),
            "distinct_articles_purchased_30d": inputs[
                "customer_distinct_articles_purchased_30d"
            ].fillna("0"),
            "avg_purchase_price_30d": inputs["customer_avg_purchase_price_30d"].fillna("0.00"),
        }
    )


@on_demand_feature_view(
    sources=[article_demand_base],
    schema=[
        Field(name="purchase_count_7d", dtype=String),
        Field(name="purchase_count_30d", dtype=String),
        Field(name="unique_customers_30d", dtype=String),
        Field(name="avg_article_price_30d", dtype=String),
        Field(name="days_since_last_article_purchase", dtype=String),
    ],
)
def article_demand_features(inputs: pd.DataFrame) -> pd.DataFrame:
    """Expose the logical article demand fields expected by the current registry."""
    return pd.DataFrame(
        {
            "purchase_count_7d": inputs["article_purchase_count_7d"].fillna("0"),
            "purchase_count_30d": inputs["article_purchase_count_30d"].fillna("0"),
            "unique_customers_30d": inputs["article_unique_customers_30d"].fillna("0"),
            "avg_article_price_30d": inputs["article_avg_article_price_30d"].fillna("0.00"),
            "days_since_last_article_purchase": inputs[
                "article_days_since_last_article_purchase"
            ].fillna("-1"),
        }
    )


@on_demand_feature_view(
    sources=[customer_article_affinity_base],
    schema=[
        Field(name="historical_purchase_count", dtype=String),
        Field(name="days_since_last_purchase", dtype=String),
        Field(name="has_purchased_before", dtype=String),
        Field(name="last_purchase_price", dtype=String),
    ],
)
def customer_article_affinity_features(inputs: pd.DataFrame) -> pd.DataFrame:
    """Expose the logical customer-article affinity fields expected by the current registry."""
    return pd.DataFrame(
        {
            "historical_purchase_count": inputs[
                "customer_article_historical_purchase_count"
            ].fillna("0"),
            "days_since_last_purchase": inputs["customer_article_days_since_last_purchase"].fillna(
                "-1"
            ),
            "has_purchased_before": inputs["customer_article_has_purchased_before"].fillna("0"),
            "last_purchase_price": inputs["customer_article_last_purchase_price"].fillna("0.00"),
        }
    )


def offline_feature_views() -> list:
    """Return the public Feast offline feature views in registry order."""
    return [
        customer_profile_features,
        article_catalog_features,
        customer_activity_features,
        article_demand_features,
        customer_article_affinity_features,
    ]
