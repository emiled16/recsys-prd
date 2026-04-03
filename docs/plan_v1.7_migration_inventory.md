# Plan v1.7 Migration Inventory

## Scope
This inventory records the current import sites that still depend on backend-owned
`recsys_prd.normalization`, `recsys_prd.validation`, and `recsys_prd.events` modules.
It is the execution map for the `v1.7` package migration.

## Target Ownership
- `pipelines.normalization_pkg`: normalization transforms, contracts, writers, and runtime
- `pipelines.validation_pkg`: normalized-data validation
- `pipelines.training`: offline training dataset builders and batch model-build entrypoints
- `simulator`: replay generation, replay validation, and event/replay contracts
- `recsys_prd.io.jsonl_ops`: shared JSONL artifact IO used across backend, pipelines, and simulator
- `recsys_prd.events.ids`: temporary shared ID helper until replay ID generation is folded into simulator

## Current Import Sites

### `recsys_prd.normalization`

#### Pipeline-owned imports to migrate
- [pipelines/normalization.py](/Users/emdim/dev/recsys-prd/pipelines/normalization.py): imports normalization transforms and dataset writer; should migrate to `pipelines.normalization_pkg`
- [pipelines/training_dataset.py](/Users/emdim/dev/recsys-prd/pipelines/training_dataset.py): imports `write_dataset_bundle`; should migrate to `pipelines.normalization_pkg.writer`
- [pipelines/ranking_dataset.py](/Users/emdim/dev/recsys-prd/pipelines/ranking_dataset.py): imports `write_dataset_bundle`; should migrate to `pipelines.normalization_pkg.writer`
- [pipelines/feast_training_dataset.py](/Users/emdim/dev/recsys-prd/pipelines/feast_training_dataset.py): imports `write_dataset_bundle`; should migrate to `pipelines.normalization_pkg.writer`

#### Backend-owned imports to replace with pipeline entrypoints
- [backend/recsys_prd/cli.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/cli.py): imports `run_hm_normalization`; should call `pipelines.normalization_pkg.run_hm_normalization`

#### Validation imports to move with pipeline validation
- [backend/recsys_prd/validation/hm_normalized.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/validation/hm_normalized.py): imports normalization contracts; should migrate into `pipelines.validation_pkg`

#### Test-only imports to update after runtime migration
- [backend/tests/unit/test_hm_normalization.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_hm_normalization.py)
- [backend/tests/unit/test_candidate_retrieval.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_candidate_retrieval.py)
- [backend/tests/unit/test_embedding_pipeline.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_embedding_pipeline.py)
- [backend/tests/unit/test_feature_parity_validation.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_feature_parity_validation.py)
- [backend/tests/unit/test_feast_training_dataset.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_feast_training_dataset.py)
- [backend/tests/unit/test_hm_events.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_hm_events.py)
- [backend/tests/unit/test_offline_ranking_evaluator.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_offline_ranking_evaluator.py)
- [backend/tests/unit/test_online_feature_computation.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_online_feature_computation.py)
- [backend/tests/unit/test_online_feature_service.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_online_feature_service.py)
- [backend/tests/unit/test_parquet_compatibility.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_parquet_compatibility.py)
- [backend/tests/unit/test_pit_training_dataset.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_pit_training_dataset.py)
- [backend/tests/unit/test_ranking_dataset.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_ranking_dataset.py)
- [backend/tests/unit/test_ranking_evaluation.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_ranking_evaluation.py)
- [backend/tests/unit/test_ranking_registry.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_ranking_registry.py)
- [backend/tests/unit/test_ranking_training.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_ranking_training.py)
- [backend/tests/unit/test_retrieval_evaluation.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_retrieval_evaluation.py)
- [backend/tests/unit/test_vector_index.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_vector_index.py)

### `recsys_prd.validation`

#### Backend-owned imports to replace with pipeline validation entrypoints
- [backend/recsys_prd/cli.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/cli.py): imports `validate_hm_normalized`; should call `pipelines.validation_pkg.validate_hm_normalized`

