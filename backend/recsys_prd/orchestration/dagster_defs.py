from __future__ import annotations

import dagster as dg

from recsys_prd.config import get_app_settings
from recsys_prd.features.feast_store import apply_feast_repo
from recsys_prd.normalization.pipeline import run_hm_normalization
from recsys_prd.ranking.evaluation import evaluate_registered_ranking_model
from recsys_prd.ranking.training import train_local_ranking_model
from recsys_prd.retrieval.embedding_pipeline import build_embedding_artifacts


@dg.asset(group_name="ingestion")
def hm_raw_dataset(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
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


@dg.asset(group_name="ranking", deps=[embedding_artifacts, feast_materialization])
def ranking_model_artifacts() -> dict[str, str]:
    """Train and track the current ranking model."""
    outputs = train_local_ranking_model(settings=get_app_settings())
    return {name: str(path) for name, path in outputs.items()}


@dg.asset(group_name="evaluation", deps=[ranking_model_artifacts])
def ranking_evaluation_report() -> dict[str, str]:
    """Evaluate the latest registered ranking model."""
    outputs = evaluate_registered_ranking_model(settings=get_app_settings())
    return {name: str(value) for name, value in outputs.items()}


training_job = dg.define_asset_job(
    name="training_job",
    selection=[
        hm_raw_dataset,
        normalized_hm_dataset,
        feast_materialization,
        embedding_artifacts,
        ranking_model_artifacts,
    ],
)

evaluation_job = dg.define_asset_job(
    name="evaluation_job",
    selection=[ranking_evaluation_report],
)

daily_training_schedule = dg.ScheduleDefinition(
    job=training_job,
    cron_schedule="0 6 * * *",
    execution_timezone="America/Toronto",
)

weekly_evaluation_schedule = dg.ScheduleDefinition(
    job=evaluation_job,
    cron_schedule="0 8 * * 1",
    execution_timezone="America/Toronto",
)

defs = dg.Definitions(
    assets=[
        hm_raw_dataset,
        normalized_hm_dataset,
        feast_materialization,
        embedding_artifacts,
        ranking_model_artifacts,
        ranking_evaluation_report,
    ],
    jobs=[training_job, evaluation_job],
    schedules=[daily_training_schedule, weekly_evaluation_schedule],
)
