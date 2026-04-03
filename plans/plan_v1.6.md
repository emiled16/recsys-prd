# Plan v1.6

## Context
`v1.5` correctly shifted the roadmap toward cleaner boundaries, but it left several decisions too implicit for the next implementation phase. The current chat history clarified that the repository needs more than a generic backend-versus-simulator split. It also needs:
- an explicit runtime surface for Dagster that is not owned by the backend package,
- infra-owned local services such as Redpanda that are not treated as backend concerns,
- a testing-ready API surface that supports realistic application validation,
- a frontend workflow that runs outside Docker Compose with Vite during local development,
- a real PyTorch-based embedding path that mirrors production practices instead of brittle stand-ins,
- and a tighter MLOps plan for reproducibility, experiment tracking, offline and online evaluation, and monitoring.

The goal of this version is to turn those requirements into an executable next-step plan. This plan assumes the existing local stack remains the baseline, but it reorganizes ownership and adds the missing work needed to make the application easy to test and closer to a real production shape.

## Milestones

### M1: Define Runtime Ownership and Local Development Topology

#### Task T102: Publish a runtime ownership matrix for backend, simulator, pipelines, orchestration, frontend, infra, and ops
- Description: Create a decision record that defines which top-level area owns application serving, synthetic data generation, batch pipelines, Dagster orchestration, frontend development, deployment assets, and local observability. The expected outcome is a repository map that explicitly prevents Redpanda, Dagster runtime management, and other shared services from being treated as backend-internal concerns.
- Files involved: `docs/key-decisions.md`, `docs/sys-design.md`, `README.md`
- Dependencies: None

#### Task T103: Move local shared-service definitions into an infra-owned local runtime layout
- Description: Introduce an `infra/local/` area that owns Docker Compose definitions, environment files, and local runtime configuration for Redpanda, Redis, Qdrant, MLflow, Prometheus, and Grafana. The expected outcome is that the backend consumes these services through configuration only, while their lifecycle and manifests live outside backend code.
- Files involved: `infra/local/`, `docker-compose.yml`, `backend/recsys_prd/config.py`, `docs/sys-design.md`
- Dependencies: T102

#### Task T104: Create a dedicated orchestration workspace for Dagster user code, webserver, daemon, and workspace configuration
- Description: Add a top-level `orchestration/` surface that owns Dagster definitions, code locations, local launch commands, and production packaging. The expected outcome is that Dagster no longer lives as a backend concern; instead, the backend exposes services and contracts, while Dagster orchestrates simulator and pipeline workloads from its own runtime surface.
- Files involved: `orchestration/`, existing Dagster definitions, `docs/sys-design.md`, `docs/key-decisions.md`
- Dependencies: T102

#### Task T105: Define local development process boundaries for backend, frontend, orchestration, and infra
- Description: Publish a local development runbook stating that the backend API runs directly with `uvicorn`, the frontend runs outside Compose with Vite, Dagster runs from the orchestration workspace, and shared infra services run through Compose. The expected outcome is a fast developer workflow with clear process ownership and no ambiguity about what belongs inside or outside Compose.
- Files involved: `README.md`, `docs/sys-design.md`, `infra/local/`, future `frontend/`, future `orchestration/`
- Dependencies: T103, T104

#### Task T106: Refactor backend code so broker, orchestration, and service bootstrap concerns are configuration-driven integrations only
- Description: Update the backend architecture so it contains API, serving, online feature access, retrieval, and ranking orchestration, but does not own Redpanda lifecycle, Dagster server startup, or other shared-runtime concerns. The expected outcome is a backend that integrates with external runtimes by contract rather than owning their deployment topology.
- Files involved: `backend/recsys_prd/services/`, `backend/recsys_prd/config.py`, `backend/recsys_prd/cli.py`, integration docs
- Dependencies: T103, T104

### M2: Separate Synthetic Data and Offline Pipelines From the Backend

