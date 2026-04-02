# Plan v1.4

## Context
`T1` through `T29` produced a solid local baseline, but the remaining plan needs to be specific enough that an engineer can implement each step without guessing. The missing work is not just "evaluation" or "serving"; it is a sequence of concrete migrations from local stand-ins to real external libraries and runtime services.

This version keeps the completed baseline intact and rewrites the future roadmap into smaller tasks with explicit implementation targets. Each task describes what object, function, service, or contract should be added or changed, what it consumes, what it produces, and which library or runtime it depends on.

## Milestones

### M1: Completed Baseline

#### Task T1: Confirm project scope and success criteria
- Description: Consolidate project goals, constraints, and acceptance criteria into a stable scope baseline.
- Dependencies: None

#### Task T2: Record initial architecture direction
- Description: Capture the high-level architecture and major technology choices.
- Dependencies: T1

#### Task T3: Publish the first execution plan and tracking artifacts
- Description: Create the initial versioned plan and checklist.
- Dependencies: T2

#### Task T4: Refine the plan into execution-sized tasks
- Description: Replace broad work packages with smaller implementation-ready tasks.
- Dependencies: T3

#### Task T5: Define the source dataset contract
- Description: Document source schemas, keys, required fields, and quality assumptions.
- Dependencies: T4

#### Task T6: Define local storage and dataset layout conventions
- Description: Define the local layered storage layout for raw, normalized, feature, event, embedding, model, and report artifacts.
- Dependencies: T5

#### Task T7: Build raw dataset ingestion
- Description: Implement reproducible loading of the H&M source dataset into the project layout.
- Dependencies: T6

#### Task T8: Build product normalization
- Description: Transform raw article records into cleaned product outputs.
- Dependencies: T7

#### Task T9: Build customer normalization
- Description: Transform raw customer records into cleaned customer outputs.
- Dependencies: T7

#### Task T10: Build transaction normalization
- Description: Transform raw transaction history into normalized event-style records.
- Dependencies: T7

#### Task T11: Validate normalized dataset outputs
- Description: Add schema and quality validation for normalized outputs.
- Dependencies: T8, T9, T10

#### Task T12: Define event schemas for simulated online behavior
- Description: Specify event types, fields, and topic boundaries for simulated online signals.
- Dependencies: T11

#### Task T13: Implement synthetic interaction generation
- Description: Generate simulated interaction events for local development.
- Dependencies: T12

#### Task T14: Implement catalog change event generation
- Description: Generate simulated catalog update events for local development.
- Dependencies: T12

#### Task T15: Implement local event publishing and replay
- Description: Publish generated events into deterministic replay artifacts.
- Dependencies: T13, T14

#### Task T16: Validate replayed event quality
- Description: Verify replay ordering, timestamps, completeness, and payload quality.
- Dependencies: T15

#### Task T17: Define offline feature entities and views
- Description: Define offline entities, feature views, and source mappings.
- Dependencies: T11

#### Task T18: Build point-in-time correct training joins
- Description: Implement historical feature retrieval without label leakage.
- Dependencies: T17

#### Task T19: Define online feature requirements
- Description: Define freshness-sensitive online features and the events that update them.
- Dependencies: T16, T17

#### Task T20: Build baseline streaming feature computation
- Description: Compute online feature snapshots from replay artifacts.
- Dependencies: T19

#### Task T21: Expose baseline online feature serving
- Description: Serve baseline online features from the local file-backed store.
- Dependencies: T20

#### Task T22: Validate baseline feature parity and freshness
- Description: Validate semantic parity and freshness targets against the baseline implementation.
- Dependencies: T18, T21

#### Task T23: Define multimodal representation strategy
- Description: Define how text, image, and structured article signals combine for retrieval.
- Dependencies: T11, T17

#### Task T24: Build baseline embedding generation pipeline
- Description: Generate deterministic local text, image, and fused embeddings.
- Dependencies: T23

#### Task T25: Build baseline vector indexing pipeline
- Description: Build local vector-index artifacts from embeddings.
- Dependencies: T24

