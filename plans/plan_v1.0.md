# Plan v1.0

## Context
Build a production-grade multimodal fashion recommendation platform for learning ML systems design. The system must cover multimodal retrieval and ranking, point-in-time correct feature engineering, streaming and batch data infrastructure, model training, offline and online evaluation, A/B testing support, and monitoring. Local development should run with infrastructure in `docker-compose` while backend and frontend remain outside containers for fast iteration.

## Milestones

### M1: Design and Project Scaffolding

#### Task T1: Define scope and architecture direction
- Description: Produce the initial system design scope, dataset strategy, key requirements, and documented architecture decisions.
- Files involved: `docs/sys-design.md`, `docs/concepts.md`, `docs/lessons.md`, `docs/progress.md`, `docs/architectural-decisions.md`
- Dependencies: None

#### Task T2: Create execution plan and tracking artifacts
- Description: Create the versioned implementation plan and checklist that will drive subsequent work.
- Files involved: `plans/plan_v1.0.md`, `checklists/plan_v1.0_checklist.md`, `docs/progress.md`
- Dependencies: T1

### M2: Data Foundation

#### Task T3: Ingest and normalize the H&M dataset
- Description: Add reproducible data ingestion and normalization steps for users, products, transactions, and image metadata.
- Files involved: `data/`, `src/`, `README` or setup docs
- Dependencies: T2

#### Task T4: Implement synthetic event generation and replay
- Description: Generate realistic interaction and catalog update events and publish them into Kafka topics for local development.
- Files involved: `src/`, `docker-compose.yml`, dev scripts
- Dependencies: T3

### M3: Feature Platform

#### Task T5: Define offline feature views and point-in-time training joins
- Description: Implement feature definitions and historical feature retrieval paths with point-in-time correctness guarantees.
- Files involved: Feast definitions, Spark jobs, offline storage definitions
- Dependencies: T3

#### Task T6: Implement online feature computation and serving
- Description: Compute near-real-time features from Kafka streams and serve them through Redis-backed Feast online storage.
- Files involved: Spark streaming jobs, Feast config, Redis integration
- Dependencies: T4, T5

### M4: Retrieval and Ranking Models

#### Task T7: Build embedding and vector retrieval pipeline
- Description: Generate text and image embeddings, index them in the vector database, and expose retrieval logic.
- Files involved: model code, embedding jobs, vector DB integration
- Dependencies: T3, T5

#### Task T8: Build ranking model training pipeline
- Description: Train the ranking model with experiment tracking, model registry integration, and reproducible configuration.
- Files involved: training pipeline, MLflow integration, model configs
- Dependencies: T5, T7

### M5: Evaluation and Serving

#### Task T9: Implement offline evaluation pipeline
- Description: Compute retrieval and ranking metrics, slice reports, and promotion gates for candidate models.
- Files involved: evaluation pipeline, reports, training artifacts
- Dependencies: T8

#### Task T10: Implement online serving path
- Description: Build retrieval and ranking services that fetch features, run inference, and expose recommendation endpoints.
- Files involved: backend services, inference code, Feast/Redis and vector DB integrations
- Dependencies: T6, T7, T8

#### Task T11: Add online evaluation and A/B testing support
- Description: Add experiment routing, shadow or canary support, guardrail metrics, and measurement hooks for live evaluation.
- Files involved: serving layer, experiment config, monitoring config
- Dependencies: T9, T10

### M6: Platform Reliability and Delivery

#### Task T12: Add monitoring and observability
- Description: Instrument infrastructure, data, feature, and model health with dashboards and alerts for the local stack.
- Files involved: monitoring stack, metrics instrumentation, dashboards, docs
- Dependencies: T6, T10, T11

#### Task T13: Add orchestration for batch and streaming workflows
- Description: Define orchestrated jobs for ingestion, feature materialization, training, evaluation, and deployment workflows.
- Files involved: orchestration definitions, job configs, docs
- Dependencies: T4, T5, T8, T9

#### Task T14: Build local infrastructure and production deployment story
- Description: Assemble `docker-compose` for infra, document production IaC and GitOps deployment approach, and connect the design to the runtime layout.
- Files involved: `docker-compose.yml`, deployment docs, IaC and GitOps docs
- Dependencies: T6, T7, T10, T12, T13

#### Task T15: Finalize system design documentation
- Description: Expand the system design with ASCII diagrams, tradeoffs, deep dives, deployment flows, and lessons learned.
- Files involved: `docs/sys-design.md`, `docs/concepts.md`, `docs/lessons.md`, `docs/architectural-decisions.md`
- Dependencies: T9, T11, T12, T13, T14

## Revisions
- v1.0: Initial version.