#### Task T107: Create a dedicated simulator package for synthetic events, replay manifests, and fake traffic generation
- Description: Add a top-level `simulator/` package that owns synthetic interaction generation, catalog event generation, replay manifests, local demo seeding, and fake producer utilities. The expected outcome is a clear separation where current "real-time" data generation is explicitly simulator-owned rather than mixed into backend modules.
- Files involved: `simulator/`, current event-generation modules, `docs/event-contract.md`
- Dependencies: T102, T105

#### Task T108: Create a dedicated pipelines package for normalization, Feast materialization, PIT joins, feature backfills, and ranking dataset assembly
- Description: Add a top-level `pipelines/` package that owns offline and batch-oriented computation. The expected outcome is that normalization, historical feature building, training-dataset construction, and other offline jobs move out of the online backend package while preserving their contracts and outputs.
- Files involved: `pipelines/`, current normalization and offline-feature modules, `docs/data-layout.md`
- Dependencies: T102, T105

#### Task T109: Define stable storage and schema contracts between simulator outputs, pipeline outputs, and backend inputs
- Description: Formalize which artifacts each surface writes and which contracts downstream surfaces consume, including replay batches, normalized datasets, feature datasets, embedding artifacts, model artifacts, and online store update messages. The expected outcome is a strict handoff model that prevents cross-surface coupling through internal imports.
- Files involved: `docs/data-layout.md`, `docs/dataset-contract.md`, `docs/event-contract.md`, shared schema modules
- Dependencies: T107, T108

#### Task T110: Preserve point-in-time correctness across the package split
- Description: Define and validate the invariants that must remain true while PIT joins, feature materialization, and replay generation move into separate packages, including event-time ordering, label-time cutoffs, timestamp provenance, and replay determinism. The expected outcome is a migration path that keeps offline training correctness intact while the repository is restructured.
- Files involved: `docs/offline-feature-spec.md`, `docs/online-feature-requirements.md`, PIT builders, parity validation
- Dependencies: T108, T109

#### Task T111: Add integration tests that validate simulator-to-backend and pipelines-to-backend boundaries
- Description: Add coverage that exercises real handoffs across top-level surfaces rather than only internal modules, for example synthetic events flowing through Redpanda into online features and pipeline outputs flowing into backend retrieval and ranking flows. The expected outcome is architecture-level regression coverage for the new separation model.
- Files involved: `backend/tests/`, future `simulator/`, future `pipelines/`, shared test fixtures
- Dependencies: T107, T108, T109, T110

### M3: Make the API Surface Sufficient for Application Testing

#### Task T112: Audit the current API endpoints against realistic application test journeys
- Description: Review the existing FastAPI surface and define the minimum set of endpoints needed to test recommendation retrieval, health, readiness, event ingestion, and observability without reaching into internal modules. The expected outcome is a concrete API contract for local application testing rather than a backend that is only smoke-testable.
- Files involved: `backend/recsys_prd/api/app.py`, `backend/recsys_prd/api/models.py`, `docs/sys-design.md`, `README.md`
- Dependencies: T102

#### Task T113: Define and implement the missing public API contracts for event tracking, readiness, and test-friendly diagnostics
- Description: Extend the API surface so application testing can cover the key interactions around recommendation requests, event submission, service readiness, and safe diagnostics needed for local verification. The expected outcome is a coherent public API that supports frontend development and end-to-end testing without exposing arbitrary internal state.
- Files involved: `backend/recsys_prd/api/`, serving and event-ingest modules, API contract docs
- Dependencies: T112, T109

#### Task T114: Add deterministic API-level smoke, contract, and end-to-end tests around the current recommendation flow
- Description: Build a test harness that validates the live API behavior using deterministic fixtures, fake or replayed events, and explicit assertions on responses, fallback behavior, and metrics exposure. The expected outcome is that the application can be tested through endpoints rather than only through unit-level service calls.
- Files involved: `backend/tests/`, API fixtures, local test scripts, `README.md`
- Dependencies: T111, T113

#### Task T115: Define the frontend-to-backend contract for recommendation requests, event emission, and session handling
- Description: Specify how the frontend should request recommendations, emit interaction events, and manage session and customer identity while remaining decoupled from backend implementation details. The expected outcome is an API contract that lets the future frontend test realistic flows without inventing its own protocol.
- Files involved: `docs/sys-design.md`, `docs/event-contract.md`, `backend/recsys_prd/api/models.py`
- Dependencies: T112, T113

