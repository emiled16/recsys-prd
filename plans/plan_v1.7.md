# Plan v1.7

## Context
`v1.6` established the top-level runtime surfaces for `backend/`, `pipelines/`, `simulator/`, `orchestration/`, `frontend/`, and `infra/`, and that work is now complete. The remaining gap is semantic ownership inside the Python codebase. Several batch- and simulator-oriented modules still live under [`backend/recsys_prd`](/Users/emdim/dev/recsys-prd/backend/recsys_prd), especially `normalization/`, `validation/`, and parts of `events/`. Training responsibilities are also still split awkwardly between backend-owned modules and pipeline entrypoints.

This plan assumes the ownership model discussed in the current chat is already accepted as the design premise:
- `backend` owns API, serving, online contracts, and MLOps control surfaces that support serving and promotion.
- `pipelines` owns offline dataset preparation, normalization, validation, feature materialization, and training dataset assembly.
- `simulator` owns synthetic event generation, replay batches, fake traffic, and replay validation.
- offline training execution belongs to pipelines and orchestration, while backend retains only serving-facing model contracts, registries, and promotion logic.
- Spark becomes the default data-processing runtime for offline pipeline stages instead of leaving normalization as an in-process Python implementation indefinitely.

The goal of this version is to execute that model through code migration, runtime changes, and boundary tests while preserving existing artifact contracts, Dagster orchestration, and local reproducibility.

## Milestones

### M1: Prepare the Codebase for Boundary Migration

#### Task T131: Create target package scaffolds for pipeline-owned offline code, simulator-owned replay code, and shared artifact IO
- Description: Add the concrete package directories and module entrypoints that will receive migrated code from `backend/recsys_prd`. This should include pipeline-owned locations for normalization and validation, simulator-owned locations for replay generation and replay validation, and a narrow shared package for artifact IO that both backend and offline jobs can consume without implying the wrong owner.
- Outputs: Importable package scaffolds with `__init__.py` files and placeholder entry modules ready for code moves.
- Files involved: `pipelines/`, `simulator/`, shared Python package paths under `backend/recsys_prd/` only where cross-runtime contracts are intentionally shared
- Dependencies: None

#### Task T132: Audit and classify current imports from backend normalization, validation, and events modules
- Description: Build an executable migration inventory by tracing which backend, pipeline, simulator, orchestration, and test modules still import `recsys_prd.normalization`, `recsys_prd.validation`, and `recsys_prd.events`. Classify each import as pipeline-owned, simulator-owned, backend-owned, or shared-utility usage so the subsequent refactors can be performed without guessing.
- Inputs: Current Python import graph and runtime entrypoints
- Outputs: Migration inventory used to drive code moves and shim removal
- Files involved: source packages, orchestration definitions, CLI modules, tests
- Dependencies: T131

#### Task T133: Add compatibility shims for legacy imports that will be migrated out of backend-owned paths
- Description: Introduce temporary re-export modules or adapter entrypoints so code can be moved incrementally without breaking the CLI, Dagster assets, or tests in one large rename. Each shim should clearly indicate its replacement target and be narrow enough to delete once the downstream imports are updated.
- Outputs: Temporary compatibility layer for staged package migration, with each shim mapped to a concrete removal step later in this plan
- Files involved: current `backend/recsys_prd/normalization/`, `backend/recsys_prd/validation/`, `backend/recsys_prd/events/`, target pipeline and simulator modules
- Dependencies: T131

### M2: Introduce Spark as the Default Runtime for Offline Data Pipelines

#### Task T134: Define the Spark runtime contract for normalization, validation, and training-dataset preparation
- Description: Add the concrete Spark runtime settings and developer entrypoints for offline data work, including library choice (`pyspark`), local execution mode, configuration model, schema enforcement expectations, partitioning strategy, deterministic output rules, and how Spark jobs interoperate with the existing `data/` artifact layout. This task should also define what remains out of scope for Spark, such as the online API and serving path.
- Outputs: Spark runtime configuration and documented execution standard for offline jobs.
- Libraries and tools: `pyspark`, Parquet, local filesystem-backed Spark execution
- Files involved: `docs/key-decisions.md`, `docs/data-layout.md`, `README.md`
- Dependencies: T131, T132, T133

#### Task T135: Add a shared Spark session bootstrap and offline dataset IO layer for pipeline jobs
- Description: Implement a pipeline-owned Spark bootstrap module that creates configured `SparkSession` instances for local and orchestrated runs, plus dataset readers and writers that enforce the repository's schema and artifact path conventions. This should replace ad hoc Pandas/file handling in offline jobs with explicit Spark-owned entrypoints.
- Inputs: App settings, raw dataset locations, normalized artifact paths, schema contracts
- Outputs: Reusable Spark session factory and Spark-based IO helpers for pipeline jobs
- Libraries and tools: `pyspark`
- Files involved: `pipelines/`, `backend/recsys_prd/config.py`, shared schema modules
- Dependencies: T134

