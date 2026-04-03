from __future__ import annotations

from datetime import timedelta

import pandas as pd
from feast import FeatureView, Field
from feast.on_demand_feature_view import on_demand_feature_view
from feast.types import String

from feast_repo.entities import article
from feast_repo.sources import point_in_time_training_dataset_source

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