### M4: Standardize the Frontend Development Surface

#### Task T116: Scaffold a top-level frontend workspace that runs outside Docker Compose with Vite for local development
- Description: Add a `frontend/` workspace with a Vite-based local dev setup, clear package boundaries, environment configuration, and no assumption that the frontend should run inside Compose during local iteration. The expected outcome is a fast feedback loop for UI work while leaving room for a separate production container later.
- Files involved: `frontend/`, `README.md`, local env docs
- Dependencies: T105, T115

#### Task T117: Define a frontend API client layer that uses the browser `fetch` API or a thin wrapper rather than Axios
- Description: Standardize frontend HTTP interaction around the native `fetch` API or a minimal safe abstraction, explicitly avoiding Axios. The expected outcome is a security-conscious frontend networking layer that matches the local Vite workflow and future production packaging.
- Files involved: `frontend/`, frontend docs, API integration examples
- Dependencies: T116

#### Task T118: Add a local end-to-end developer workflow that combines Vite, the backend API, and shared infra services
- Description: Publish and automate a workflow that starts frontend, backend, and required infra processes in a way that supports quick manual testing and future automated end-to-end testing. The expected outcome is a repeatable local application loop rather than a set of disconnected service commands.
- Files involved: `README.md`, local dev scripts, `infra/local/`, `frontend/`, `backend/`
- Dependencies: T105, T114, T116, T117

### M5: Replace Brittle Embeddings With a Real PyTorch-Based Model Path

#### Task T119: Define the production-like embedding strategy, model choices, and reproducibility contract
- Description: Select the real PyTorch-backed embedding models to use for the example stack, define device handling, model-version pinning, seed control, batching behavior, dataset snapshot requirements, and artifact metadata. The expected outcome is a documented embedding strategy that behaves like a real production pipeline even if the chosen models are small.
- Files involved: `docs/multimodal-representation-strategy.md`, `docs/key-decisions.md`, model config modules
- Dependencies: T102, T109

#### Task T120: Implement PyTorch-backed text and image embedding jobs with stable artifact manifests
- Description: Replace the current brittle embedding stand-ins with real model-backed jobs that produce text and image embeddings, persist them with explicit metadata, and support reproducible rebuilds from known inputs. The expected outcome is a true deep-learning embedding stage that mirrors real-world inference and artifact management.
- Files involved: embedding pipeline modules, future `pipelines/`, model config, artifact schemas
- Dependencies: T119

#### Task T121: Add experiment tracking and lineage for embedding runs, models, datasets, and indexes
- Description: Extend the existing MLflow and artifact-tracking approach so embedding runs record model versions, dataset snapshots, hardware and config metadata, output manifests, and downstream index lineage. The expected outcome is end-to-end reproducibility for the retrieval side of the stack rather than only for ranking runs.
- Files involved: MLflow integration code, embedding manifests, index manifests, `docs/sys-design.md`
- Dependencies: T120

#### Task T122: Expand offline evaluation for retrieval quality, embedding quality, and slice behavior using real model outputs
- Description: Add evaluation coverage that measures retrieval quality, modality contribution, slice-based performance, and index freshness using the real embedding artifacts rather than only baseline stand-ins. The expected outcome is a realistic offline evaluation loop for the retrieval stack.
- Files involved: retrieval evaluation modules, reports, evaluation docs
- Dependencies: T120, T121

#### Task T123: Define online monitoring for embedding freshness, vector index health, retrieval drift, and model regressions
- Description: Extend observability so the system can detect stale embeddings, unhealthy index refreshes, retrieval score drift, and regressions caused by model or data changes. The expected outcome is production-shaped monitoring for the embedding and retrieval path in addition to existing API metrics.
- Files involved: observability modules, Prometheus and Grafana assets, monitoring docs
- Dependencies: T121, T122

### M6: Harden the Broader MLOps Lifecycle for Ranking and Recommendation Serving