#### Task T136: Define parity checks between the current offline outputs and the Spark-produced outputs
- Description: Specify the validation strategy that ensures Spark migrations preserve current semantics, including row counts, required-field completeness, key uniqueness, timestamp normalization, partition contents, and deterministic ordering where relevant. The expected result is a migration safety net before pipeline code is rewritten.
- Outputs: Parity and regression validation spec for Spark migrations
- Files involved: `docs/data-layout.md`, `backend/tests/unit/`, future pipeline validation modules
- Dependencies: T134, T135

### M3: Move Normalization and Offline Validation Out of the Backend Package

#### Task T137: Create pipeline-owned normalization packages for customers, products, transactions, and shared cleaning logic
- Description: Move the current normalization modules out of `backend/recsys_prd/normalization` into pipeline-owned packages that reflect their batch-only role. Preserve the current dataset contracts and command behavior while relocating transforms, schemas, writers, and orchestration entrypoints to `pipelines/` or a pipeline-scoped Python package.
- Inputs: Current normalization modules, normalization CLI commands, current normalized artifact layout
- Outputs: Pipeline-owned normalization package with no imports from backend-serving modules
- Files involved: current `backend/recsys_prd/normalization/`, `pipelines/normalization.py`, pipeline package init files
- Dependencies: T132, T135, T136

#### Task T138: Reimplement normalization execution on Spark while preserving the normalized artifact contract
- Description: Replace the in-process normalization execution path with Spark-based transforms for raw H&M source tables. Preserve the normalized dataset names, schema contracts, profile metadata, and writer behavior expected by downstream feature, retrieval, and ranking code so the migration changes the runtime but not the interface.
- Inputs: Raw H&M datasets, normalization schemas, Spark bootstrap, artifact path settings
- Outputs: Spark-backed normalization job producing the existing normalized datasets under `data/normalized/`
- Libraries and tools: `pyspark`
- Files involved: pipeline normalization modules, writers, schema contracts, tests
- Dependencies: T137

#### Task T139: Move normalized-data validation into a pipeline-owned validation package with Spark-aware checks
- Description: Relocate `backend/recsys_prd/validation/hm_normalized.py` into the pipeline surface and update it so data-quality checks can operate against Spark-produced outputs without leaking pipeline concerns back into the backend package. Keep the report artifacts and failure conditions stable for downstream consumers.
- Outputs: Pipeline-owned normalized-data validation module and updated validation commands/tests
- Libraries and tools: `pyspark`
- Files involved: current `backend/recsys_prd/validation/`, pipeline validation modules, CLI/orchestration entrypoints
- Dependencies: T136, T138

### M4: Move Simulator and Replay Concerns Fully Out of the Backend Package

#### Task T140: Split backend `events` into simulator-owned replay generation and shared artifact IO contracts
- Description: Remove the current mixed ownership in `backend/recsys_prd/events` by moving replay generation, catalog generation, interaction generation, replay validation, and simulator contracts into `simulator/`. If low-level JSONL helpers still need to be shared, place them in a narrow artifact IO package instead of leaving them under an `events` namespace that implies backend ownership.
- Inputs: Current `events` modules, simulator package, downstream imports in ranking, retrieval, serving, and tests
- Outputs: Simulator-owned replay modules and a minimized shared IO surface
- Files involved: current `backend/recsys_prd/events/`, `simulator/`, `backend/recsys_prd/io/` or equivalent shared package
- Dependencies: T132, T133

#### Task T141: Update backend, pipeline, and evaluator code to consume simulator artifacts through explicit contracts instead of backend event imports
- Description: Refactor downstream code paths that currently import `recsys_prd.events.*` so they consume replay manifests, event logs, and artifact readers from simulator-owned or shared-contract modules. The main goal is to preserve artifact compatibility while removing accidental backend ownership of simulator outputs.
- Outputs: Updated imports and explicit handoff contracts across simulator, pipelines, retrieval, ranking, and serving
- Files involved: backend retrieval/ranking/serving modules, simulator modules, tests
- Dependencies: T140

#### Task T142: Publish simulator ownership and runtime rules for replay generation, fake traffic, and event validation
- Description: Expand the architecture docs so they define simulator responsibilities beyond static replay generation, including fake traffic producers, event schema ownership, replay validation, and how simulator outputs are consumed by backend and pipeline surfaces during local development and orchestration.
- Outputs: Simulator runtime and ownership guide
- Files involved: `docs/event-contract.md`, `docs/sys-design.md`, `README.md`
- Dependencies: T140, T141

### M5: Separate Offline Training Pipelines From Backend-Serving Model Components

