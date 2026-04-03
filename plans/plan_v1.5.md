# Plan v1.5

## Context
`v1.4` delivered a runnable local stack for ingestion, replay, features, retrieval, ranking, serving, observability, and orchestration. The next phase is no longer about proving the baseline can run. It is about hardening repository boundaries so the project can evolve from a local systems-design exercise into a maintainable multi-surface platform.

The current chat history surfaced five architectural constraints that should now drive the next version:
- Keep a clear separation between the online backend and fake or synthetic data generation.
- Separate offline data-engineering and batch pipelines from serving-oriented backend code.
- Make the origin of "real-time" data explicit, with synthetic replay treated as a first-class simulator rather than implicit backend behavior.
- Reorganize the CLI around coherent domains, with `typer` preferred over a growing `argparse` surface.
- Prepare the repository for future frontend and deployment work with top-level structure for `frontend/`, `infra/`, and Helm-based packaging.

This version therefore focuses on structural refactoring, contract clarity, and developer ergonomics. It does not assume a new product surface is immediately implemented, but it makes room for one without forcing future work through the current mixed boundaries.

## Milestones

### M1: Freeze the Target Architecture and Boundary Contracts

#### Task T79: Publish a repository-boundary decision record for backend, simulator, pipelines, frontend, and infra
- Description: Create an architecture decision record that defines the target top-level layout, ownership boundaries, and allowed dependencies between `backend/`, a future `simulator/`, a future `pipelines/`, `frontend/`, and `infra/`. The expected outcome is one canonical document that explains which code belongs in each area and which cross-package imports are disallowed.
- Files involved: `docs/key-decisions.md`, `docs/sys-design.md`, `plans/`, `checklists/`
- Dependencies: None

#### Task T80: Define explicit producer-consumer contracts for synthetic events, real client events, and backend ingestion
- Description: Extend the event contract so the repository distinguishes between synthetic event producers, future frontend or service producers, and backend consumers. The expected outcome is a contract that makes simulator output and real event ingestion interchangeable at the schema and topic level.
- Files involved: `docs/event-contract.md`, `backend/recsys_prd/events/contracts.py`, `backend/recsys_prd/schemas/`
- Dependencies: T79

#### Task T81: Document runtime modes for local demo, synthetic replay, and production-oriented integrations
- Description: Define named runtime modes such as `demo`, `synthetic_replay`, and `integration`, including which services, datasets, and producers are active in each mode. The expected outcome is a documented matrix that clarifies when the system is using fake data, when it expects real infrastructure, and how those modes are configured.
- Files involved: `docs/sys-design.md`, `README.md`, `backend/recsys_prd/config.py`
- Dependencies: T79, T80

#### Task T82: Define a migration policy that preserves point-in-time correctness during package extraction
- Description: Write down the invariants that must remain true while moving PIT builders and feature sources into separate packages, including event-time semantics, label-time joins, source timestamps, and replay reproducibility. The expected outcome is a migration guardrail document that prevents structural refactors from breaking offline correctness.
- Files involved: `docs/offline-feature-spec.md`, `docs/online-feature-requirements.md`, `docs/key-decisions.md`, `backend/recsys_prd/features/`
- Dependencies: T79, T80

### M2: Extract Synthetic Data and Replay Into a Dedicated Simulator Surface

#### Task T83: Create a top-level simulator package for synthetic catalog and interaction generation
- Description: Add a dedicated package, for example `simulator/recsys_sim/`, and move synthetic interaction generation, catalog event generation, replay manifests, and related helpers out of the backend-owned package. The expected outcome is that fake data generation becomes a separate deployable and import boundary rather than hidden backend behavior.
- Files involved: `simulator/`, `backend/recsys_prd/events/`, `backend/pyproject.toml`
- Dependencies: T80, T81, T82

#### Task T84: Expose simulator-owned commands for seeding, replay generation, and broker publishing
- Description: Replace backend-owned synthetic-data commands with simulator-owned commands that can generate deterministic replay batches, inspect manifests, and publish events to Redpanda. The expected outcome is a CLI surface where simulation operations are clearly separated from serving and training commands.
- Files involved: `simulator/`, `backend/recsys_prd/cli.py`, `backend/scripts/`
- Dependencies: T83

