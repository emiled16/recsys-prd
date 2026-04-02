from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ReplayTopicManifest(BaseModel):
    path: str
    row_count: int


class ReplayBatchManifest(BaseModel):
    generated_at_utc: str
    topics: dict[str, ReplayTopicManifest]


class EmbeddingArtifactRecord(BaseModel):
    article_id: str
    generated_at_utc: str
    model_name: str
    model_version: str
    modality: str
    strategy_name: str
    vector: list[float]
    vector_dimension: int
    structured_metadata: dict[str, str]
    modality_availability: dict[str, bool]
    source_path: str | None = None


class FeatureStoreWriteRecord(BaseModel):
    entity_type: Literal["session", "customer", "article"]
    entity_key: str
    feature_view: str
    payload: dict[str, Any] = Field(default_factory=dict)
    event_id: str | None = None
    event_time: str | None = None


class ModelRegistrationRecord(BaseModel):
    registration_id: str
    registered_at_utc: str
    model_name: str
    model_version: str
    stage: str
    source_run_id: str
    training_manifest_path: str
    dataset: dict[str, Any]
    training_config: dict[str, Any]
    metrics: dict[str, Any]
    artifacts: dict[str, Any]
    lineage: dict[str, Any]
    registration_path: str
