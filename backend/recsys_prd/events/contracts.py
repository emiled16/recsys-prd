from __future__ import annotations


INTERACTION_EVENT_TYPES = [
    "product_view",
    "product_click",
    "add_to_cart",
    "wishlist_add",
    "purchase",
    "search_query",
]

CATALOG_EVENT_TYPES = [
    "inventory_update",
    "price_change",
    "product_metadata_update",
]

INTERACTION_REQUIRED_FIELDS = [
    "event_id",
    "event_type",
    "event_time",
    "customer_id",
    "session_id",
    "source",
]

CATALOG_REQUIRED_FIELDS = [
    "event_id",
    "event_type",
    "event_time",
    "article_id",
    "source",
]
