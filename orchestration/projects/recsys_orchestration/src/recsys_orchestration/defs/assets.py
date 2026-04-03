from __future__ import annotations

import dagster as dg

import recsys_orchestration.defs.runtime  # noqa: F401

from recsys_prd.config import get_app_settings

from pipelines.feast_store import apply_feast_repo
from pipelines.normalization import run_hm_normalization
from simulator.replay import publish_local_replay
from recsys_prd.api.smoke import build_api_smoke_report
from recsys_prd.features.streaming_features import compute_online_feature_store
from recsys_prd.ranking.evaluation import evaluate_registered_ranking_model
from recsys_prd.ranking.offline_evaluator import OfflineRankingEvaluator
from recsys_prd.ranking.promotion import evaluate_promotion_gate
from recsys_prd.ranking.registry import register_candidate_ranking_model
from recsys_prd.ranking.training import train_local_ranking_model
from recsys_prd.retrieval.embedding_pipeline import build_embedding_artifacts
from recsys_prd.retrieval.evaluation import OfflineRetrievalEvaluator
from recsys_prd.retrieval.vector_index import build_vector_indexes
from recsys_prd.serving.online_evaluation import build_online_experiment_report


@dg.asset(group_name="ingestion")
def hm_raw_dataset(context) -> dg.MaterializeResult:
    """Track the raw H&M dataset landing area."""
    settings = get_app_settings()
    return dg.MaterializeResult(
        metadata={"raw_root": str(settings.paths.raw_hm_root), "run_id": context.run_id}
    )


@dg.asset(group_name="normalization", deps=[hm_raw_dataset])
def normalized_hm_dataset() -> dict[str, str]:
    """Normalize the ingested H&M source tables."""
    outputs = run_hm_normalization(settings=get_app_settings())
    return {name: str(path) for name, path in outputs.items()}


@dg.asset(group_name="simulator", deps=[normalized_hm_dataset])
def replay_batches() -> dict[str, str]:
    """Generate deterministic simulator replay batches."""
    outputs = publish_local_replay(settings=get_app_settings())
    return {name: str(path) for name, path in outputs.items()}


@dg.asset(group_name="features")
def feast_materialization() -> dict[str, str]:
    """Apply the Feast repository definitions."""
    outputs = apply_feast_repo(settings=get_app_settings())
    return {key: str(value) for key, value in outputs.items()}


@dg.asset(group_name="retrieval", deps=[normalized_hm_dataset])
def embedding_artifacts() -> dict[str, str]:
    """Build embedding artifacts for retrieval."""
    outputs = build_embedding_artifacts(settings=get_app_settings())
    return {name: str(path) for name, path in outputs.items()}


@dg.asset(group_name="retrieval", deps=[embedding_artifacts])
def vector_index_artifacts() -> dict[str, str]:
    """Build vector index artifacts from embedding outputs."""
    outputs = build_vector_indexes(settings=get_app_settings())
    return {name: str(path) for name, path in outputs.items()}


@dg.asset(group_name="features", deps=[replay_batches])
def online_feature_state() -> dict[str, str]:
    """Compute local online feature snapshots from replay batches."""
    outputs = compute_online_feature_store(settings=get_app_settings())
    return {name: str(path) for name, path in outputs.items()}


@dg.asset(group_name="retrieval", deps=[vector_index_artifacts])
def retrieval_evaluation_report() -> dict[str, str]:
    """Evaluate retrieval quality, freshness, and promotion readiness."""
    outputs = OfflineRetrievalEvaluator(settings=get_app_settings()).evaluate()
    return {name: str(value) for name, value in outputs.items()}


@dg.asset(group_name="ranking", deps=[vector_index_artifacts, feast_materialization])
def ranking_model_artifacts() -> dict[str, str]:
    """Train and track the current ranking model."""
    outputs = train_local_ranking_model(settings=get_app_settings())
    return {name: str(path) for name, path in outputs.items()}


@dg.asset(group_name="ranking", deps=[ranking_model_artifacts])
def ranking_candidate_registration() -> dict[str, str]:
    """Register the latest ranking model as the current candidate."""
    outputs = register_candidate_ranking_model(settings=get_app_settings())
    return {name: str(path) for name, path in outputs.items()}


@dg.asset(group_name="evaluation", deps=[ranking_candidate_registration])
def ranking_evaluation_report() -> dict[str, str]:
    """Evaluate the latest registered ranking model."""
    outputs = evaluate_registered_ranking_model(settings=get_app_settings())
    return {name: str(value) for name, value in outputs.items()}


@dg.asset(group_name="evaluation", deps=[ranking_candidate_registration])
def offline_ranking_quality_report() -> dict[str, str]:
    """Evaluate offline ranking quality metrics for the latest candidate."""
    outputs = OfflineRankingEvaluator(settings=get_app_settings()).evaluate()
    return {name: str(value) for name, value in outputs.items()}


@dg.asset(group_name="serving")
def api_smoke_report() -> dict[str, str]:
    """Validate health, readiness, and diagnostics through the public API contract."""
    outputs = build_api_smoke_report(settings=get_app_settings())
    return {name: str(value) for name, value in outputs.items()}


@dg.asset(group_name="serving", deps=[api_smoke_report])
def online_experiment_report() -> dict[str, str]:
    """Summarize local exposure and event logs into online guardrail metrics."""
    outputs = build_online_experiment_report(settings=get_app_settings())
    return {name: str(value) for name, value in outputs.items()}


@dg.asset(
    group_name="promotion",
    deps=[
        retrieval_evaluation_report,
        ranking_evaluation_report,
        online_experiment_report,
    ],
)
def promotion_gate_report() -> dict[str, str]:
    """Combine offline metrics, API smoke checks, and online guardrails into one decision."""
    outputs = evaluate_promotion_gate(settings=get_app_settings())
    return {name: str(value) for name, value in outputs.items()}


ASSETS = [
    hm_raw_dataset,
    normalized_hm_dataset,
    replay_batches,
    feast_materialization,
    embedding_artifacts,
    vector_index_artifacts,
    online_feature_state,
    retrieval_evaluation_report,
    ranking_model_artifacts,
    ranking_candidate_registration,
    ranking_evaluation_report,
    offline_ranking_quality_report,
    api_smoke_report,
    online_experiment_report,
    promotion_gate_report,
]