#### Task T26: Implement baseline candidate retrieval logic
- Description: Retrieve candidates from the local index for a request context.
- Dependencies: T25, T21

#### Task T27: Build ranking dataset generation
- Description: Assemble ranking examples from retrieved candidates, labels, and point-in-time features.
- Dependencies: T18, T26

#### Task T28: Implement baseline ranking model training
- Description: Train the first local ranking baseline and write model artifacts.
- Dependencies: T27

#### Task T29: Register baseline candidate models and metadata
- Description: Persist trained model versions and metadata in the local registry.
- Dependencies: T28

### M2: Refactor the Current Backend Into Stable Boundaries

#### Task T30: Add `AppSettings` and `PathSettings` objects under a dedicated config module
- Description: Implement typed configuration objects, for example `AppSettings`, `PathSettings`, and `ServiceSettings`, that load environment variables and centralize all runtime paths and external endpoints. Inputs: `.env`, process environment, default local paths. Outputs: strongly typed settings objects used by ingestion, features, retrieval, ranking, and serving code. Libraries and tools: `pydantic`, `pydantic-settings`.
- Dependencies: T29

#### Task T31: Replace direct path construction in existing modules with settings-based path resolution
- Description: Update modules such as `ingestion.hm_raw`, `events.replay`, `features.training_dataset`, `features.streaming_features`, `retrieval.embedding_pipeline`, `retrieval.vector_index`, `ranking.training`, and `ranking.registry` to depend on `AppSettings` rather than hardcoded `Path` construction. Inputs: settings object. Outputs: modules that can run against local files now and external services later without hidden path assumptions. Libraries and tools: existing Python modules, `pathlib`.
- Dependencies: T30

#### Task T32: Split the current monolithic CLI into domain command handlers
- Description: Refactor `build_parser()` and `main()` in `backend/recsys_prd/cli.py` so each subsystem owns explicit handlers, for example `run_ingestion_command()`, `run_event_command()`, `run_feature_command()`, `run_retrieval_command()`, and `run_ranking_command()`. Inputs: parsed CLI args and settings. Outputs: command handlers with stable subsystem boundaries. Libraries and tools: current `argparse` CLI or `typer` if adopted in the refactor.
- Dependencies: T30

#### Task T33: Introduce shared request and artifact schemas for post-baseline evolution
- Description: Add explicit data objects for requests and persisted records that are currently implicit dictionaries, for example `ReplayBatchManifest`, `EmbeddingArtifactRecord`, `FeatureStoreWriteRecord`, and `ModelRegistrationRecord`. Inputs: raw dict payloads from current pipelines. Outputs: validated typed records used across file-backed and external-service-backed implementations. Libraries and tools: `pydantic` dataclasses or models.
- Dependencies: T30

#### Task T34: Convert normalized, PIT, and ranking datasets from CSV/JSON to Parquet write paths
- Description: Update the normalization, feature, and ranking pipelines so their primary persisted outputs are Parquet datasets rather than only CSV or JSON. Inputs: normalized rows, training rows, ranking rows. Outputs: Parquet files under the existing data layout, with backward-compatible manifests where needed. Libraries and tools: `pyarrow`.
- Dependencies: T31, T33

#### Task T35: Add compatibility readers so current code can consume both old and new artifact formats during migration
- Description: Implement adapter functions such as `load_normalized_products()`, `load_training_rows()`, and `load_ranking_rows()` that can read the legacy CSV/JSON artifacts and the new Parquet outputs during the migration window. Inputs: artifact root paths. Outputs: normalized in-memory row objects for downstream callers. Libraries and tools: `pyarrow`, existing CSV/JSON helpers.
- Dependencies: T34

#### Task T36: Add refactor-focused tests for settings, schemas, and CLI handler routing
- Description: Add or update tests that verify `AppSettings` parsing, schema validation behavior, and domain-level CLI dispatch without depending on implementation internals. Inputs: test fixtures and temp directories. Outputs: stable regression coverage for the refactor. Libraries and tools: `pytest`.
- Dependencies: T32, T33, T35

