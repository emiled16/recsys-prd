# Plan v1.7 Import Audit

## Scope
This inventory captures current imports of `recsys_prd.normalization`, `recsys_prd.validation`, and `recsys_prd.events` so the package migration in `plan_v1.7` can be executed without guessing.

## Ownership Classification
- `recsys_prd.normalization.*`: pipeline-owned. Target home is `pipelines.normalization_pkg.*`.
- `recsys_prd.validation.hm_normalized`: pipeline-owned. Target home is `pipelines.validation_pkg.hm_normalized`.
- `recsys_prd.events.replay`, `recsys_prd.events.validation`, `recsys_prd.events.contracts`: simulator-owned. Target home is `simulator.*`.
- `recsys_prd.events.ids`: shared event-contract utility used by simulator-owned code.
- `recsys_prd.events.io`: shared artifact IO utility. Target home is `recsys_prd.io.jsonl_ops`.

## Pipeline-Owned Importers

### `pipelines/normalization.py`
- `recsys_prd.normalization.customers`
- `recsys_prd.normalization.products`
- `recsys_prd.normalization.transactions`
- `recsys_prd.normalization.writer`
- Migration target: replace all imports with `pipelines.normalization_pkg.*`.

### `pipelines/feast_training_dataset.py`
- `recsys_prd.normalization.writer`
- Migration target: replace with `pipelines.normalization_pkg.writer`.

### `pipelines/ranking_dataset.py`
- `recsys_prd.normalization.writer`
- Migration target: replace with `pipelines.normalization_pkg.writer`.

### `pipelines/training_dataset.py`
- `recsys_prd.normalization.writer`
- Migration target: replace with `pipelines.normalization_pkg.writer`.

## Simulator-Owned Importers

### `simulator/catalog_generator.py`
- `recsys_prd.events.ids`
- Migration target: move to a shared contract helper that is not under `recsys_prd.events`.

### `simulator/interaction_generator.py`
- `recsys_prd.events.ids`
- Migration target: move to a shared contract helper that is not under `recsys_prd.events`.

### `simulator/replay.py`
- `recsys_prd.events.io`
- Migration target: replace with `recsys_prd.io.jsonl_ops`.

### `simulator/validation.py`
- `recsys_prd.events.io`
- Migration target: replace with `recsys_prd.io.jsonl_ops`.

## Backend-Owned Importers

### Backend CLI
`backend/recsys_prd/cli.py`
- `recsys_prd.events.replay`
- `recsys_prd.events.validation`
- `recsys_prd.normalization.pipeline`
- `recsys_prd.validation.hm_normalized`
- Migration target: import simulator-owned and pipeline-owned entrypoints directly from `simulator.*` and `pipelines.*`.

### Backend Serving, Retrieval, Ranking, and Services
- `backend/recsys_prd/features/streaming_features.py`: `recsys_prd.events.io`
- `backend/recsys_prd/ranking/registry.py`: `recsys_prd.events.io`
- `backend/recsys_prd/ranking/training.py`: `recsys_prd.events.io`
- `backend/recsys_prd/retrieval/candidate_retrieval.py`: `recsys_prd.events.io`
- `backend/recsys_prd/retrieval/embedding_pipeline.py`: `recsys_prd.events.io`
- `backend/recsys_prd/retrieval/vector_index.py`: `recsys_prd.events.io`
- `backend/recsys_prd/services/qdrant_store.py`: `recsys_prd.events.io`
- `backend/recsys_prd/services/redpanda.py`: `recsys_prd.events.io`
- `backend/recsys_prd/serving/online_evaluation.py`: `recsys_prd.events.io`
- Migration target: replace all event IO imports with `recsys_prd.io.jsonl_ops`.

### Backend Internal Legacy Modules
- `backend/recsys_prd/normalization/customers.py`: imports `recsys_prd.normalization.cleaning`, `recsys_prd.normalization.contracts`
- `backend/recsys_prd/normalization/products.py`: imports `recsys_prd.normalization.cleaning`, `recsys_prd.normalization.contracts`
- `backend/recsys_prd/normalization/transactions.py`: imports `recsys_prd.normalization.cleaning`, `recsys_prd.normalization.contracts`
- `backend/recsys_prd/normalization/writer.py`: imports `recsys_prd.normalization.profile`
- `backend/recsys_prd/validation/hm_normalized.py`: imports `recsys_prd.normalization.contracts`
- Migration target: these become temporary shim modules and are deleted by `T146`.

## Orchestration-Owned Importers
- No direct imports from `recsys_prd.normalization`, `recsys_prd.validation`, or `recsys_prd.events` in the current Dagster definitions.
- Indirect dependency exists through `pipelines.normalization.run_hm_normalization` and backend CLI entrypoints.
- Migration target: keep orchestration importing only owner surfaces after `T145` and `T147`.

## Tests
- Replay imports:
  - `backend/tests/unit/test_candidate_retrieval.py`
  - `backend/tests/unit/test_feature_parity_validation.py`
  - `backend/tests/unit/test_hm_events.py`
  - `backend/tests/unit/test_online_feature_computation.py`
  - `backend/tests/unit/test_online_feature_service.py`
- Validation imports:
  - `backend/tests/unit/test_hm_events.py`
  - `backend/tests/unit/test_hm_normalization.py`
- Normalization imports:
  - `backend/tests/unit/test_candidate_retrieval.py`
  - `backend/tests/unit/test_embedding_pipeline.py`
  - `backend/tests/unit/test_feast_training_dataset.py`
  - `backend/tests/unit/test_feature_parity_validation.py`
  - `backend/tests/unit/test_hm_events.py`
  - `backend/tests/unit/test_hm_normalization.py`
  - `backend/tests/unit/test_offline_ranking_evaluator.py`
  - `backend/tests/unit/test_online_feature_computation.py`
  - `backend/tests/unit/test_online_feature_service.py`
  - `backend/tests/unit/test_parquet_compatibility.py`
  - `backend/tests/unit/test_pit_training_dataset.py`
  - `backend/tests/unit/test_ranking_dataset.py`
  - `backend/tests/unit/test_ranking_evaluation.py`
  - `backend/tests/unit/test_ranking_registry.py`
  - `backend/tests/unit/test_ranking_training.py`
  - `backend/tests/unit/test_retrieval_evaluation.py`
  - `backend/tests/unit/test_vector_index.py`
- Event IO imports:
  - `backend/tests/unit/test_embedding_pipeline.py`
  - `backend/tests/unit/test_ranking_registry.py`
  - `backend/tests/unit/test_ranking_training.py`
  - `backend/tests/unit/test_vector_index.py`
- Migration target: update tests to import owner surfaces directly and reserve shared imports for `recsys_prd.io.jsonl_ops` only.
