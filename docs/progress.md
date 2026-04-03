# Project Progress

This is the append-only execution log for the recommendation system project. Each entry records when work started or ended and references the active plan version and task identifier where applicable.

## Plan v1.0
[2026-04-01 18:15:06] [plan v1.0] [START] T1: Define project scope, dataset strategy, and initial documentation structure
[2026-04-01 18:15:06] [plan v1.0] [DONE] T1: Defined project scope, dataset strategy, and created initial system design and learning documents
[2026-04-01 18:15:06] [plan v1.0] [START] T2: Create initial implementation plan and execution checklist
[2026-04-01 18:15:06] [plan v1.0] [DONE] T2: Created plan v1.0 and matching checklist for end-to-end implementation
[2026-04-01 21:23:01] [plan v1.0] [START] T1: Create a contract-style project charter covering context, objectives, deliverables, and expectations
[2026-04-01 21:23:01] [plan v1.0] [DONE] T1: Added project charter document summarizing the engagement scope and acceptance criteria

---
## Plan v1.1
[2026-04-01 21:59:26] [plan v1.1] [START] T5: Define the H&M source dataset contract for customers, products, transactions, and images
[2026-04-01 21:59:26] [plan v1.1] [DONE] T5: Added a source dataset contract document with schemas, keys, required fields, and quality rules
[2026-04-01 21:59:26] [plan v1.1] [START] T6: Define local storage and dataset layout conventions for raw and derived assets
[2026-04-01 21:59:26] [plan v1.1] [DONE] T6: Added local data layout conventions for raw, normalized, feature, event, embedding, index, model, and report layers
[2026-04-01 22:03:00] [plan v1.1] [START] T7: Build reproducible raw H&M dataset ingestion into the local data layout
[2026-04-01 22:03:00] [plan v1.1] [DONE] T7: Added Python project scaffolding, a raw-ingestion CLI, and unit coverage for zip and directory ingestion flows
[2026-04-01 22:12:00] [plan v1.1] [CORRECTION] T7: Moved Python code under backend/ and split ingestion logic into smaller focused modules to align with backend/frontend repo boundaries and Python module guidelines
[2026-04-01 22:28:00] [plan v1.1] [START] T8: Build product normalization and image-manifest generation from ingested raw data
[2026-04-01 22:28:00] [plan v1.1] [DONE] T8: Added product normalization, image manifest generation, and output metadata writing
[2026-04-01 22:28:00] [plan v1.1] [START] T9: Build customer normalization from ingested raw data
[2026-04-01 22:28:00] [plan v1.1] [DONE] T9: Added customer normalization and output metadata writing
[2026-04-01 22:28:00] [plan v1.1] [START] T10: Build transaction normalization with deterministic event identifiers
[2026-04-01 22:28:00] [plan v1.1] [DONE] T10: Added transaction normalization with normalized event timestamps and deterministic event IDs
[2026-04-01 22:28:00] [plan v1.1] [START] T11: Validate normalized dataset outputs
[2026-04-01 22:28:00] [plan v1.1] [DONE] T11: Added normalized dataset validation checks, quality report output, and unit coverage for the normalization pipeline
[2026-04-01 22:41:00] [plan v1.1] [START] T12: Define event schemas and topic boundaries for simulated online behavior
[2026-04-01 22:41:00] [plan v1.1] [DONE] T12: Added an event contract document for interaction and catalog topics, payload rules, and replay conventions
[2026-04-01 22:41:00] [plan v1.1] [START] T13: Implement synthetic interaction generation
[2026-04-01 22:41:00] [plan v1.1] [DONE] T13: Added deterministic interaction event generation from normalized transactions and products
[2026-04-01 22:41:00] [plan v1.1] [START] T14: Implement catalog change event generation
[2026-04-01 22:41:00] [plan v1.1] [DONE] T14: Added deterministic catalog update event generation from normalized products
[2026-04-01 22:41:00] [plan v1.1] [START] T15: Implement local event publishing and replay
[2026-04-01 22:41:00] [plan v1.1] [DONE] T15: Added local replay-batch publishing and manifest writing for interaction and catalog topics
[2026-04-01 22:41:00] [plan v1.1] [START] T16: Validate replayed event quality
[2026-04-01 22:41:00] [plan v1.1] [DONE] T16: Added replay validation checks and unit coverage for generated event batches
[2026-04-01 22:52:00] [plan v1.1] [START] T17: Define offline feature entities and views
[2026-04-01 22:52:00] [plan v1.1] [DONE] T17: Added an offline feature spec plus code-level entity and view registry definitions for future point-in-time feature work
[2026-04-01 23:04:00] [plan v1.1] [START] T18: Build point-in-time correct training joins
[2026-04-01 23:04:00] [plan v1.1] [DONE] T18: Added a leakage-safe offline training dataset builder, join manifest output, and unit coverage for historical feature retrieval
[2026-04-01 23:12:00] [plan v1.1] [START] T19: Define online feature requirements
[2026-04-01 23:12:00] [plan v1.1] [DONE] T19: Added online feature requirement definitions covering entities, freshness targets, and streaming-input mappings
[2026-04-01 23:21:00] [plan v1.1] [START] T20: Build streaming feature computation
[2026-04-01 23:21:00] [plan v1.1] [DONE] T20: Added local online feature computation from replayed events plus snapshot-store outputs and unit coverage
[2026-04-01 23:28:00] [plan v1.1] [START] T21: Expose online feature serving
[2026-04-01 23:28:00] [plan v1.1] [DONE] T21: Added a local online feature service and CLI retrieval path for session, customer, and article payloads
[2026-04-01 23:36:00] [plan v1.1] [START] T22: Validate feature parity and freshness
[2026-04-01 23:36:00] [plan v1.1] [DONE] T22: Added parity and freshness validation for the local online feature store with report output and unit coverage
[2026-04-01 23:47:00] [plan v1.1] [START] T23: Define multimodal representation strategy
[2026-04-01 23:47:00] [plan v1.1] [DONE] T23: Added a multimodal retrieval strategy document plus code-level modality and fusion strategy definitions
[2026-04-01 22:55:10] [extra request] [DONE] Outside plan: pinned backend Python to 3.13.0 in `.python-version` and rebuilt `backend/.venv` with the local Python 3.13 interpreter
[2026-04-01 23:01:58] [plan v1.1] [START] T24: Build embedding generation pipeline
[2026-04-01 23:04:33] [plan v1.1] [DONE] T24: Added deterministic text, image, and fused embedding generation with JSONL artifacts, manifests, CLI support, and unit coverage
[2026-04-01 23:05:21] [plan v1.1] [START] T25: Build vector indexing pipeline
[2026-04-01 23:07:16] [plan v1.1] [START] T26: Implement candidate retrieval logic
[2026-04-01 23:09:44] [plan v1.1] [DONE] T25: Added rebuildable text and fused vector index artifacts with manifests, CLI support, and unit coverage
[2026-04-01 23:09:44] [plan v1.1] [DONE] T26: Added local candidate retrieval over the vector index with query text, seed-item, and online-context support plus unit coverage
[2026-04-02 00:05:00] [plan v1.1] [START] T27: Build ranking dataset generation
[2026-04-02 00:05:00] [plan v1.1] [DONE] T27: Added a ranking dataset builder that combines observed positives with retrieved negatives, candidate-specific PIT features, manifests, CLI support, and unit coverage
[2026-04-02 00:18:00] [extra request] [DONE] Added backend Poetry dev dependencies, lint/test tool configuration, and a generated lockfile for reproducible local tooling
[2026-04-02 00:34:00] [plan v1.1] [START] T28: Implement ranking model training
[2026-04-02 00:34:00] [plan v1.1] [DONE] T28: Added a deterministic logistic ranking baseline with tracked training runs, serialized model artifacts, CLI support, and unit coverage
[2026-04-02 00:43:00] [plan v1.1] [START] T29: Register candidate models and metadata
[2026-04-02 00:43:00] [plan v1.1] [DONE] T29: Added a file-backed candidate model registry with lineage metadata, latest-candidate pointers, CLI support, and unit coverage
[2026-04-02 01:40:00] [plan v1.4] [START] T56: Introduce text embedder abstractions and a SentenceTransformer-backed implementation
[2026-04-02 01:40:00] [plan v1.4] [DONE] T56: Added pluggable text embedding interfaces, a SentenceTransformerTextEmbedder, and focused unit coverage while preserving optional dependency loading
[2026-04-02 02:00:00] [plan v1.4] [START] T57: Introduce image embedder abstractions and an OpenCLIP-backed implementation
[2026-04-02 02:00:00] [plan v1.4] [DONE] T57: Added pluggable image embedding interfaces, an OpenClipImageEmbedder, and focused unit coverage with optional dependency loading
[2026-04-02 02:12:00] [plan v1.4] [START] T58: Refactor embedding artifact generation to use pluggable embedder implementations
[2026-04-02 02:12:00] [plan v1.4] [DONE] T58: Refactored build_embedding_artifacts to use injected embedders, preserved deterministic fallback behavior, and added coverage for mixed embedding dimensions
[2026-04-02 02:28:00] [plan v1.4] [START] T59: Implement a Qdrant index manager that creates collections and upserts embedding artifacts
[2026-04-02 02:28:00] [plan v1.4] [DONE] T59: Expanded the Qdrant manager to own collection creation, stable article-key upserts, and persisted embedding artifact loading
[2026-04-02 02:34:00] [plan v1.4] [START] T60: Add a CLI command that loads embedding artifacts into Qdrant collections
[2026-04-02 02:34:00] [plan v1.4] [DONE] T60: Added build-qdrant-index CLI routing with regression coverage for the new Qdrant loading path
[2026-04-02 02:44:00] [plan v1.4] [START] T61: Implement a Qdrant-backed candidate retriever while preserving the existing retrieval contract
[2026-04-02 02:44:00] [plan v1.4] [DONE] T61: Replaced the local index search path with a Qdrant-backed retriever and added fake-client regression coverage for ranking, seed exclusion, and context propagation
[2026-04-02 02:52:00] [plan v1.4] [START] T62: Enrich retrieval request context with Feast and Redis online features
[2026-04-02 02:52:00] [plan v1.4] [DONE] T62: Added a Feast online feature service and updated retrieval context hydration to combine Feast and Redis request signals
[2026-04-02 03:08:00] [plan v1.4] [START] T63: Implement an MLflow run logger wrapper for params, metrics, tags, and artifacts
[2026-04-02 03:08:00] [plan v1.4] [DONE] T63: Expanded the MLflow run logger to support nested payload flattening for training params and metrics while preserving artifact logging
[2026-04-02 03:16:00] [plan v1.4] [START] T64: Refactor train_local_ranking_model to log training results through MLflowRunLogger
[2026-04-02 03:16:00] [plan v1.4] [DONE] T64: Updated ranking training to emit MLflow run metadata, params, metrics, and artifacts while preserving local manifests and offline fallback retrieval
[2026-04-02 03:24:00] [plan v1.4] [START] T65: Implement an MLflow model registrar for trained ranking models
[2026-04-02 03:24:00] [plan v1.4] [DONE] T65: Updated ranking registration to call the MLflow model registrar and persist MLflow model-version metadata alongside local registry lineage