### M3: Add the External Services Needed for the Real Stack

#### Task T37: Create `docker-compose.yml` with named services for Redpanda, Redis, Qdrant, and MLflow
- Description: Add a real compose stack with deterministic service names, ports, volumes, and health checks so the backend can target external infrastructure locally. Inputs: local runtime requirements from settings. Outputs: `docker-compose.yml` and any supporting env files. Libraries and tools: `docker compose`.
- Dependencies: T30

#### Task T38: Add Redpanda service configuration and topic bootstrap script
- Description: Add topic creation logic for the event topics defined in `docs/event-contract.md`, for example `interactions` and `catalog_updates`, plus a connectivity check the test suite or CLI can run. Inputs: compose service endpoints and topic names. Outputs: bootstrapped Kafka-compatible topics. Libraries and tools: `redpanda`, `rpk` or equivalent bootstrap command.
- Dependencies: T37

#### Task T39: Add Redis service configuration and a connectivity probe
- Description: Add Redis to the compose stack and implement a simple connectivity probe such as `ping_redis(settings)` for use by health checks and future service startup. Inputs: Redis host, port, and db from settings. Outputs: verified Redis availability. Libraries and tools: `redis`.
- Dependencies: T37

#### Task T40: Add Qdrant service configuration and collection-management probe
- Description: Add Qdrant to the compose stack and implement a probe such as `ensure_qdrant_connection(settings)` that can create or list collections. Inputs: Qdrant host, port, and collection names from settings. Outputs: verified Qdrant availability. Libraries and tools: `qdrant-client`.
- Dependencies: T37

#### Task T41: Add MLflow tracking server configuration and a run logging probe
- Description: Add MLflow to the compose stack and implement a smoke path that logs one temporary run with params and metrics. Inputs: tracking URI and artifact root from settings. Outputs: verified MLflow tracking and artifact logging. Libraries and tools: `mlflow`.
- Dependencies: T37

### M4: Replace the File-Only Event Publishing Path With Kafka-Compatible Publishing

#### Task T42: Implement a `KafkaReplayPublisher` object for sending replay batches to Redpanda
- Description: Create a publisher object, for example `KafkaReplayPublisher.publish(topic: str, events: list[dict])`, that consumes the current replay artifacts and writes them to Redpanda while preserving payload shape and ordering. Inputs: replay JSONL batches or in-memory event dicts. Outputs: messages published to Kafka-compatible topics. Libraries and tools: `confluent-kafka` or `kafka-python`.
- Dependencies: T38

#### Task T43: Add a CLI command that publishes replay artifacts into broker topics
- Description: Add a command such as `publish-replay-to-kafka` that loads existing replay files produced by `publish_local_replay()` and sends them through `KafkaReplayPublisher`. Inputs: replay manifest path and topic mappings. Outputs: broker-populated topics ready for consumers. Libraries and tools: existing CLI, Kafka client library.
- Dependencies: T42

#### Task T44: Implement broker delivery validation for published replay batches
- Description: Add a validation function such as `validate_broker_replay(settings, manifest_path)` that checks expected message counts and key fields per topic after publishing. Inputs: manifest path and broker connection settings. Outputs: a broker-delivery validation report. Libraries and tools: Kafka client library.
- Dependencies: T43

### M5: Replace the File-Backed Online Feature Store With Redis

#### Task T45: Implement a `RedisOnlineFeatureStore` object with `put_*` and `get_*` methods for session, customer, and article entities
- Description: Create an object that owns online feature reads and writes, for example `put_session_features(customer_id, session_id, payload)`, `put_customer_features(customer_id, payload)`, `put_article_features(article_id, payload)`, plus corresponding getters. Inputs: typed feature payloads. Outputs: Redis hash or JSON records keyed by entity ID. Libraries and tools: `redis`.
- Dependencies: T39, T33

