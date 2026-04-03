from __future__ import annotations

from datetime import timedelta

import pandas as pd
from feast import FeatureView, Field
from feast.on_demand_feature_view import on_demand_feature_view
from feast.types import String

from feast_repo.entities import customer
from feast_repo.sources import point_in_time_training_dataset_source

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
