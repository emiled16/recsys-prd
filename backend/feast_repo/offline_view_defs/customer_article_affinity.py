from __future__ import annotations

from datetime import timedelta

import pandas as pd
from feast import FeatureView, Field
from feast.on_demand_feature_view import on_demand_feature_view
from feast.types import String

from feast_repo.entities import article, customer
from feast_repo.sources import point_in_time_training_dataset_source

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
