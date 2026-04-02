# Plan v1.2

## Context
The current implementation completed `T1` through `T29` as local, dependency-light baselines. That delivered useful contracts and artifact boundaries, but the plan drifted away from the intended production-oriented stack: broker-backed streaming is not wired, the online store is still file-backed, vector indexing is still JSONL-backed, and model registration is still file-backed. This version corrects the roadmap by inserting a refactor-and-integration phase before more evaluation and serving work.

This plan keeps the completed baseline work, but reclassifies it as scaffolding that must now be hardened and migrated onto explicit external libraries and local infrastructure. The next tasks are intentionally concrete about the tools to introduce so execution does not depend on unstated assumptions.

## Milestones

### M1: Foundation and Planning Baseline

#### Task T1: Confirm project scope and success criteria
- Description: Consolidate the project goals, required capabilities, constraints, and non-goals into a stable scope baseline that the rest of the implementation can follow.
- Dependencies: None

#### Task T2: Record initial architecture direction
- Description: Capture the high-level architecture, core subsystems, and major technology choices that shape the first implementation pass.
- Dependencies: T1

#### Task T3: Publish the first execution plan and tracking artifacts
- Description: Create the initial versioned plan and checklist used to track implementation work.
- Dependencies: T2

#### Task T4: Refine the plan into execution-sized tasks
- Description: Replace broad work packages with smaller, implementation-ready tasks and update the versioned planning artifacts accordingly.
- Dependencies: T3

### M2: Dataset and Data Contracts Baseline

#### Task T5: Define the source dataset contract
- Description: Document the expected schemas, required fields, primary keys, and quality assumptions for users, products, transactions, and image-related data.
- Dependencies: T4

#### Task T6: Define local storage and dataset layout conventions
- Description: Decide how raw, normalized, and derived datasets will be organized locally so ingestion and downstream jobs use a predictable structure.
- Dependencies: T5

#### Task T7: Build raw dataset ingestion
- Description: Implement reproducible loading of the H&M source dataset into the local project environment.
- Dependencies: T6

#### Task T8: Build product normalization
- Description: Transform raw product records into a cleaned and standardized representation suitable for feature generation and retrieval.
- Dependencies: T7

#### Task T9: Build customer normalization
- Description: Transform raw customer records into a cleaned and standardized representation suitable for downstream feature computation.
- Dependencies: T7

#### Task T10: Build transaction normalization
- Description: Transform raw transaction history into a cleaned event-style dataset with timestamps and identifiers that support training and evaluation.
- Dependencies: T7

#### Task T11: Validate normalized dataset outputs
- Description: Add checks that verify schema consistency, key uniqueness, null handling, and basic row-count expectations across normalized datasets.
- Dependencies: T8, T9, T10

### M3: Local Event and Feature Baseline

#### Task T12: Define event schemas for simulated online behavior
- Description: Specify the event types, required fields, and topic boundaries for interactions, catalog changes, and other replayed online signals.
- Dependencies: T11

#### Task T13: Implement synthetic interaction generation
- Description: Generate realistic user interaction events that reflect browsing, engagement, and purchase-related behaviors for local development.
- Dependencies: T12

#### Task T14: Implement catalog change event generation
- Description: Generate realistic product update events such as inventory, metadata, and availability changes.
- Dependencies: T12

#### Task T15: Implement local event publishing and replay
- Description: Publish generated events into the local replay format and support deterministic replay for repeatable testing.
- Dependencies: T13, T14

#### Task T16: Validate replayed event quality
- Description: Verify ordering, timestamps, payload completeness, and replay behavior so downstream streaming consumers can rely on the simulated feed.
- Dependencies: T15

#### Task T17: Define offline feature entities and views
- Description: Specify the feature entities, offline feature sets, and source mappings needed for training and batch scoring.
- Dependencies: T11

#### Task T18: Build point-in-time correct training joins
- Description: Implement historical feature retrieval that prevents leakage and produces reproducible training datasets.
- Dependencies: T17

#### Task T19: Define online feature requirements
- Description: Identify which features must be served online, their freshness expectations, and which streaming inputs update them.
- Dependencies: T16, T17

#### Task T20: Build baseline streaming feature computation
- Description: Implement the first near-real-time aggregation logic over replay artifacts so online feature semantics can be tested before broker integration.
- Dependencies: T19

#### Task T21: Expose baseline online feature serving
- Description: Connect computed online features to the local file-backed serving abstraction and verify they can be retrieved consistently at inference time.
- Dependencies: T20

#### Task T22: Validate baseline feature parity and freshness
- Description: Add checks that compare offline and online feature semantics and confirm freshness targets against the baseline local implementation.
- Dependencies: T18, T21

### M4: Local Retrieval and Ranking Baseline

