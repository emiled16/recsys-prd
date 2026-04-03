from __future__ import annotations

from datetime import timedelta

import pandas as pd
from feast import FeatureView, Field
from feast.on_demand_feature_view import on_demand_feature_view
from feast.types import String

from feast_repo.entities import customer
from feast_repo.sources import point_in_time_training_dataset_source

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
