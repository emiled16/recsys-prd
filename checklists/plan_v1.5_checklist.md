# Checklist for Plan v1.5

## Milestone M1: Freeze the Target Architecture and Boundary Contracts
- [ ] T79: Publish a repository-boundary decision record for backend, simulator, pipelines, frontend, and infra
- [ ] T80: Define explicit producer-consumer contracts for synthetic events, real client events, and backend ingestion
- [ ] T81: Document runtime modes for local demo, synthetic replay, and production-oriented integrations
- [ ] T82: Define a migration policy that preserves point-in-time correctness during package extraction

## Milestone M2: Extract Synthetic Data and Replay Into a Dedicated Simulator Surface
- [ ] T83: Create a top-level simulator package for synthetic catalog and interaction generation
- [ ] T84: Expose simulator-owned commands for seeding, replay generation, and broker publishing
- [ ] T85: Refactor backend consumers to depend only on shared schemas and event topics, not simulator internals
- [ ] T86: Add integration coverage for the simulator-to-backend handoff
- [ ] T87: Publish operating docs that explain how synthetic traffic is produced today and how real producers will replace it later

## Milestone M3: Split Offline Data Engineering From Online Serving
- [ ] T88: Create a top-level pipelines package for normalization, PIT joins, feature backfills, and training-data assembly
- [ ] T89: Move Feast materialization, PIT dataset building, and ranking-dataset assembly behind pipelines-owned entrypoints
- [ ] T90: Define the storage and artifact contract between pipelines outputs and backend inputs
- [ ] T91: Revalidate point-in-time correctness and freshness checks after the package split
- [ ] T92: Refactor Dagster definitions to orchestrate simulator and pipelines assets without importing backend-only serving code

## Milestone M4: Replace the Current CLI and Test Layout With Scalable Developer Surfaces
- [ ] T93: Introduce a `typer`-based command tree with sub-apps per coherent domain
- [ ] T94: Preserve command compatibility with thin wrappers during the CLI migration
- [ ] T95: Convert the test suite from `unittest`-style authoring to `pytest` fixtures, parametrization, and plain assertions
- [ ] T96: Add test markers and fixture layers that reflect unit, contract, integration, and service-backed coverage

## Milestone M5: Prepare the Repository for Frontend and Deployment Work
- [ ] T97: Define the frontend integration contract for recommendation requests and event emission
- [ ] T98: Scaffold a top-level frontend workspace with explicit non-goals and no production UI assumptions
- [ ] T99: Create an `infra/` layout for Helm charts, cluster manifests, and future Terraform or GitOps assets
- [ ] T100: Define Helm chart boundaries for backend API, simulator jobs, pipelines jobs, and shared services
- [ ] T101: Publish the end-to-end deployment topology that connects frontend, backend, simulator, pipelines, feature services, and observability
