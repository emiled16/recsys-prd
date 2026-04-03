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
    backend: str = ""
    modality: str
    strategy_name: str
    vector: list[float]
    vector_dimension: int
    structured_metadata: dict[str, str]
    modality_availability: dict[str, bool]
    lineage: dict[str, Any] = Field(default_factory=dict)
    source_path: str | None = None


class EmbeddingArtifactManifest(BaseModel):
    path: str
    row_count: int
    model_name: str
    model_version: str
    backend: str
    strategy_name: str
    required_modalities: list[str] = Field(default_factory=list)
    dimension: int
    artifact_digest: str
    lineage: dict[str, Any] = Field(default_factory=dict)


class VectorIndexArtifactManifest(BaseModel):
    path: str
    source_embedding_path: str
    source_embedding_manifest_path: str | None = None
    row_count: int
    dimension: int
    strategy_name: str
    distance_metric: str = "cosine"
    artifact_digest: str
    lineage: dict[str, Any] = Field(default_factory=dict)


class RetrievalSliceMetric(BaseModel):
    slice_name: str
    query_count: int
    metrics: dict[str, float] = Field(default_factory=dict)


class PromotionReadinessReport(BaseModel):
    ready_for_promotion: bool = False
    required_metrics: dict[str, float] = Field(default_factory=dict)
    actual_metrics: dict[str, float] = Field(default_factory=dict)
    freshness: dict[str, Any] = Field(default_factory=dict)
    blockers: list[str] = Field(default_factory=list)


class ApiSmokeReport(BaseModel):
    checked_at_utc: str
    health_ok: bool = False
    ready_ok: bool = False
    diagnostics_ok: bool = False
    blockers: list[str] = Field(default_factory=list)


class PromotionGateDecision(BaseModel):
    checked_at_utc: str
    ready_for_promotion: bool = False
    retrieval_ready: bool = False
    ranking_ready: bool = False
    api_smoke_ok: bool = False
    experiment_ready: bool = False
    blockers: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class RetrievalEvaluationReport(BaseModel):
    evaluated_at_utc: str
    query_count: int
    k: int
    index_name: str
    index_manifest_path: str | None = None
    embedding_manifest_path: str | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    slices: dict[str, RetrievalSliceMetric] = Field(default_factory=dict)
    freshness: dict[str, Any] = Field(default_factory=dict)
    readiness: PromotionReadinessReport = Field(default_factory=PromotionReadinessReport)


class OnlineExperimentReport(BaseModel):
    evaluated_at_utc: str
    exposure_count: int = 0
    click_count: int = 0
    feedback_count: int = 0
    ctr: float = 0.0
    fallback_rate: float = 0.0
    null_result_rate: float = 0.0
    guardrails: dict[str, Any] = Field(default_factory=dict)
    rollback_recommended: bool = False
    blockers: list[str] = Field(default_factory=list)


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
