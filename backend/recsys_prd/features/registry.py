from __future__ import annotations

from recsys_prd.features.entities import (
    ARTICLE_ENTITY,
    CUSTOMER_ARTICLE_ENTITY,
    CUSTOMER_ENTITY,
)
from recsys_prd.features.views import (
    ARTICLE_CATALOG_VIEW,
    ARTICLE_DEMAND_VIEW,
    CUSTOMER_ACTIVITY_VIEW,
    CUSTOMER_ARTICLE_AFFINITY_VIEW,
    CUSTOMER_PROFILE_VIEW,
)


def feature_entities() -> list:
    """Return the offline feature entities in registry order."""
    return [CUSTOMER_ENTITY, ARTICLE_ENTITY, CUSTOMER_ARTICLE_ENTITY]


def feature_views() -> list:
    """Return the offline feature views in registry order."""
    return [
        CUSTOMER_PROFILE_VIEW,
        ARTICLE_CATALOG_VIEW,
        CUSTOMER_ACTIVITY_VIEW,
        ARTICLE_DEMAND_VIEW,
        CUSTOMER_ARTICLE_AFFINITY_VIEW,
    ]
