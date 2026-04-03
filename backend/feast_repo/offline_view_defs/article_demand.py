from __future__ import annotations

from datetime import timedelta

import pandas as pd
from feast import FeatureView, Field
from feast.on_demand_feature_view import on_demand_feature_view
from feast.types import String

from feast_repo.entities import article
from feast_repo.sources import point_in_time_training_dataset_source

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