#### Task T46: Refactor `OnlineFeatureService` to read from `RedisOnlineFeatureStore` instead of JSON files
- Description: Replace the current file-backed implementation behind `OnlineFeatureService` with Redis reads while preserving the lookup contract already used by retrieval and future serving code. Inputs: entity IDs and Redis settings. Outputs: the same logical online feature payloads currently returned by `OnlineFeatureService`. Libraries and tools: `redis`.
- Dependencies: T45

#### Task T47: Implement a `FeatureUpdateProcessor` that converts broker events into online feature mutations
- Description: Add an object or function, for example `FeatureUpdateProcessor.apply(event) -> list[FeatureStoreWriteRecord]`, that maps interaction and catalog events to feature store updates for `customer_session`, `customer`, and `article`. Inputs: one broker event at a time. Outputs: feature mutations ready to write into `RedisOnlineFeatureStore`. Libraries and tools: existing feature semantics from `online_feature_requirements()`.
- Dependencies: T33, T45

#### Task T48: Implement a broker consumer that applies feature updates into Redis
- Description: Create a consumer such as `consume_feature_updates(settings)` that reads Redpanda topics, invokes `FeatureUpdateProcessor`, and persists results through `RedisOnlineFeatureStore`. Inputs: subscribed broker topics and event payloads. Outputs: continuously updated Redis online features. Libraries and tools: `confluent-kafka` or `kafka-python`; `redis`.
- Dependencies: T44, T47

#### Task T49: Update feature freshness and parity validation to use Redis-backed reads
- Description: Refactor `validate_feature_parity_and_freshness()` and related helper functions so they compare offline features against Redis-backed online values rather than file-based JSON payloads. Inputs: training dataset rows and Redis-backed online entities. Outputs: freshness and parity reports for the real online store. Libraries and tools: `redis`, existing validation logic.
- Dependencies: T46, T48

### M6: Express the Feature Platform in Feast

#### Task T50: Create a dedicated Feast repository with `feature_store.yaml`, entity definitions, and source definitions
- Description: Add a Feast repo, for example under `backend/feast_repo/`, containing `feature_store.yaml`, entity definitions for `customer`, `article`, and `customer_session`, and offline source definitions pointing to local Parquet artifacts. Inputs: Parquet datasets from T34 and settings from T30. Outputs: a runnable Feast repository. Libraries and tools: `feast[redis]`.
- Dependencies: T34, T39

#### Task T51: Re-express offline feature views from `features.registry()` as Feast feature views
- Description: Map the current logical offline views, including `customer_profile_features`, `article_catalog_features`, `customer_activity_features`, `article_demand_features`, and `customer_article_affinity_features`, into Feast-managed definitions. Inputs: current feature semantics and Parquet sources. Outputs: Feast feature view objects with the same names and semantics where feasible. Libraries and tools: `feast`.
- Dependencies: T50

#### Task T52: Re-express online feature requirements as Feast online feature views backed by Redis
- Description: Map `session_intent_features`, `customer_realtime_features`, and `article_realtime_features` into Feast-managed definitions bound to Redis-backed online serving. Inputs: online feature requirements and Redis store config. Outputs: Feast definitions usable for online retrieval. Libraries and tools: `feast[redis]`, Redis.
- Dependencies: T46, T50

#### Task T53: Add a command to materialize or apply Feast definitions locally
- Description: Add a CLI command such as `apply-feast-repo` or `materialize-features` that validates and applies the Feast repository definitions in local development. Inputs: Feast repo path and settings. Outputs: applied feature definitions and, where appropriate, materialized offline/online state. Libraries and tools: Feast CLI or Python API.
- Dependencies: T51, T52

#### Task T54: Implement a `FeastPointInTimeDatasetBuilder` that replaces custom PIT joins
- Description: Add an object or function, for example `FeastPointInTimeDatasetBuilder.build(entity_df, feature_refs, label_df)`, that builds training rows through Feast point-in-time retrieval rather than direct historical replay logic. Inputs: label rows built from normalized transactions and feature references from the Feast repo. Outputs: point-in-time correct training datasets backed by Feast retrieval. Libraries and tools: `feast`.
- Dependencies: T51, T53

