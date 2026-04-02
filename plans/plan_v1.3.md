# Plan v1.3

## Context
`T1` through `T29` produced a working local baseline, but the remaining roadmap was still too abstract to execute cleanly. Several completed tasks proved only the contract shape, not the production-oriented stack described in the system design. In particular, Kafka-compatible messaging, Redis-backed online features, Feast-managed feature definitions, Qdrant-backed retrieval, MLflow-backed tracking, and a real API runtime are still missing.

This version keeps the baseline work as completed, then rewrites the remaining roadmap into narrower execution tasks. Each task now states a concrete outcome and the main library or runtime being introduced so the next implementation steps are unambiguous.

## Milestones

### M1: Completed Baseline

#### Task T1: Confirm project scope and success criteria
- Description: Consolidate the project goals, required capabilities, constraints, and non-goals into a stable scope baseline.
- Dependencies: None

#### Task T2: Record initial architecture direction
- Description: Capture the high-level architecture, core subsystems, and major technology choices.
- Dependencies: T1

#### Task T3: Publish the first execution plan and tracking artifacts
- Description: Create the initial versioned plan and checklist.
- Dependencies: T2

#### Task T4: Refine the plan into execution-sized tasks
- Description: Replace broad work packages with smaller implementation-ready tasks.
- Dependencies: T3

#### Task T5: Define the source dataset contract
- Description: Document expected schemas, keys, required fields, and quality assumptions for source data.
- Dependencies: T4

#### Task T6: Define local storage and dataset layout conventions
- Description: Define how raw, normalized, and derived datasets are organized locally.
- Dependencies: T5

#### Task T7: Build raw dataset ingestion
- Description: Implement reproducible loading of the H&M source dataset into the local project layout.
- Dependencies: T6

#### Task T8: Build product normalization
- Description: Transform raw product records into cleaned article outputs.
- Dependencies: T7

#### Task T9: Build customer normalization
- Description: Transform raw customer records into cleaned customer outputs.
- Dependencies: T7

#### Task T10: Build transaction normalization
- Description: Transform raw transaction history into cleaned event-style records.
- Dependencies: T7

#### Task T11: Validate normalized dataset outputs
- Description: Add schema, uniqueness, null-handling, and row-level validation for normalized outputs.
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
- Description: Verify ordering, timestamps, completeness, and replay behavior.
- Dependencies: T15

#### Task T17: Define offline feature entities and views
- Description: Specify offline feature entities, feature sets, and source mappings.
- Dependencies: T11

#### Task T18: Build point-in-time correct training joins
- Description: Implement historical feature retrieval without label leakage.
- Dependencies: T17

#### Task T19: Define online feature requirements
- Description: Identify freshness-sensitive features and the events that update them.
- Dependencies: T16, T17

#### Task T20: Build baseline streaming feature computation
- Description: Compute online feature snapshots from replay artifacts.
- Dependencies: T19

#### Task T21: Expose baseline online feature serving
- Description: Serve baseline online features from the local file-backed store.
- Dependencies: T20

#### Task T22: Validate baseline feature parity and freshness
- Description: Check offline-online semantic parity and freshness targets against the baseline implementation.
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

### M2: Refactor the Current Code Before More Features

#### Task T30: Split backend code into stable module boundaries
- Description: Reorganize the package so `ingestion`, `events`, `features`, `retrieval`, `ranking`, and `serving` have clear ownership and do not depend on each other's internal files.
- Libraries and tools: Python package refactor, existing tests.
- Dependencies: T29

#### Task T31: Introduce typed application configuration
- Description: Replace scattered path and runtime constants with a typed settings layer for storage paths, broker endpoints, Redis, Qdrant, and MLflow.
- Libraries and tools: `pydantic`, `pydantic-settings`.
- Dependencies: T30

#### Task T32: Separate CLI commands by subsystem
- Description: Refactor the current CLI so ingestion, replay, features, retrieval, training, and serving commands are grouped by domain and can evolve independently.
- Libraries and tools: existing CLI or `typer`.
- Dependencies: T30

