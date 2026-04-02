from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OnlineFeatureRequirement:
    name: str
    entity_name: str
    join_keys: tuple[str, ...]
    freshness_target_seconds: int
    streaming_inputs: tuple[str, ...]
    feature_fields: tuple[str, ...]
    description: str