#### Task T55: Update ranking dataset generation to consume Feast-built training rows
- Description: Refactor `build_ranking_dataset()` so it reads candidate and feature inputs produced by `FeastPointInTimeDatasetBuilder` instead of relying solely on the current custom feature-join path. Inputs: Feast-built training rows and retrieval candidates. Outputs: ranking dataset rows with the same label contract and richer feature-store provenance. Libraries and tools: `feast`, existing ranking pipeline.
- Dependencies: T54

### M7: Replace Deterministic Embeddings and Local Vector Indexes

#### Task T56: Introduce a `TextEmbedder` abstraction with a real `SentenceTransformerTextEmbedder` implementation
- Description: Define an interface such as `TextEmbedder.embed_articles(rows) -> list[EmbeddingArtifactRecord]` and implement a model-backed version using product text fields like `prod_name`, `product_type_name`, `product_group_name`, `colour_group_name`, `department_name`, and `detail_desc`. Inputs: normalized article rows. Outputs: text embedding records with model metadata and vectors. Libraries and tools: `sentence-transformers`, `transformers`, `torch`.
- Dependencies: T34, T33

#### Task T57: Introduce an `ImageEmbedder` abstraction with a real `OpenClipImageEmbedder` implementation
- Description: Define an interface such as `ImageEmbedder.embed_images(records) -> list[EmbeddingArtifactRecord]` and implement a model-backed version using product image paths from the image manifest. Inputs: image manifest rows and local image files. Outputs: image embedding records with model metadata and vectors. Libraries and tools: `open_clip_torch`, `torch`, image preprocessing utilities.
- Dependencies: T34, T33

#### Task T58: Refactor `build_embedding_artifacts()` to use pluggable embedder implementations
- Description: Update `build_embedding_artifacts()` so it can run with the current hash-based embedders during fallback mode and the real model-backed embedders during the production-oriented path. Inputs: article rows, image manifest rows, embedder objects, and settings. Outputs: text, image, and fused embedding artifacts with stable manifest shape. Libraries and tools: existing retrieval pipeline plus new embedder abstractions.
- Dependencies: T56, T57

#### Task T59: Implement a `QdrantIndexManager` that creates collections and upserts embedding records
- Description: Add an object such as `QdrantIndexManager.ensure_collection(name, dimension)` and `QdrantIndexManager.upsert(records)` that owns all Qdrant interactions for text and fused retrieval collections. Inputs: embedding artifact records and collection config. Outputs: populated Qdrant collections. Libraries and tools: `qdrant-client`.
- Dependencies: T40, T58

#### Task T60: Add a command that loads embedding artifacts into Qdrant collections
- Description: Add a CLI command such as `build-qdrant-index` that reads the persisted embedding artifacts and populates text and fused collections through `QdrantIndexManager`. Inputs: embedding manifest paths and Qdrant settings. Outputs: searchable Qdrant collections. Libraries and tools: existing CLI, `qdrant-client`.
- Dependencies: T59

#### Task T61: Implement a `QdrantCandidateRetriever` that preserves the current `RetrievalRequest -> RetrievalResult` contract
- Description: Replace the local in-memory vector search in `CandidateRetriever` with Qdrant-backed nearest-neighbor retrieval while preserving request fields such as `query_text`, `seed_article_ids`, and request-context payloads. Inputs: `RetrievalRequest`, Qdrant collections, and optional online features. Outputs: `RetrievalResult` with ranked `CandidateRecord` entries. Libraries and tools: `qdrant-client`.
- Dependencies: T59

#### Task T62: Update candidate retrieval to enrich requests with Feast and Redis online context
- Description: Refactor retrieval request assembly so session and customer context comes from `OnlineFeatureService` backed by Redis and, where appropriate, Feast online retrieval. Inputs: customer ID, session ID, optional query text, optional seed articles. Outputs: a fully hydrated retrieval request and Qdrant-backed candidate result set. Libraries and tools: `feast`, `redis`, `qdrant-client`.
- Dependencies: T52, T61

### M8: Replace the File-Backed Model Platform With MLflow and a Library-Backed Ranker