#### Task T143: Move ranking training dataset builders and offline training entrypoints into the pipeline-owned training surface
- Description: Relocate offline training-dataset assembly, point-in-time dataset preparation, and batch training job entrypoints so they are owned by the pipeline surface instead of the backend package. Preserve current artifact manifests and downstream evaluator inputs while making it explicit that batch training execution is not part of the serving backend.
- Inputs: Current training dataset builders, PIT feature builders, ranking dataset modules, orchestration assets
- Outputs: Pipeline-owned training dataset and model-build entrypoints
- Files involved: `pipelines/training_dataset.py`, `pipelines/ranking_dataset.py`, backend ranking dataset/training modules, orchestration assets
- Dependencies: T132, T133, T138, T139

#### Task T144: Define the backend-owned serving model contract separate from pipeline-owned training implementations
- Description: Introduce or refine backend-owned contracts for loading approved models, invoking ranking and retrieval inference, and exposing promotion metadata without coupling the backend runtime to offline fitting code. This should preserve backend access to registries and approved artifacts while preventing it from owning batch training implementations.
- Outputs: Serving model contract and module boundaries between offline training and online inference
- Files involved: `backend/recsys_prd/ranking/`, `backend/recsys_prd/retrieval/`, `backend/recsys_prd/serving/`, schema contracts
- Dependencies: T133, T143

#### Task T145: Move offline evaluation and training orchestration imports to pipeline-owned or orchestration-owned entrypoints
- Description: Refactor Dagster assets, CLI commands, and helper entrypoints so offline training, offline evaluation, and batch rebuilds are launched from pipeline-owned or orchestration-owned modules rather than backend-serving package paths. Keep backend-owned promotion and serving checks accessible where they belong.
- Outputs: Clear runtime entrypoints for offline training and evaluation that no longer imply backend ownership
- Files involved: `backend/recsys_prd/cli.py`, `orchestration/projects/recsys_orchestration/`, `pipelines/`, backend evaluator modules
- Dependencies: T143, T144

### M6: Align Orchestration, Testing, and Documentation With the New Boundaries

#### Task T146: Remove temporary migration shims after downstream imports have been moved to their owning packages
- Description: Delete the temporary compatibility modules introduced earlier in the migration once CLI commands, Dagster assets, tests, and application code import only the new pipeline-owned, simulator-owned, backend-owned, or shared-contract paths. The final state must not retain re-export layers that preserve the old backend-owned locations.
- Outputs: Clean package graph with no temporary migration shims remaining
- Files involved: shim modules under `backend/recsys_prd/normalization/`, `backend/recsys_prd/validation/`, `backend/recsys_prd/events/`, updated downstream imports
- Dependencies: T139, T141, T145

#### Task T147: Refactor Dagster asset definitions to import pipeline, simulator, and backend entrypoints from their owning surfaces only
- Description: Update the orchestration workspace so normalization, validation, replay generation, training, evaluation, and serving checks are each imported from the correct owning package. The expected outcome is that Dagster reflects the same ownership model documented in the architecture rather than silently depending on backend-internal modules for batch work.
- Outputs: Ownership-aligned Dagster definitions and jobs
- Files involved: `orchestration/projects/recsys_orchestration/src/recsys_orchestration/defs/`
- Dependencies: T139, T141, T145

#### Task T148: Add architecture-level regression tests for backend-versus-pipeline-versus-simulator imports and artifact handoffs
- Description: Add tests that fail when batch-only modules reappear under backend-owned packages or when runtime surfaces depend on the wrong owners. Include handoff tests for normalized datasets, replay batches, and training artifacts so the refactor is protected by executable boundary checks rather than documentation alone.
- Outputs: Import-boundary and artifact-handoff regression coverage
- Files involved: `backend/tests/`, pipeline tests, simulator tests, shared fixtures
- Dependencies: T146, T147

#### Task T149: Publish the updated topology and migration notes for the Spark-backed pipeline architecture
- Description: Update the system design, local development docs, and migration notes to show the final package ownership after the refactor, including where Spark runs, how simulator outputs flow into online and offline consumers, and how training execution differs from backend serving. Document what was moved, what remains backend-owned, and which contracts were intentionally preserved.
- Outputs: Updated architecture documentation and implementation notes for the new steady-state layout
- Files involved: `docs/sys-design.md`, `docs/data-layout.md`, `README.md`
- Dependencies: T142, T146, T147, T148

## Revisions
- v1.7: Builds on completed `v1.6` work by planning the remaining semantic reorganization inside the codebase. This version assumes the ownership model has already been agreed and focuses on executable migration work: adding target package scaffolds, auditing current imports, introducing temporary shims, moving offline normalization and validation out of `backend/recsys_prd`, fully separating simulator concerns from backend event utilities, clarifying training boundaries through code moves, and introducing `pyspark` as the default runtime for offline data pipelines while preserving current artifact contracts and orchestration behavior.