#### Task T33: Convert core persisted datasets to Parquet
- Description: Change normalized outputs, PIT datasets, ranking datasets, and evaluation-ready artifacts from ad hoc CSV/JSON files to Parquet-backed outputs.
- Libraries and tools: `pyarrow`.
- Dependencies: T31

#### Task T34: Update tests around the refactored contracts
- Description: Rewrite unit and integration tests so they validate the new module boundaries, settings layer, CLI surface, and Parquet contracts.
- Libraries and tools: `pytest`.
- Dependencies: T32, T33

### M3: Add the Missing Local Infrastructure

#### Task T35: Create the Docker Compose stack
- Description: Add a real `docker-compose.yml` that boots the external services needed by the next milestones.
- Libraries and tools: `docker compose`.
- Dependencies: T31

#### Task T36: Add Kafka-compatible messaging with Redpanda
- Description: Add a Redpanda service, topic bootstrap, and local connectivity checks for interaction and catalog topics.
- Libraries and tools: `redpanda`.
- Dependencies: T35

#### Task T37: Add Redis for online feature serving
- Description: Add a Redis service and verify the backend can connect to it through the typed settings layer.
- Libraries and tools: `redis`.
- Dependencies: T35

#### Task T38: Add Qdrant for vector retrieval
- Description: Add a Qdrant service and verify collection creation and query connectivity from the backend.
- Libraries and tools: `qdrant`, `qdrant-client`.
- Dependencies: T35

#### Task T39: Add MLflow for experiment tracking and model registry
- Description: Add an MLflow tracking server and verify model artifacts and metrics can be logged locally.
- Libraries and tools: `mlflow`.
- Dependencies: T35

### M4: Replace the Fake Streaming Path

#### Task T40: Publish replay events into Redpanda topics
- Description: Replace file-only publishing with real broker publishing while preserving the current event payload contract.
- Libraries and tools: `confluent-kafka` or `kafka-python`, `redpanda`.
- Dependencies: T36

#### Task T41: Add a broker consumer for feature updates
- Description: Create a streaming consumer that reads interaction and catalog topics and emits feature-update records.
- Libraries and tools: `pyspark` or a Python Kafka consumer.
- Dependencies: T40

#### Task T42: Persist online features into Redis
- Description: Replace the file-backed online store with Redis-backed online feature writes and reads.
- Libraries and tools: `redis-py`, Redis.
- Dependencies: T37, T41

#### Task T43: Re-validate online feature freshness on the real stack
- Description: Re-run freshness and parity validation against broker-backed updates and Redis-backed serving.
- Libraries and tools: existing validation suite, Redis.
- Dependencies: T42

### M5: Replace the Fake Feature Platform

#### Task T44: Create the Feast repository layout
- Description: Add a Feast repo with feature store configuration, entities, feature views, and data source definitions.
- Libraries and tools: `feast[redis]`.
- Dependencies: T33, T37

#### Task T45: Map existing offline feature definitions into Feast
- Description: Re-express the current offline feature registry as Feast entities and feature views without changing feature semantics.
- Libraries and tools: `feast`.
- Dependencies: T44

#### Task T46: Map existing online feature definitions into Feast
- Description: Re-express the current online feature contract in Feast and bind it to Redis-backed online serving.
- Libraries and tools: `feast[redis]`, Redis.
- Dependencies: T42, T44

#### Task T47: Rebuild point-in-time training retrieval through Feast
- Description: Replace the custom historical join path with Feast-backed point-in-time feature retrieval.
- Libraries and tools: `feast`.
- Dependencies: T45, T46

### M6: Replace the Fake Retrieval Stack

#### Task T48: Introduce real text encoders
- Description: Replace deterministic text embeddings with model-backed text embeddings while preserving the current embedding artifact shape.
- Libraries and tools: `sentence-transformers`, `transformers`, `torch`.
- Dependencies: T33, T35

#### Task T49: Introduce real image encoders
- Description: Replace deterministic image embeddings with model-backed image embeddings while preserving the current embedding artifact shape.
- Libraries and tools: `open_clip_torch` or equivalent, `torch`.
- Dependencies: T33, T35