#### Task T23: Define multimodal representation strategy
- Description: Decide how text, image, and structured product signals will be combined into retrieval-ready representations.
- Dependencies: T11, T17

#### Task T24: Build baseline embedding generation pipeline
- Description: Generate deterministic local embeddings for the required modalities and persist them in a form suitable for indexing and reuse before model-backed encoders are introduced.
- Dependencies: T23

#### Task T25: Build baseline vector indexing pipeline
- Description: Load baseline embeddings into a rebuildable local index representation and support refresh or rebuild flows for development.
- Dependencies: T24

#### Task T26: Implement baseline candidate retrieval logic
- Description: Expose retrieval behavior that queries the local index and returns candidate products for a given request context.
- Dependencies: T25, T21

#### Task T27: Build ranking dataset generation
- Description: Assemble ranking training examples by combining retrieval candidates, labels, and point-in-time correct features.
- Dependencies: T18, T26

#### Task T28: Implement baseline ranking model training
- Description: Train the first deterministic ranking baseline with reproducible configuration, tracked runs, and model artifacts ready for evaluation.
- Dependencies: T27

#### Task T29: Register baseline candidate models and metadata
- Description: Persist trained model versions, lineage, and metadata in the local registry so evaluation and serving can reference approved artifacts.
- Dependencies: T28

### M5: Codebase Refactor and Runtime Foundations

#### Task T30: Refactor the backend into explicit pipeline, domain, and serving boundaries
- Description: Reorganize the current code so ingestion, eventing, features, retrieval, ranking, and serving each expose clear service interfaces, shared schemas, and configuration entrypoints instead of accumulating more behavior in the current flat package layout.
- Libraries and tools: `pydantic`, `pydantic-settings`, `typer` or the existing CLI surface, Python package refactor, test-suite updates.
- Dependencies: T29

#### Task T31: Introduce environment-aware configuration and dependency management
- Description: Centralize local runtime configuration for broker endpoints, Redis, Feast repo paths, MLflow tracking URI, Qdrant connection details, and model/feature storage locations so later integrations do not hardcode paths or ports.
- Libraries and tools: `pydantic-settings`, Poetry dependency groups, `.env` support, Docker Compose environment wiring.
- Dependencies: T30

#### Task T32: Migrate core artifacts from ad hoc JSON and CSV outputs to Parquet-first storage contracts
- Description: Promote normalized datasets, feature snapshots, training sets, and evaluation outputs onto Parquet-backed contracts so Spark, Feast, and ML tooling can consume the same artifacts without translation layers.
- Libraries and tools: `pyarrow`, optionally `polars` for local transforms, existing validation suite.
- Dependencies: T31

#### Task T33: Add a real local infrastructure stack in Docker Compose
- Description: Create the local runtime needed for the rest of the roadmap and verify it boots coherently for development.
- Libraries and tools: `docker compose`, `redpanda` for Kafka-compatible messaging, `redis`, `qdrant`, `mlflow`, optional `minio`, shared healthchecks.
- Dependencies: T31

### M6: Streaming and Feature Platform Integration

#### Task T34: Wire replay publishing into Kafka-compatible topics
- Description: Replace file-only event publishing with broker publishing while preserving deterministic replay inputs and topic contracts.
- Libraries and tools: `redpanda`, `kafka-python` or `confluent-kafka`, existing replay manifests, Docker Compose topics/bootstrap scripts.
- Dependencies: T33

#### Task T35: Implement broker-backed streaming feature computation
- Description: Replace the replay-only feature computation path with a real stream consumer that reads interaction and catalog topics and emits online feature updates.
- Libraries and tools: `pyspark` with Spark Structured Streaming, Kafka source connector, Parquet checkpoints/state, Redis update sink.
- Dependencies: T32, T34

#### Task T36: Stand up a Feast repository for offline and online feature definitions
- Description: Move feature definitions into Feast objects so offline retrieval and online serving share one declarative feature contract.
- Libraries and tools: `feast[redis]`, Redis online store, Parquet or file-based offline store for local dev.
- Dependencies: T32, T33

#### Task T37: Connect streaming outputs to the online feature store
- Description: Ensure the broker-backed streaming job writes freshness-sensitive features into Redis in the shape expected by Feast online serving and by the recommendation service.
- Libraries and tools: `redis`, `feast[redis]`, `pyspark`, integration tests against running services.
- Dependencies: T35, T36

#### Task T38: Rebuild point-in-time training retrieval through Feast
- Description: Replace the custom historical join path with Feast-backed offline retrieval while preserving leakage-safe semantics and validation coverage.
- Libraries and tools: `feast`, `pyarrow`, existing parity and training-dataset tests.
- Dependencies: T36

### M7: Retrieval and Model Platform Integration