#### Task T63: Implement an `MLflowRunLogger` wrapper for params, metrics, tags, and artifact logging
- Description: Add a wrapper such as `MLflowRunLogger.log_training_run(...)` so training code no longer writes only local manifest files. Inputs: training config, dataset references, metrics, and artifact paths. Outputs: MLflow runs with reproducible metadata. Libraries and tools: `mlflow`.
- Dependencies: T41, T55

#### Task T64: Refactor `train_local_ranking_model()` to log training results through `MLflowRunLogger`
- Description: Update the training flow so the ranking trainer emits params, metrics, feature schema summaries, and model artifacts into MLflow while optionally preserving local manifests as secondary outputs. Inputs: ranking dataset path, training config, and artifact paths. Outputs: trained model artifacts plus an MLflow run ID. Libraries and tools: `mlflow`, existing ranking code.
- Dependencies: T63

#### Task T65: Implement an `MLflowModelRegistrar` that registers trained ranking models into the MLflow Model Registry
- Description: Add an object such as `MLflowModelRegistrar.register(model_uri, name, tags)` that replaces the file-backed promotion path in `register_candidate_ranking_model()`. Inputs: MLflow run outputs and registration metadata. Outputs: MLflow model versions and stage metadata. Libraries and tools: `mlflow`.
- Dependencies: T64

#### Task T66: Add a `LightGBMRankerTrainer` or `XGBoostRankerTrainer` implementation behind a ranking trainer abstraction
- Description: Define a trainer interface and implement a stronger library-backed baseline that consumes the ranking dataset features and labels already produced by the pipeline. Inputs: ranking Parquet dataset, feature schema, and training config. Outputs: fitted ranking model artifact, feature importance data, and evaluation metrics. Libraries and tools: `lightgbm` or `xgboost`, `mlflow`.
- Dependencies: T55, T63

#### Task T67: Update ranking evaluation to score MLflow-registered models rather than only local artifacts
- Description: Refactor ranking evaluation so it can load the chosen model version from MLflow and evaluate it against held-out ranking rows. Inputs: MLflow model URI or registered model version plus evaluation dataset. Outputs: offline ranking metrics tied to a model registry version. Libraries and tools: `mlflow`.
- Dependencies: T65, T66

### M9: Build the Actual Evaluation and Recommendation Serving Paths

#### Task T68: Implement an `OfflineRetrievalEvaluator` for Recall@K, MRR, and NDCG on Qdrant-backed candidates
- Description: Add an evaluator object that consumes retrieval requests plus ground-truth labels and computes retrieval metrics against `QdrantCandidateRetriever`. Inputs: evaluation query set, ground-truth article labels, and retriever config. Outputs: retrieval metric reports and per-slice summaries. Libraries and tools: `qdrant-client`, existing retrieval contracts.
- Dependencies: T61

#### Task T69: Implement an `OfflineRankingEvaluator` for Precision@K, MAP@K, NDCG@K, and pairwise quality
- Description: Add an evaluator object that consumes ranked candidate lists and held-out labels from the ranking dataset and computes offline ranking quality metrics. Inputs: model version, evaluation ranking rows, and scoring pipeline. Outputs: ranking metric reports linked to an MLflow run or registered model version. Libraries and tools: existing ranking code plus `mlflow`.
- Dependencies: T67

#### Task T70: Add API request and response models for recommendation serving
- Description: Implement explicit serving models such as `RecommendationRequest`, `RecommendationItem`, and `RecommendationResponse` so the API does not rely on untyped dictionaries. Inputs: HTTP JSON payloads. Outputs: validated request and response objects. Libraries and tools: `pydantic`.
- Dependencies: T33

#### Task T71: Implement a `RecommendationService` orchestration object
- Description: Add a service object such as `RecommendationService.recommend(request)` that fetches online features, calls `QdrantCandidateRetriever`, loads the selected ranking model, scores candidates, and returns ordered recommendation items. Inputs: `RecommendationRequest`, online features, retriever, and model registry reference. Outputs: ranked recommendations and supporting metadata such as model version and feature freshness context. Libraries and tools: `feast`, `redis`, `qdrant-client`, `mlflow`.
- Dependencies: T62, T65, T66, T70

