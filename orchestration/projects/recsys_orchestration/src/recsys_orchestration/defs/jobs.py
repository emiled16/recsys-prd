from __future__ import annotations

import dagster as dg

from recsys_orchestration.defs.assets import (
    api_smoke_report,
    embedding_artifacts,
    feast_materialization,
    hm_raw_dataset,
    normalized_hm_dataset,
    offline_ranking_quality_report,
    online_experiment_report,
    online_feature_state,
    promotion_gate_report,
    ranking_candidate_registration,
    ranking_evaluation_report,
    ranking_model_artifacts,
    replay_batches,
    retrieval_evaluation_report,
    vector_index_artifacts,
)


training_job = dg.define_asset_job(
    name="training_job",
    selection=[
        hm_raw_dataset,
        normalized_hm_dataset,
        replay_batches,
        feast_materialization,
        embedding_artifacts,
        vector_index_artifacts,
        online_feature_state,
        ranking_model_artifacts,
        ranking_candidate_registration,
    ],
)

evaluation_job = dg.define_asset_job(
    name="evaluation_job",
    selection=[
        retrieval_evaluation_report,
        ranking_evaluation_report,
        offline_ranking_quality_report,
        api_smoke_report,
        online_experiment_report,
        promotion_gate_report,
    ],
)

replay_job = dg.define_asset_job(
    name="replay_job",
    selection=[replay_batches, online_feature_state],
)

JOBS = [training_job, evaluation_job, replay_job]
