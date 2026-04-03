# Checklist for Plan v1.7

## Milestone M1: Prepare the Codebase for Boundary Migration
- [x] T131: Create target package scaffolds for pipeline-owned offline code, simulator-owned replay code, and shared artifact IO
- [x] T132: Audit and classify current imports from backend normalization, validation, and events modules
- [x] T133: Add compatibility shims for legacy imports that will be migrated out of backend-owned paths

## Milestone M2: Introduce Spark as the Default Runtime for Offline Data Pipelines
- [x] T134: Define the Spark runtime contract for normalization, validation, and training-dataset preparation
- [x] T135: Add a shared Spark session bootstrap and offline dataset IO layer for pipeline jobs
- [x] T136: Define parity checks between the current offline outputs and the Spark-produced outputs

## Milestone M3: Move Normalization and Offline Validation Out of the Backend Package
- [x] T137: Create pipeline-owned normalization packages for customers, products, transactions, and shared cleaning logic
- [x] T138: Reimplement normalization execution on Spark while preserving the normalized artifact contract
- [x] T139: Move normalized-data validation into a pipeline-owned validation package with Spark-aware checks

## Milestone M4: Move Simulator and Replay Concerns Fully Out of the Backend Package
- [x] T140: Split backend `events` into simulator-owned replay generation and shared artifact IO contracts
- [x] T141: Update backend, pipeline, and evaluator code to consume simulator artifacts through explicit contracts instead of backend event imports
- [x] T142: Publish simulator ownership and runtime rules for replay generation, fake traffic, and event validation

## Milestone M5: Separate Offline Training Pipelines From Backend-Serving Model Components
- [x] T143: Move ranking training dataset builders and offline training entrypoints into the pipeline-owned training surface
- [ ] T144: Define the backend-owned serving model contract separate from pipeline-owned training implementations
- [ ] T145: Move offline evaluation and training orchestration imports to pipeline-owned or orchestration-owned entrypoints

## Milestone M6: Align Orchestration, Testing, and Documentation With the New Boundaries
- [ ] T146: Remove temporary migration shims after downstream imports have been moved to their owning packages
- [ ] T147: Refactor Dagster asset definitions to import pipeline, simulator, and backend entrypoints from their owning surfaces only
- [ ] T148: Add architecture-level regression tests for backend-versus-pipeline-versus-simulator imports and artifact handoffs
- [ ] T149: Publish the updated topology and migration notes for the Spark-backed pipeline architecture
