from __future__ import annotations

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

__all__ = [
    "customer_profile_base",
    "product_catalog_base",
    "customer_activity_base",
    "article_demand_base",
    "customer_article_affinity_base",
    "customer_profile_features",
    "article_catalog_features",
    "customer_activity_features",
    "article_demand_features",
    "customer_article_affinity_features",
    "offline_feature_views",
]


def offline_feature_views() -> list:
    """Return the public Feast offline feature views in registry order."""
    return [
        customer_profile_features,
        article_catalog_features,
        customer_activity_features,
        article_demand_features,
        customer_article_affinity_features,
    ]