#### Task T85: Refactor backend consumers to depend only on shared schemas and event topics, not simulator internals
- Description: Update the backend event ingestion and feature-consumer path so it reads replay files or Kafka topics through shared contracts only, without importing simulator implementations. The expected outcome is a one-way dependency where simulator produces events and backend consumes them without package entanglement.
- Files involved: `backend/recsys_prd/features/consumer.py`, `backend/recsys_prd/services/redpanda.py`, `backend/recsys_prd/events/`, `backend/recsys_prd/schemas/`
- Dependencies: T83, T84

#### Task T86: Add integration coverage for the simulator-to-backend handoff
- Description: Add tests that generate synthetic events through the simulator surface and verify that backend consumers, online-feature updates, and validation flows work without direct simulator imports. The expected outcome is regression coverage for the architectural boundary rather than only internal module behavior.
- Files involved: `backend/tests/`, `simulator/`, shared test fixtures
- Dependencies: T84, T85

#### Task T87: Publish operating docs that explain how synthetic traffic is produced today and how real producers will replace it later
- Description: Update the README and architecture docs so contributors can quickly see that current "real-time" traffic is synthetic, how the simulator is run, and what future frontend or service producers must emit to replace it. The expected outcome is zero ambiguity about the role of fake data in the current stack.
- Files involved: `README.md`, `docs/sys-design.md`, `docs/event-contract.md`
- Dependencies: T84, T85

### M3: Split Offline Data Engineering From Online Serving

#### Task T88: Create a top-level pipelines package for normalization, PIT joins, feature backfills, and training-data assembly
- Description: Add a dedicated package, for example `pipelines/recsys_pipelines/`, for batch and historical processing code currently mixed into the backend package. The expected outcome is a clear split between code that runs as offline jobs and code that serves online requests.
- Files involved: `pipelines/`, `backend/recsys_prd/normalization/`, `backend/recsys_prd/features/`, `backend/recsys_prd/ranking/`, `backend/pyproject.toml`
- Dependencies: T79, T82

#### Task T89: Move Feast materialization, PIT dataset building, and ranking-dataset assembly behind pipelines-owned entrypoints
- Description: Relocate batch-oriented entrypoints such as Feast apply/materialization, point-in-time dataset generation, and ranking-dataset construction into the pipelines package while preserving their contracts. The expected outcome is that backend retains online feature reads and recommendation orchestration, while pipelines owns historical computation.
- Files involved: `pipelines/`, `backend/recsys_prd/features/feast_store.py`, `backend/recsys_prd/features/training_dataset.py`, `backend/recsys_prd/ranking/dataset.py`
- Dependencies: T88

#### Task T90: Define the storage and artifact contract between pipelines outputs and backend inputs
- Description: Formalize which datasets and artifacts pipelines writes and which of those the backend is allowed to consume, including normalized tables, embedding artifacts, model registrations, and feature-store metadata. The expected outcome is a stable handoff contract that prevents backend code from reaching into arbitrary pipeline internals.
- Files involved: `docs/data-layout.md`, `docs/dataset-contract.md`, `backend/recsys_prd/config.py`, `pipelines/`
- Dependencies: T88, T89

#### Task T91: Revalidate point-in-time correctness and freshness checks after the package split
- Description: Re-run and, if needed, refactor PIT and parity validation so the extraction into pipelines does not change label-time semantics, historical joins, or online/offline comparison logic. The expected outcome is proof that the new package boundaries preserve the correctness guarantees already established in the baseline.
- Files involved: `backend/recsys_prd/features/parity_validation.py`, `pipelines/`, `backend/tests/`
- Dependencies: T89, T90

#### Task T92: Refactor Dagster definitions to orchestrate simulator and pipelines assets without importing backend-only serving code
- Description: Update the Dagster layer so assets and jobs target simulator and pipelines entrypoints where appropriate, while backend remains focused on APIs and online runtime services. The expected outcome is orchestration that mirrors the intended system boundaries instead of the current monorepo convenience layout.
- Files involved: `backend/recsys_prd/orchestration/dagster_defs.py`, `simulator/`, `pipelines/`
- Dependencies: T84, T89, T90

### M4: Replace the Current CLI and Test Layout With Scalable Developer Surfaces

#### Task T93: Introduce a `typer`-based command tree with sub-apps per coherent domain
- Description: Replace the current growing `argparse` surface with a `typer` command tree that has explicit sub-apps for backend serving, simulator operations, pipelines jobs, and environment probes. The expected outcome is a more maintainable CLI with clearer help output, modular command ownership, and room for future frontend and infra utilities.
- Files involved: `backend/recsys_prd/cli.py`, `backend/scripts/`, `simulator/`, `pipelines/`, `backend/pyproject.toml`
- Dependencies: T84, T89