#### Task T72: Expose `RecommendationService` through a FastAPI application
- Description: Add a FastAPI app with endpoints such as `POST /recommendations` and `GET /healthz`, wiring settings, dependency injection, and model/service initialization cleanly. Inputs: HTTP requests and application settings. Outputs: live API responses and health checks. Libraries and tools: `fastapi`, `uvicorn`.
- Dependencies: T71

#### Task T73: Add timeout, fallback, and validation behavior to the API path
- Description: Add explicit fallback rules for missing online features, Qdrant failures, Redis failures, and model lookup failures, plus request validation limits and timeout budgets. Inputs: `RecommendationRequest` and dependency health state. Outputs: deterministic degraded-mode responses and structured errors. Libraries and tools: `fastapi`, `pydantic`.
- Dependencies: T72

#### Task T74: Implement an `ExperimentAssigner` and `ExposureLogger` for online experimentation
- Description: Add objects that assign incoming requests to retrieval and ranking variants and emit exposure events to Redpanda for later analysis. Inputs: request identity, experiment config, served model versions, and candidate/ranking metadata. Outputs: experiment assignment decisions and broker-published exposure events. Libraries and tools: FastAPI middleware or service-layer hooks, `confluent-kafka` or `kafka-python`.
- Dependencies: T72

### M10: Add Observability, Orchestration, and Final Documentation

#### Task T75: Instrument API, retrieval, ranking, and feature flows with Prometheus metrics
- Description: Add metrics for request count, request latency, Redis lookup latency, Qdrant retrieval latency, ranking latency, fallback count, broker consumer lag, and feature freshness staleness. Inputs: API and pipeline runtime events. Outputs: Prometheus-exposed metrics suitable for dashboards and alerts. Libraries and tools: `prometheus-client`.
- Dependencies: T48, T72, T73

#### Task T76: Add Prometheus and Grafana services plus a baseline dashboard
- Description: Extend the compose stack with Prometheus and Grafana and add at least one dashboard that visualizes API health, retrieval latency, ranking latency, and feature freshness. Inputs: Prometheus metrics endpoint and compose network config. Outputs: local observability dashboard and scrape config. Libraries and tools: Prometheus, Grafana.
- Dependencies: T37, T75

#### Task T77: Add Dagster assets and jobs for ingestion, feature materialization, embedding generation, training, and evaluation
- Description: Define Dagster assets or jobs that orchestrate the major batch workflows and capture dependencies between ingestion, Parquet generation, Feast application, embedding builds, Qdrant indexing, training, and offline evaluation. Inputs: settings, CLI/service functions, and artifact paths. Outputs: orchestrated local workflows with explicit lineage. Libraries and tools: `dagster`.
- Dependencies: T55, T60, T67, T69

#### Task T78: Update the system design and operating docs to match the implemented stack
- Description: Revise architecture, deployment, and operations docs so they document the actual local stack, the implemented service boundaries, the concrete libraries in use, and the production promotion path. Inputs: final code and compose topology. Outputs: updated project documentation with no remaining plan-to-code mismatches. Libraries and tools: documentation only.
- Dependencies: T76, T77

## Revisions
- v1.4: Replaced the post-`T29` roadmap with smaller implementation-grade tasks that name concrete objects, functions, inputs, outputs, and external libraries.
- v1.3: Replaced the still-broad post-`T29` roadmap from v1.2 with narrower execution tasks, each with a clearer outcome and explicit library/runtime target.
- v1.2: Reframed `T1`-`T29` as completed local baselines, inserted a mandatory backend refactor before further platform work, and replaced the vague remainder of the roadmap with library-specific integration tasks for streaming, feature serving, vector search, model registry, serving, observability, and orchestration.
- v1.1: Replaced coarse implementation tasks from v1.0 with more granular execution steps, removed speculative file-level references where ownership is not yet known, and preserved the same overall delivery scope.
- v1.0: Initial version.
