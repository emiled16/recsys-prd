# Checklist for Plan v1.6

## Milestone M1: Define Runtime Ownership and Local Development Topology
- [x] T102: Publish a runtime ownership matrix for backend, simulator, pipelines, orchestration, frontend, infra, and ops
- [x] T103: Move local shared-service definitions into an infra-owned local runtime layout
- [x] T104: Create a dedicated orchestration workspace for Dagster user code, webserver, daemon, and workspace configuration
- [x] T105: Define local development process boundaries for backend, frontend, orchestration, and infra
- [x] T106: Refactor backend code so broker, orchestration, and service bootstrap concerns are configuration-driven integrations only

## Milestone M2: Separate Synthetic Data and Offline Pipelines From the Backend
- [x] T107: Create a dedicated simulator package for synthetic events, replay manifests, and fake traffic generation
- [x] T108: Create a dedicated pipelines package for normalization, Feast materialization, PIT joins, feature backfills, and ranking dataset assembly
- [x] T109: Define stable storage and schema contracts between simulator outputs, pipeline outputs, and backend inputs
- [x] T110: Preserve point-in-time correctness across the package split
- [x] T111: Add integration tests that validate simulator-to-backend and pipelines-to-backend boundaries

## Milestone M3: Make the API Surface Sufficient for Application Testing
- [x] T112: Audit the current API endpoints against realistic application test journeys
- [x] T113: Define and implement the missing public API contracts for event tracking, readiness, and test-friendly diagnostics
- [x] T114: Add deterministic API-level smoke, contract, and end-to-end tests around the current recommendation flow
- [x] T115: Define the frontend-to-backend contract for recommendation requests, event emission, and session handling

## Milestone M4: Standardize the Frontend Development Surface
- [x] T116: Scaffold a top-level frontend workspace that runs outside Docker Compose with Vite for local development
- [x] T117: Define a frontend API client layer that uses the browser `fetch` API or a thin wrapper rather than Axios
- [x] T118: Add a local end-to-end developer workflow that combines Vite, the backend API, and shared infra services

## Milestone M5: Replace Brittle Embeddings With a Real PyTorch-Based Model Path
- [x] T119: Define the production-like embedding strategy, model choices, and reproducibility contract
- [x] T120: Implement PyTorch-backed text and image embedding jobs with stable artifact manifests
- [x] T121: Add experiment tracking and lineage for embedding runs, models, datasets, and indexes
- [x] T122: Expand offline evaluation for retrieval quality, embedding quality, and slice behavior using real model outputs
- [x] T123: Define online monitoring for embedding freshness, vector index health, retrieval drift, and model regressions

## Milestone M6: Harden the Broader MLOps Lifecycle for Ranking and Recommendation Serving
- [x] T124: Consolidate reproducibility requirements for ranking training, embedding generation, feature inputs, and evaluation runs
- [x] T125: Add promotion gates that combine offline evaluation thresholds, smoke checks, and experiment readiness criteria
- [x] T126: Define the online evaluation loop for exposure logging, user events, guardrails, and rollback decisions
- [x] T127: Refactor orchestration workflows so Dagster schedules and jobs cover simulator runs, batch pipelines, model rebuilds, evaluation, and promotion checks

## Milestone M7: Package the Deployment Surfaces for Local and Production-Like Environments
- [x] T128: Create an infra layout for Helm charts covering backend API, orchestration, simulator jobs, pipelines jobs, and frontend delivery
- [x] T129: Define environment-specific values and ownership for shared dependencies such as Redpanda, Redis, Qdrant, MLflow, and observability
- [x] T130: Publish the end-to-end topology showing how frontend, backend, simulator, pipelines, orchestration, and shared services interact