#### Task T124: Consolidate reproducibility requirements for ranking training, embedding generation, feature inputs, and evaluation runs
- Description: Define a common reproducibility contract covering dataset versions, feature-store snapshots, model configs, seeds, environment metadata, and artifact lineage across both retrieval and ranking. The expected outcome is one consistent MLOps foundation instead of separate ad hoc tracking per subsystem.
- Files involved: `docs/key-decisions.md`, MLflow integration code, artifact schemas, training docs
- Dependencies: T121

#### Task T125: Add promotion gates that combine offline evaluation thresholds, smoke checks, and experiment readiness criteria
- Description: Define and implement promotion policies so candidate retrieval and ranking models cannot advance without satisfying offline metrics, artifact completeness, API smoke checks, and online experiment prerequisites. The expected outcome is a more realistic deployment gate than simply registering the latest local run.
- Files involved: model registry code, evaluation modules, promotion docs, orchestration entrypoints
- Dependencies: T122, T124

#### Task T126: Define the online evaluation loop for exposure logging, user events, guardrails, and rollback decisions
- Description: Extend the current experimentation path so it has an explicit contract for exposure events, user feedback events, guardrail metrics, winner criteria, and rollback triggers. The expected outcome is a production-oriented online evaluation model that connects the API, frontend event flow, and experiment analysis.
- Files involved: serving experimentation modules, `docs/event-contract.md`, API contracts, monitoring docs
- Dependencies: T113, T115, T125

#### Task T127: Refactor orchestration workflows so Dagster schedules and jobs cover simulator runs, batch pipelines, model rebuilds, evaluation, and promotion checks
- Description: Expand the orchestration surface so it manages the simulator, batch pipelines, embedding jobs, ranking jobs, evaluation runs, and promotion checks from the dedicated orchestration workspace. The expected outcome is a coherent MLOps control plane that is separate from backend serving and aligned with the new package boundaries.
- Files involved: `orchestration/`, Dagster definitions, simulator and pipelines entrypoints, promotion docs
- Dependencies: T104, T107, T108, T125, T126

### M7: Package the Deployment Surfaces for Local and Production-Like Environments

#### Task T128: Create an infra layout for Helm charts covering backend API, orchestration, simulator jobs, pipelines jobs, and frontend delivery
- Description: Add a top-level `infra/helm/` structure that defines how each top-level runtime surface is packaged and configured, including separate charts or subcharts where appropriate. The expected outcome is a deployment layout that matches the repository boundaries instead of collapsing everything into a backend-centric model.
- Files involved: `infra/helm/`, `docs/sys-design.md`, `docs/key-decisions.md`
- Dependencies: T103, T104, T107, T108, T116

#### Task T129: Define environment-specific values and ownership for shared dependencies such as Redpanda, Redis, Qdrant, MLflow, and observability
- Description: Document how shared dependencies are provisioned and referenced across local, demo, and production-like environments, and which of them remain external versus app-owned at each stage. The expected outcome is a clear deployment model for services that support the platform but are not owned by the backend runtime.
- Files involved: `infra/`, `docs/sys-design.md`, environment configuration docs
- Dependencies: T103, T128

#### Task T130: Publish the end-to-end topology showing how frontend, backend, simulator, pipelines, orchestration, and shared services interact
- Description: Update the system design with an implementation-ready topology that includes local development mode, production-style deployment mode, network boundaries, event flows, artifact flows, and ownership lines across all top-level surfaces. The expected outcome is a final architecture map that another engineer can implement against without guessing where any runtime should live.
- Files involved: `docs/sys-design.md`, `docs/data-layout.md`, `README.md`, `infra/`
- Dependencies: T118, T127, T129

## Revisions
- v1.6: Replaced the broad structural plan in `v1.5` with a more concrete next-step plan driven by the missing concerns raised in the current chat. This version makes Dagster runtime ownership explicit through a separate `orchestration/` surface, moves shared services such as Redpanda into infra-owned local runtime definitions, expands the API roadmap so the application is testable through endpoints, standardizes the frontend workflow around Vite and `fetch`, and upgrades the model roadmap to require a real PyTorch-based embedding path plus stronger MLOps, evaluation, and monitoring.