#### Task T39: Replace deterministic embeddings with model-backed multimodal encoders
- Description: Introduce real text and image encoders while preserving the current embedding artifact contract and fallback behavior.
- Libraries and tools: `sentence-transformers`, `transformers`, `open_clip_torch` or equivalent CLIP-compatible image encoder, `torch`.
- Dependencies: T32, T33

#### Task T40: Replace file-backed vector indexes with Qdrant collections
- Description: Load embedding artifacts into Qdrant, define collection schemas, and support rebuild and refresh workflows against the running local vector database.
- Libraries and tools: `qdrant-client`, Qdrant Docker service, collection bootstrap scripts.
- Dependencies: T33, T39

#### Task T41: Rebuild candidate retrieval on the production-oriented stack
- Description: Update retrieval to query Qdrant, enrich requests with Feast-served online features, and preserve the current request/response contract for downstream ranking.
- Libraries and tools: `qdrant-client`, `feast`, `redis`, service-level integration tests.
- Dependencies: T37, T40

#### Task T42: Replace the local training registry with MLflow tracking and model registry
- Description: Log training runs, parameters, metrics, model artifacts, and promotion metadata in MLflow so offline evaluation and serving consume a real registry.
- Libraries and tools: `mlflow`, local tracking server in Docker Compose, artifact store on local filesystem or `minio`.
- Dependencies: T33, T38

#### Task T43: Upgrade ranking training to an external ML library baseline
- Description: Move beyond the custom deterministic trainer to a stronger baseline that still trains locally and integrates cleanly with MLflow.
- Libraries and tools: `lightgbm` or `xgboost`, `mlflow`, Parquet datasets, existing ranking feature pipeline.
- Dependencies: T38, T42

### M8: Evaluation, Serving, and Experimentation

#### Task T44: Build the offline evaluation pipeline on registered models and real retrieval infrastructure
- Description: Compute retrieval and ranking metrics from MLflow-registered models, Feast-backed features, and Qdrant-backed candidate generation in a repeatable evaluation workflow.
- Libraries and tools: `mlflow`, `qdrant-client`, `feast`, `pyarrow` or `polars`.
- Dependencies: T41, T42, T43

#### Task T45: Implement the recommendation API service
- Description: Build the end-to-end serving path that fetches online features, runs retrieval and ranking, and returns recommendation results through an application interface.
- Libraries and tools: `fastapi`, `uvicorn`, `feast`, `qdrant-client`, MLflow model loading.
- Dependencies: T41, T42, T43

#### Task T46: Add online inference safeguards and fallbacks
- Description: Add request validation, timeout budgets, degraded-mode fallbacks, and model/version selection controls so the serving path behaves predictably when dependencies are stale or unavailable.
- Libraries and tools: `fastapi`, `pydantic`, structured logging, service integration tests.
- Dependencies: T45

#### Task T47: Implement experiment routing and exposure logging
- Description: Add variant assignment, exposure events, and outcome capture so retrieval and ranking versions can be compared consistently.
- Libraries and tools: FastAPI middleware or service layer routing, Kafka-compatible event emission via Redpanda, experiment metadata persisted in PostgreSQL or structured event logs.
- Dependencies: T45

### M9: Observability, Orchestration, and Delivery

#### Task T48: Add metrics, dashboards, and alert baselines
- Description: Instrument broker lag, feature freshness, retrieval latency, ranking latency, API error rates, and model-serving health, then surface them in local dashboards.
- Libraries and tools: `prometheus-client`, Prometheus, Grafana, Redpanda and Redis exporter integrations where needed.
- Dependencies: T35, T45, T46

#### Task T49: Implement orchestrated workflows for batch and operational jobs
- Description: Define and run orchestrated jobs for ingestion, normalization, feature definitions, feature materialization, embedding refresh, training, and evaluation.
- Libraries and tools: `dagster`, Dagster asset/jobs definitions, Docker Compose service wiring, MLflow and Feast integration points.
- Dependencies: T38, T42, T44

#### Task T50: Document the production deployment path and finalize the system design
- Description: Publish the corrected production narrative, deployment topology, tradeoffs, and operational runbooks that match the implemented local stack and its planned promotion path.
- Libraries and tools: documentation only; should reference the chosen stack from `redpanda`, `feast`, `redis`, `qdrant`, `mlflow`, `fastapi`, `prometheus`, `grafana`, and `dagster`.
- Dependencies: T48, T49

## Revisions
- v1.2: Reframed `T1`-`T29` as completed local baselines, inserted a mandatory backend refactor before further platform work, and replaced the vague remainder of the roadmap with library-specific integration tasks for streaming, feature serving, vector search, model registry, serving, observability, and orchestration.
- v1.1: Replaced coarse implementation tasks from v1.0 with more granular execution steps, removed speculative file-level references where ownership is not yet known, and preserved the same overall delivery scope.
- v1.0: Initial version.
