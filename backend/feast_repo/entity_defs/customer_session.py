from __future__ import annotations

from feast import Entity
from feast.value_type import ValueType

customer_session = Entity(
    name="customer_session",
    join_keys=["customer_session_id"],
    value_type=ValueType.STRING,
    description="Composite customer-session entity using a derived single-key identifier.",
)