#### Task T94: Preserve command compatibility with thin wrappers during the CLI migration
- Description: Add compatibility wrappers so existing script entrypoints and developer workflows continue to function while the new `typer` command tree becomes the primary interface. The expected outcome is a low-risk migration that avoids breaking current commands abruptly.
- Files involved: `backend/scripts/`, CLI wrapper modules, `README.md`
- Dependencies: T93

#### Task T95: Convert the test suite from `unittest`-style authoring to `pytest` fixtures, parametrization, and plain assertions
- Description: Rewrite the current tests so they keep `pytest` as the runner but use pytest-native fixtures and assertions instead of `unittest.TestCase` classes. The expected outcome is simpler setup, clearer assertions, and easier boundary testing across backend, simulator, and pipelines packages.
- Files involved: `backend/tests/`, shared test fixtures, `backend/pyproject.toml`
- Dependencies: T86, T91

#### Task T96: Add test markers and fixture layers that reflect unit, contract, integration, and service-backed coverage
- Description: Introduce test markers and shared fixtures for isolated unit tests, contract tests, simulator-to-backend integration tests, and external-service-backed tests. The expected outcome is a test layout that matches the new architecture and makes it obvious which suite validates which boundary.
- Files involved: `backend/tests/`, pytest configuration, shared fixtures
- Dependencies: T95

### M5: Prepare the Repository for Frontend and Deployment Work

#### Task T97: Define the frontend integration contract for recommendation requests and event emission
- Description: Specify how a future frontend will request recommendations, emit user events, and identify sessions and customers without tightly coupling UI code to backend internals. The expected outcome is an API-level contract that allows frontend work to begin later without reopening backend boundary debates.
- Files involved: `docs/sys-design.md`, `docs/event-contract.md`, `backend/recsys_prd/api/models.py`, `backend/recsys_prd/api/app.py`
- Dependencies: T80, T85

#### Task T98: Scaffold a top-level frontend workspace with explicit non-goals and no production UI assumptions
- Description: Add a `frontend/` workspace with initial documentation, package boundaries, and API integration placeholders, while explicitly deferring visual implementation until the product surface is chosen. The expected outcome is a clean place for future UI work without forcing design or product choices prematurely.
- Files involved: `frontend/`, `README.md`, `docs/sys-design.md`
- Dependencies: T97

#### Task T99: Create an `infra/` layout for Helm charts, cluster manifests, and future Terraform or GitOps assets
- Description: Add a top-level `infra/` structure that separates local operational files from deployment packaging, including directories for Helm charts, environment overlays, and infrastructure definitions. The expected outcome is a repository shape where `ops/` remains local-observability focused and `infra/` becomes the home for deployable infrastructure.
- Files involved: `infra/`, `ops/`, `docker-compose.yml`, deployment docs
- Dependencies: T79

#### Task T100: Define Helm chart boundaries for backend API, simulator jobs, pipelines jobs, and shared services
- Description: Document which components deserve their own charts, which shared services remain external dependencies, and how values should differ between local, demo, and cluster environments. The expected outcome is a Helm packaging strategy that follows the new backend/simulator/pipelines split rather than the current monolithic layout.
- Files involved: `infra/helm/`, `docs/sys-design.md`, `docs/key-decisions.md`
- Dependencies: T92, T99

#### Task T101: Publish the end-to-end deployment topology that connects frontend, backend, simulator, pipelines, feature services, and observability
- Description: Update the system design with a final topology view showing where frontend, backend API, simulator jobs, pipelines, Feast, Redis, Qdrant, MLflow, Dagster, Prometheus, and Grafana live and how traffic and artifacts move between them. The expected outcome is an implementation-ready deployment map that future infra and frontend work can follow.
- Files involved: `docs/sys-design.md`, `docs/data-layout.md`, `infra/`
- Dependencies: T98, T100

## Revisions
- v1.5: Replaced the post-baseline focus on "more capabilities in place" with a structural hardening plan driven by the current chat history. This version adds an explicit separation strategy for backend, synthetic-data generation, offline pipelines, future frontend work, and Helm-oriented infrastructure so the repository can evolve without compounding mixed boundaries.