#### Test-only imports to update after migration
- [backend/tests/unit/test_hm_normalization.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_hm_normalization.py)

### `recsys_prd.events`

#### Simulator-owned imports to move into simulator or shared JSONL IO
- [simulator/catalog_generator.py](/Users/emdim/dev/recsys-prd/simulator/catalog_generator.py): imports `build_event_id`; should move to a simulator-owned or shared event ID helper
- [simulator/interaction_generator.py](/Users/emdim/dev/recsys-prd/simulator/interaction_generator.py): imports `build_event_id`; should move to a simulator-owned or shared event ID helper
- [simulator/replay.py](/Users/emdim/dev/recsys-prd/simulator/replay.py): imports `write_jsonl`; should migrate to `recsys_prd.io.jsonl_ops`
- [simulator/validation.py](/Users/emdim/dev/recsys-prd/simulator/validation.py): imports `read_jsonl`; should migrate to `recsys_prd.io.jsonl_ops`

#### Backend-owned imports to replace with simulator or shared IO contracts
- [backend/recsys_prd/cli.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/cli.py): imports replay generation and replay validation; should call `simulator.publish_local_replay` and `simulator.validate_local_replay`
- [backend/recsys_prd/features/streaming_features.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/features/streaming_features.py): imports `read_jsonl`; should migrate to `recsys_prd.io.jsonl_ops`
- [backend/recsys_prd/ranking/registry.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/ranking/registry.py): imports `read_jsonl` and `write_jsonl`; should migrate to `recsys_prd.io.jsonl_ops`
- [backend/recsys_prd/ranking/training.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/ranking/training.py): imports `read_jsonl` and `write_jsonl`; should migrate to `recsys_prd.io.jsonl_ops`
- [backend/recsys_prd/retrieval/candidate_retrieval.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/retrieval/candidate_retrieval.py): imports `read_jsonl`; should migrate to `recsys_prd.io.jsonl_ops`
- [backend/recsys_prd/retrieval/embedding_pipeline.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/retrieval/embedding_pipeline.py): imports `write_jsonl`; should migrate to `recsys_prd.io.jsonl_ops`
- [backend/recsys_prd/retrieval/vector_index.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/retrieval/vector_index.py): imports `read_jsonl` and `write_jsonl`; should migrate to `recsys_prd.io.jsonl_ops`
- [backend/recsys_prd/services/qdrant_store.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/services/qdrant_store.py): imports `read_jsonl`; should migrate to `recsys_prd.io.jsonl_ops`
- [backend/recsys_prd/services/redpanda.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/services/redpanda.py): imports `read_jsonl`; should migrate to `recsys_prd.io.jsonl_ops`
- [backend/recsys_prd/serving/online_evaluation.py](/Users/emdim/dev/recsys-prd/backend/recsys_prd/serving/online_evaluation.py): imports `read_jsonl`; should migrate to `recsys_prd.io.jsonl_ops`

#### Test-only imports to update after migration
- [backend/tests/unit/test_candidate_retrieval.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_candidate_retrieval.py)
- [backend/tests/unit/test_embedding_pipeline.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_embedding_pipeline.py)
- [backend/tests/unit/test_feature_parity_validation.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_feature_parity_validation.py)
- [backend/tests/unit/test_hm_events.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_hm_events.py)
- [backend/tests/unit/test_online_feature_computation.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_online_feature_computation.py)
- [backend/tests/unit/test_online_feature_service.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_online_feature_service.py)
- [backend/tests/unit/test_ranking_registry.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_ranking_registry.py)
- [backend/tests/unit/test_ranking_training.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_ranking_training.py)
- [backend/tests/unit/test_vector_index.py](/Users/emdim/dev/recsys-prd/backend/tests/unit/test_vector_index.py)

## Sequencing Notes
- Migrate JSONL helpers first because they are shared across simulator and backend consumers.
- Migrate normalization and normalized-data validation before moving offline training entrypoints.
- Keep `recsys_prd.events.ids` temporarily shared until replay generation is fully simulator-owned.
- Remove all backend-path shims in `T146` after all import sites point to owning packages.
