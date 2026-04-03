from __future__ import annotations

from feast import Entity
from feast.value_type import ValueType

article = Entity(
    name="article",
    join_keys=["article_id"],
    value_type=ValueType.STRING,
    description="Canonical article entity for retrieval and ranking features.",
)
