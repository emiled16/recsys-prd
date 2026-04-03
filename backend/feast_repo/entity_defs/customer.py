from __future__ import annotations

from feast import Entity
from feast.value_type import ValueType

customer = Entity(
    name="customer",
    join_keys=["customer_id"],
    value_type=ValueType.STRING,
    description="Canonical customer entity for offline and online feature serving.",
)
