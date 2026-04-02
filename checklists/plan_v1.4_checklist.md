# Checklist for Plan v1.4

## Milestone M1: Completed Baseline
- [x] T1: Confirm project scope and success criteria
- [x] T2: Record initial architecture direction
- [x] T3: Publish the first execution plan and tracking artifacts
- [x] T4: Refine the plan into execution-sized tasks
- [x] T5: Define the source dataset contract
- [x] T6: Define local storage and dataset layout conventions
- [x] T7: Build raw dataset ingestion
- [x] T8: Build product normalization
- [x] T9: Build customer normalization
- [x] T10: Build transaction normalization
- [x] T11: Validate normalized dataset outputs
- [x] T12: Define event schemas for simulated online behavior
- [x] T13: Implement synthetic interaction generation
- [x] T14: Implement catalog change event generation
- [x] T15: Implement local event publishing and replay
- [x] T16: Validate replayed event quality
- [x] T17: Define offline feature entities and views
- [x] T18: Build point-in-time correct training joins
- [x] T19: Define online feature requirements
- [x] T20: Build baseline streaming feature computation
- [x] T21: Expose baseline online feature serving
- [x] T22: Validate baseline feature parity and freshness
- [x] T23: Define multimodal representation strategy
- [x] T24: Build baseline embedding generation pipeline
- [x] T25: Build baseline vector indexing pipeline
- [x] T26: Implement baseline candidate retrieval logic
- [x] T27: Build ranking dataset generation
- [x] T28: Implement baseline ranking model training
- [x] T29: Register baseline candidate models and metadata

## Milestone M2: Refactor the Current Backend Into Stable Boundaries
- [x] T30: Add `AppSettings` and `PathSettings` objects under a dedicated config module
- [x] T31: Replace direct path construction in existing modules with settings-based path resolution
- [x] T32: Split the current monolithic CLI into domain command handlers
- [x] T33: Introduce shared request and artifact schemas for post-baseline evolution
- [x] T34: Convert normalized, PIT, and ranking datasets from CSV/JSON to Parquet write paths
- [x] T35: Add compatibility readers so current code can consume both old and new artifact formats during migration
- [x] T36: Add refactor-focused tests for settings, schemas, and CLI handler routing

## Milestone M3: Add the External Services Needed for the Real Stack
- [x] T37: Create `docker-compose.yml` with named services for Redpanda, Redis, Qdrant, and MLflow
- [x] T38: Add Redpanda service configuration and topic bootstrap script
- [x] T39: Add Redis service configuration and a connectivity probe
- [x] T40: Add Qdrant service configuration and collection-management probe
- [x] T41: Add MLflow tracking server configuration and a run logging probe

## Milestone M4: Replace the File-Only Event Publishing Path With Kafka-Compatible Publishing
- [x] T42: Implement a `KafkaReplayPublisher` object for sending replay batches to Redpanda
- [x] T43: Add a CLI command that publishes replay artifacts into broker topics
- [x] T44: Implement broker delivery validation for published replay batches

## Milestone M5: Replace the File-Backed Online Feature Store With Redis
- [x] T45: Implement a `RedisOnlineFeatureStore` object with `put_*` and `get_*` methods for session, customer, and article entities
- [x] T46: Refactor `OnlineFeatureService` to read from `RedisOnlineFeatureStore` instead of JSON files
- [x] T47: Implement a `FeatureUpdateProcessor` that converts broker events into online feature mutations
- [x] T48: Implement a broker consumer that applies feature updates into Redis
- [x] T49: Update feature freshness and parity validation to use Redis-backed reads

## Milestone M6: Express the Feature Platform in Feast
- [x] T50: Create a dedicated Feast repository with `feature_store.yaml`, entity definitions, and source definitions
- [x] T51: Re-express offline feature views from `features.registry()` as Feast feature views
- [x] T52: Re-express online feature requirements as Feast online feature views backed by Redis
- [x] T53: Add a command to materialize or apply Feast definitions locally
- [x] T54: Implement a `FeastPointInTimeDatasetBuilder` that replaces custom PIT joins
- [x] T55: Update ranking dataset generation to consume Feast-built training rows

## Milestone M7: Replace Deterministic Embeddings and Local Vector Indexes
- [x] T56: Introduce a `TextEmbedder` abstraction with a real `SentenceTransformerTextEmbedder` implementation
- [x] T57: Introduce an `ImageEmbedder` abstraction with a real `OpenClipImageEmbedder` implementation
- [x] T58: Refactor `build_embedding_artifacts()` to use pluggable embedder implementations
- [ ] T59: Implement a `QdrantIndexManager` that creates collections and upserts embedding records
- [ ] T60: Add a command that loads embedding artifacts into Qdrant collections
- [ ] T61: Implement a `QdrantCandidateRetriever` that preserves the current `RetrievalRequest -> RetrievalResult` contract
- [ ] T62: Update candidate retrieval to enrich requests with Feast and Redis online context

## Milestone M8: Replace the File-Backed Model Platform With MLflow and a Library-Backed Ranker
- [ ] T63: Implement an `MLflowRunLogger` wrapper for params, metrics, tags, and artifact logging
- [ ] T64: Refactor `train_local_ranking_model()` to log training results through `MLflowRunLogger`
- [ ] T65: Implement an `MLflowModelRegistrar` that registers trained ranking models into the MLflow Model Registry
- [ ] T66: Add a `LightGBMRankerTrainer` or `XGBoostRankerTrainer` implementation behind a ranking trainer abstraction
- [ ] T67: Update ranking evaluation to score MLflow-registered models rather than only local artifacts

## Milestone M9: Build the Actual Evaluation and Recommendation Serving Paths
- [ ] T68: Implement an `OfflineRetrievalEvaluator` for Recall@K, MRR, and NDCG on Qdrant-backed candidates
- [ ] T69: Implement an `OfflineRankingEvaluator` for Precision@K, MAP@K, NDCG@K, and pairwise quality
- [ ] T70: Add API request and response models for recommendation serving
- [ ] T71: Implement a `RecommendationService` orchestration object
- [ ] T72: Expose `RecommendationService` through a FastAPI application
- [ ] T73: Add timeout, fallback, and validation behavior to the API path
- [ ] T74: Implement an `ExperimentAssigner` and `ExposureLogger` for online experimentation

## Milestone M10: Add Observability, Orchestration, and Final Documentation
- [ ] T75: Instrument API, retrieval, ranking, and feature flows with Prometheus metrics
- [ ] T76: Add Prometheus and Grafana services plus a baseline dashboard
- [ ] T77: Add Dagster assets and jobs for ingestion, feature materialization, embedding generation, training, and evaluation
- [ ] T78: Update the system design and operating docs to match the implemented stack
