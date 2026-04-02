# Checklist for Plan v1.3

## Milestone M1: Completed Baseline
- [x] T1: Confirm project scope and success criteria
- [x] T2: Record initial architecture direction
- [x] T3: Publish the first execution plan and tracking artifacts
- [x] T4: Refine the plan into execution-sized tasks
- [x] T5: Define the source dataset contract
- [x] T6: Define local storage and dataset layout conventions
- [x] T7: Build raw dataset ingestion
- [x] T8: Build product normalization
- [x] T9: Build customer normalization
- [x] T10: Build transaction normalization
- [x] T11: Validate normalized dataset outputs
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
- [x] T23: Define multimodal representation strategy
- [x] T24: Build baseline embedding generation pipeline
- [x] T25: Build baseline vector indexing pipeline
- [x] T26: Implement baseline candidate retrieval logic
- [x] T27: Build ranking dataset generation
- [x] T28: Implement baseline ranking model training
- [x] T29: Register baseline candidate models and metadata

## Milestone M2: Refactor the Current Code Before More Features
- [ ] T30: Split backend code into stable module boundaries
- [ ] T31: Introduce typed application configuration
- [ ] T32: Separate CLI commands by subsystem
- [ ] T33: Convert core persisted datasets to Parquet
- [ ] T34: Update tests around the refactored contracts

## Milestone M3: Add the Missing Local Infrastructure
- [ ] T35: Create the Docker Compose stack
- [ ] T36: Add Kafka-compatible messaging with Redpanda
- [ ] T37: Add Redis for online feature serving
- [ ] T38: Add Qdrant for vector retrieval
- [ ] T39: Add MLflow for experiment tracking and model registry

## Milestone M4: Replace the Fake Streaming Path
- [ ] T40: Publish replay events into Redpanda topics
- [ ] T41: Add a broker consumer for feature updates
- [ ] T42: Persist online features into Redis
- [ ] T43: Re-validate online feature freshness on the real stack

## Milestone M5: Replace the Fake Feature Platform
- [ ] T44: Create the Feast repository layout
- [ ] T45: Map existing offline feature definitions into Feast
- [ ] T46: Map existing online feature definitions into Feast
- [ ] T47: Rebuild point-in-time training retrieval through Feast

## Milestone M6: Replace the Fake Retrieval Stack
- [ ] T48: Introduce real text encoders
- [ ] T49: Introduce real image encoders
- [ ] T50: Load embeddings into Qdrant collections
- [ ] T51: Rebuild candidate retrieval against Qdrant and Feast

## Milestone M7: Replace the Fake Model Platform
- [ ] T52: Log training runs to MLflow
- [ ] T53: Register trained models in MLflow Model Registry
- [ ] T54: Upgrade ranking training to a library-backed baseline

## Milestone M8: Build the Actual Serving and Evaluation Paths
- [ ] T55: Build offline retrieval evaluation
- [ ] T56: Build offline ranking evaluation
- [ ] T57: Build the FastAPI recommendation service
- [ ] T58: Add inference safeguards and fallback behavior
- [ ] T59: Add experiment assignment and exposure logging

## Milestone M9: Operability and Delivery
- [ ] T60: Add metrics instrumentation to the API and pipelines
- [ ] T61: Add Prometheus and Grafana to the local stack
- [ ] T62: Add Dagster orchestration for batch jobs
- [ ] T63: Finalize deployment and system design documentation
