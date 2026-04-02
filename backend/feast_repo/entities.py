from __future__ import annotations

from feast import Entity
from feast.value_type import ValueType

customer = Entity(
    name="customer",
    join_keys=["customer_id"],
    value_type=ValueType.STRING,
    description="Canonical customer entity for offline and online feature serving.",
)

article = Entity(
    name="article",
    join_keys=["article_id"],
    value_type=ValueType.STRING,
    description="Canonical article entity for retrieval and ranking features.",
)

customer_session = Entity(
    name="customer_session",
    join_keys=["customer_session_id"],
    value_type=ValueType.STRING,
    description="Composite customer-session entity using a derived single-key identifier.",
)