---
## Plan v1.6
[2026-04-02 17:50:12] [plan v1.6] [START] T102: Publish a runtime ownership matrix for backend, simulator, pipelines, orchestration, frontend, infra, and ops
[2026-04-02 17:50:12] [plan v1.6] [START] T103: Move local shared-service definitions into an infra-owned local runtime layout
[2026-04-02 17:50:12] [plan v1.6] [START] T104: Create a dedicated orchestration workspace for Dagster user code, webserver, daemon, and workspace configuration
[2026-04-02 17:50:12] [plan v1.6] [START] T105: Define local development process boundaries for backend, frontend, orchestration, and infra
[2026-04-02 17:50:12] [plan v1.6] [START] T106: Refactor backend code so broker, orchestration, and service bootstrap concerns are configuration-driven integrations only
[2026-04-02 17:50:12] [plan v1.6] [DONE] T102: Added a runtime ownership matrix and M1 topology guidance to the system design, decisions log, and repo README
[2026-04-02 17:50:12] [plan v1.6] [DONE] T103: Created an infra-owned local runtime layout with canonical Compose and broker bootstrap assets under infra/local
[2026-04-02 17:50:12] [plan v1.6] [DONE] T104: Moved Dagster definitions into the top-level orchestration project and updated orchestration workspace documentation
[2026-04-02 17:50:12] [plan v1.6] [DONE] T105: Published explicit local run boundaries for backend, orchestration, infra, and the future frontend workflow
[2026-04-02 17:50:12] [plan v1.6] [DONE] T106: Removed backend-owned runtime bootstrap CLI and Dagster module ownership, and aligned backend broker defaults with external local infra access
[2026-04-02 18:45:48] [plan v1.6] [START] T107: Create a dedicated simulator package for synthetic events, replay manifests, and fake traffic generation
[2026-04-02 18:45:48] [plan v1.6] [START] T108: Create a dedicated pipelines package for normalization, Feast materialization, PIT joins, feature backfills, and ranking dataset assembly
[2026-04-02 18:45:48] [plan v1.6] [START] T109: Define stable storage and schema contracts between simulator outputs, pipeline outputs, and backend inputs
[2026-04-02 18:45:48] [plan v1.6] [START] T110: Preserve point-in-time correctness across the package split
[2026-04-02 18:45:48] [plan v1.6] [START] T111: Add integration tests that validate simulator-to-backend and pipelines-to-backend boundaries
[2026-04-02 18:45:48] [plan v1.6] [DONE] T107: Added top-level simulator-owned replay, event-generation, validation, and contract modules with backend compatibility wrappers
[2026-04-02 18:45:48] [plan v1.6] [DONE] T108: Added a top-level pipelines package for normalization, PIT dataset building, Feast batch flows, and ranking-dataset assembly with backend compatibility wrappers
[2026-04-02 18:45:48] [plan v1.6] [DONE] T109: Updated the data, dataset, and event contracts to define artifact ownership and stable simulator/pipelines-to-backend handoffs
[2026-04-02 18:45:48] [plan v1.6] [DONE] T110: Documented the package-split PIT invariants and preserved the existing leakage-safe builders behind the pipelines-owned boundary
[2026-04-02 18:45:48] [plan v1.6] [DONE] T111: Added boundary tests that exercise simulator replay into backend online features and pipelines outputs into backend parity validation
[2026-04-02 21:28:06] [plan v1.6] [START] T112: Audit the current API endpoints against realistic application test journeys
[2026-04-02 21:28:06] [plan v1.6] [START] T113: Define and implement the missing public API contracts for event tracking, readiness, and test-friendly diagnostics
[2026-04-02 21:28:06] [plan v1.6] [START] T114: Add deterministic API-level smoke, contract, and end-to-end tests around the current recommendation flow
[2026-04-02 21:28:06] [plan v1.6] [START] T115: Define the frontend-to-backend contract for recommendation requests, event emission, and session handling
[2026-04-02 21:28:06] [plan v1.6] [DONE] T112: Audited the public FastAPI surface and documented the minimum application-facing endpoints for liveness, readiness, diagnostics, recommendations, tracking, and metrics
[2026-04-02 21:28:06] [plan v1.6] [DONE] T113: Added `/readyz`, `/diagnostics`, and `/events` with explicit request and response contracts for local application testing
[2026-04-02 21:28:06] [plan v1.6] [DONE] T114: Added deterministic API smoke and contract coverage, including in-process smoke reporting for health, readiness, and diagnostics
[2026-04-02 21:28:06] [plan v1.6] [DONE] T115: Defined the frontend-to-backend contract for recommendation requests, tracking events, and session correlation
[2026-04-02 21:28:06] [plan v1.6] [START] T116: Scaffold a top-level frontend workspace that runs outside Docker Compose with Vite for local development
[2026-04-02 21:28:06] [plan v1.6] [START] T117: Define a frontend API client layer that uses the browser `fetch` API or a thin wrapper rather than Axios
[2026-04-02 21:28:06] [plan v1.6] [START] T118: Add a local end-to-end developer workflow that combines Vite, the backend API, and shared infra services
[2026-04-02 21:28:06] [plan v1.6] [DONE] T116: Added a top-level Vite frontend workspace with environment defaults and a lightweight demo application
[2026-04-02 21:28:06] [plan v1.6] [DONE] T117: Standardized frontend API calls on a thin browser `fetch` client instead of Axios
[2026-04-02 21:28:06] [plan v1.6] [DONE] T118: Added a local developer workflow script and updated the repo runbooks for frontend, backend, orchestration, and shared infra
[2026-04-02 21:28:06] [plan v1.6] [START] T119: Define the production-like embedding strategy, model choices, and reproducibility contract
[2026-04-02 21:28:06] [plan v1.6] [START] T120: Implement PyTorch-backed text and image embedding jobs with stable artifact manifests
[2026-04-02 21:28:06] [plan v1.6] [START] T121: Add experiment tracking and lineage for embedding runs, models, datasets, and indexes
[2026-04-02 21:28:06] [plan v1.6] [START] T122: Expand offline evaluation for retrieval quality, embedding quality, and slice behavior using real model outputs
[2026-04-02 21:28:06] [plan v1.6] [START] T123: Define online monitoring for embedding freshness, vector index health, retrieval drift, and model regressions
[2026-04-02 21:28:06] [plan v1.6] [DONE] T119: Published the PyTorch-based embedding strategy, runtime behavior, reproducibility contract, and lineage expectations for retrieval artifacts
[2026-04-02 21:28:06] [plan v1.6] [DONE] T120: Replaced the brittle embedding default with a torch-backed projection path that emits stable manifests and per-record lineage metadata
[2026-04-02 21:28:06] [plan v1.6] [DONE] T121: Extended MLflow lineage logging and embedding/index manifests so retrieval artifacts capture dataset, runtime, and downstream index provenance
[2026-04-02 21:28:06] [plan v1.6] [DONE] T122: Expanded offline retrieval evaluation to include slice metrics, index freshness signals, and promotion-readiness summaries
[2026-04-02 21:28:06] [plan v1.6] [DONE] T123: Added online guardrail metrics and observability hooks for fallback rate, null-result rate, rollback recommendation, and retrieval promotion readiness
[2026-04-02 21:28:06] [plan v1.6] [START] T124: Consolidate reproducibility requirements for ranking training, embedding generation, feature inputs, and evaluation runs
[2026-04-02 21:28:06] [plan v1.6] [START] T125: Add promotion gates that combine offline evaluation thresholds, smoke checks, and experiment readiness criteria
[2026-04-02 21:28:06] [plan v1.6] [START] T126: Define the online evaluation loop for exposure logging, user events, guardrails, and rollback decisions
[2026-04-02 21:28:06] [plan v1.6] [START] T127: Refactor orchestration workflows so Dagster schedules and jobs cover simulator runs, batch pipelines, model rebuilds, evaluation, and promotion checks
[2026-04-02 21:28:06] [plan v1.6] [DONE] T124: Consolidated reproducibility through shared artifact schemas, manifest lineage, MLflow parameter logging, and repo-level contract documentation
[2026-04-02 21:28:06] [plan v1.6] [DONE] T125: Added an explicit promotion-gate report that combines retrieval readiness, ranking metrics, API smoke checks, and online guardrails
[2026-04-02 21:28:06] [plan v1.6] [DONE] T126: Added online evaluation reporting over exposure and tracking logs with CTR, fallback, null-result, and rollback guardrails
[2026-04-02 21:28:06] [plan v1.6] [DONE] T127: Expanded Dagster assets, jobs, and schedules to cover simulator replay, feature refresh, embedding rebuilds, offline evaluation, API smoke checks, and promotion gating
[2026-04-02 21:28:06] [plan v1.6] [START] T128: Create an infra layout for Helm charts covering backend API, orchestration, simulator jobs, pipelines jobs, and frontend delivery
[2026-04-02 21:28:06] [plan v1.6] [START] T129: Define environment-specific values and ownership for shared dependencies such as Redpanda, Redis, Qdrant, MLflow, and observability
[2026-04-02 21:28:06] [plan v1.6] [START] T130: Publish the end-to-end topology showing how frontend, backend, simulator, pipelines, orchestration, and shared services interact
[2026-04-02 21:28:06] [plan v1.6] [DONE] T128: Added `infra/helm/` charts for backend API, frontend, orchestration, simulator jobs, and pipelines jobs
[2026-04-02 21:28:06] [plan v1.6] [DONE] T129: Added environment overlays and infra documentation that define shared dependency ownership across local, demo, and production-like targets
[2026-04-02 21:28:06] [plan v1.6] [DONE] T130: Updated the README, system design, contracts, and infra docs with the end-to-end runtime topology and local versus production-like deployment model
