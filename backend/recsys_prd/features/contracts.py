from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureEntity:
    name: str
    join_keys: tuple[str, ...]
    source_dataset: str
    description: str


@dataclass(frozen=True)
class FeatureView:
    name: str
    entity_name: str
    source_datasets: tuple[str, ...]
    timestamp_field: str | None
    feature_fields: tuple[str, ...]
    description: str
