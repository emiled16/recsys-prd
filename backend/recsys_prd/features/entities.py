from __future__ import annotations

from recsys_prd.features.contracts import FeatureEntity


CUSTOMER_ENTITY = FeatureEntity(
    name="customer",
    join_keys=("customer_id",),
    source_dataset="customers_normalized",
    description="Canonical customer entity for profile and historical activity features.",
)

ARTICLE_ENTITY = FeatureEntity(
    name="article",
    join_keys=("article_id",),
    source_dataset="products_normalized",
    description="Canonical article entity for catalog and demand features.",
)

CUSTOMER_ARTICLE_ENTITY = FeatureEntity(
    name="customer_article",
    join_keys=("customer_id", "article_id"),
    source_dataset="transactions_normalized",
    description="Composite entity for customer-article affinity features.",
)