#### Task T50: Load embeddings into Qdrant collections
- Description: Replace JSONL vector indexes with Qdrant collections and collection rebuild flows.
- Libraries and tools: `qdrant-client`, Qdrant.
- Dependencies: T38, T48, T49

#### Task T51: Rebuild candidate retrieval against Qdrant and Feast
- Description: Retrieve candidates from Qdrant and enrich the request path with Redis/Feast-served online features.
- Libraries and tools: `qdrant-client`, `feast`, Redis.
- Dependencies: T46, T50

### M7: Replace the Fake Model Platform

#### Task T52: Log training runs to MLflow
- Description: Replace the file-only run metadata path with MLflow run logging for params, metrics, and artifacts.
- Libraries and tools: `mlflow`.
- Dependencies: T39, T47

#### Task T53: Register trained models in MLflow Model Registry
- Description: Replace the file-backed candidate registry with MLflow model registration and version promotion.
- Libraries and tools: `mlflow`.
- Dependencies: T52

#### Task T54: Upgrade ranking training to a library-backed baseline
- Description: Replace the custom trainer with a stronger baseline that still fits local development and integrates with MLflow.
- Libraries and tools: `lightgbm` or `xgboost`, `mlflow`.
- Dependencies: T47, T52

### M8: Build the Actual Serving and Evaluation Paths

#### Task T55: Build offline retrieval evaluation
- Description: Compute retrieval metrics from Qdrant-backed candidates and Feast-backed features.
- Libraries and tools: `qdrant-client`, `feast`.
- Dependencies: T51, T53

#### Task T56: Build offline ranking evaluation
- Description: Compute ranking metrics from MLflow-registered models and Feast-backed datasets.
- Libraries and tools: `mlflow`, `feast`.
- Dependencies: T53, T54

#### Task T57: Build the FastAPI recommendation service
- Description: Expose an API that fetches online features, retrieves candidates, scores them, and returns recommendations.
- Libraries and tools: `fastapi`, `uvicorn`, `feast`, `qdrant-client`, `mlflow`.
- Dependencies: T51, T53, T54

#### Task T58: Add inference safeguards and fallback behavior
- Description: Add request validation, timeout handling, dependency-health checks, and degraded-mode fallback responses.
- Libraries and tools: `fastapi`, `pydantic`.
- Dependencies: T57

#### Task T59: Add experiment assignment and exposure logging
- Description: Assign requests to retrieval or ranking variants and emit exposure events for later analysis.
- Libraries and tools: FastAPI middleware, `redpanda`.
- Dependencies: T57

### M9: Operability and Delivery

#### Task T60: Add metrics instrumentation to the API and pipelines
- Description: Emit metrics for request latency, broker lag, feature freshness, retrieval latency, and ranking latency.
- Libraries and tools: `prometheus-client`.
- Dependencies: T43, T57, T58

#### Task T61: Add Prometheus and Grafana to the local stack
- Description: Add dashboards and alert baselines for the core runtime and recommendation path.
- Libraries and tools: Prometheus, Grafana.
- Dependencies: T35, T60

#### Task T62: Add Dagster orchestration for batch jobs
- Description: Orchestrate ingestion, normalization, feature materialization, embedding generation, training, and evaluation as explicit jobs/assets.
- Libraries and tools: `dagster`.
- Dependencies: T47, T53, T56

#### Task T63: Finalize deployment and system design documentation
- Description: Update the architecture and operational docs so they match the implemented local stack and its intended production promotion path.
- Libraries and tools: documentation only.
- Dependencies: T61, T62

## Revisions
- v1.3: Replaced the still-broad post-`T29` roadmap from v1.2 with narrower execution tasks, each with a clearer outcome and explicit library/runtime target.
- v1.2: Reframed `T1`-`T29` as completed local baselines, inserted a mandatory backend refactor before further platform work, and replaced the vague remainder of the roadmap with library-specific integration tasks for streaming, feature serving, vector search, model registry, serving, observability, and orchestration.
- v1.1: Replaced coarse implementation tasks from v1.0 with more granular execution steps, removed speculative file-level references where ownership is not yet known, and preserved the same overall delivery scope.
- v1.0: Initial version.
