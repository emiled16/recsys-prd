# Checklist for Plan v1.2

## Milestone M1: Foundation and Planning Baseline
- [x] T1: Confirm project scope and success criteria
- [x] T2: Record initial architecture direction
- [x] T3: Publish the first execution plan and tracking artifacts
- [x] T4: Refine the plan into execution-sized tasks

## Milestone M2: Dataset and Data Contracts Baseline
- [x] T5: Define the source dataset contract
- [x] T6: Define local storage and dataset layout conventions
- [x] T7: Build raw dataset ingestion
- [x] T8: Build product normalization
- [x] T9: Build customer normalization
- [x] T10: Build transaction normalization
- [x] T11: Validate normalized dataset outputs

## Milestone M3: Local Event and Feature Baseline
- [x] T12: Define event schemas for simulated online behavior
- [x] T13: Implement synthetic interaction generation
- [x] T14: Implement catalog change event generation
- [x] T15: Implement local event publishing and replay
- [x] T16: Validate replayed event quality
- [x] T17: Define offline feature entities and views
- [x] T18: Build point-in-time correct training joins
- [x] T19: Define online feature requirements
- [x] T20: Build baseline streaming feature computation
- [x] T21: Expose baseline online feature serving
- [x] T22: Validate baseline feature parity and freshness

## Milestone M4: Local Retrieval and Ranking Baseline
- [x] T23: Define multimodal representation strategy
- [x] T24: Build baseline embedding generation pipeline
- [x] T25: Build baseline vector indexing pipeline
- [x] T26: Implement baseline candidate retrieval logic
- [x] T27: Build ranking dataset generation
- [x] T28: Implement baseline ranking model training
- [x] T29: Register baseline candidate models and metadata

## Milestone M5: Codebase Refactor and Runtime Foundations
- [ ] T30: Refactor the backend into explicit pipeline, domain, and serving boundaries
- [ ] T31: Introduce environment-aware configuration and dependency management
- [ ] T32: Migrate core artifacts from ad hoc JSON and CSV outputs to Parquet-first storage contracts
- [ ] T33: Add a real local infrastructure stack in Docker Compose

## Milestone M6: Streaming and Feature Platform Integration
- [ ] T34: Wire replay publishing into Kafka-compatible topics
- [ ] T35: Implement broker-backed streaming feature computation
- [ ] T36: Stand up a Feast repository for offline and online feature definitions
- [ ] T37: Connect streaming outputs to the online feature store
- [ ] T38: Rebuild point-in-time training retrieval through Feast

## Milestone M7: Retrieval and Model Platform Integration
- [ ] T39: Replace deterministic embeddings with model-backed multimodal encoders
- [ ] T40: Replace file-backed vector indexes with Qdrant collections
- [ ] T41: Rebuild candidate retrieval on the production-oriented stack
- [ ] T42: Replace the local training registry with MLflow tracking and model registry
- [ ] T43: Upgrade ranking training to an external ML library baseline

## Milestone M8: Evaluation, Serving, and Experimentation
- [ ] T44: Build the offline evaluation pipeline on registered models and real retrieval infrastructure
- [ ] T45: Implement the recommendation API service
- [ ] T46: Add online inference safeguards and fallbacks
- [ ] T47: Implement experiment routing and exposure logging

## Milestone M9: Observability, Orchestration, and Delivery
- [ ] T48: Add metrics, dashboards, and alert baselines
- [ ] T49: Implement orchestrated workflows for batch and operational jobs
- [ ] T50: Document the production deployment path and finalize the system design
