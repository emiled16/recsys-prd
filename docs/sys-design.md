# Multimodal Fashion Recommendation System Design

## Business Context
An e-commerce fashion platform wants to improve discovery and conversion by personalizing product recommendations across the home feed, product detail pages, cart cross-sell surfaces, and search result reranking.

The platform has rich catalog metadata, product images, user interaction logs, and transaction history. The challenge is to turn those heterogeneous signals into a production-grade recommendation stack that supports both high-quality retrieval and low-latency ranking while remaining auditable, observable, and easy to evolve.

## Business Objective
Build a production-grade multimodal fashion recommendation platform that:
- retrieves relevant candidates using embeddings and vector search,
- ranks candidates with a deep learning model,
- uses point-in-time correct offline and online features,
- supports full training, evaluation, experimentation, and monitoring workflows,
- can run locally for development with infra-owned Docker Compose plus direct app processes,
- can later be promoted to production using infrastructure-as-code and GitOps.

## Non-Functional Requirements
- Low-latency online inference for retrieval and ranking.
- Point-in-time correctness for all offline training datasets.
- Near-real-time freshness for session, popularity, and inventory-sensitive features.
- Reproducible training and deployment pipelines.
- Observable serving, data, and feature pipelines.
- Clear rollback and experiment isolation for online changes.
- Dev setup must be runnable locally; architecture must still map to a production deployment model.

## High-Level Objective and Scope
The system will support:
- multimodal product understanding from text and images,
- embedding generation and vector retrieval,
- online and offline feature stores using Feast with Redis online serving,
- Kafka event ingestion and Spark Structured Streaming feature updates,
- offline feature computation with Spark and Hive-compatible tables,
- model training with experiment tracking and model registry,
- offline evaluation and online evaluation pipelines,
- A/B testing support for retrieval/ranking variants,
- model serving and end-to-end monitoring,
- orchestrated batch and streaming workflows.

The explicit project scope includes:
- Training pipeline:
  data ingestion, validation, feature generation, negative sampling, dataset construction, model training, experiment tracking, model registration, and scheduled retraining.
- Offline evaluation pipeline:
  candidate retrieval and ranking evaluation with metrics such as Recall@K, Precision@K, MAP@K, NDCG@K, MRR, calibration, and slice-based quality checks.
- Online evaluation pipeline:
  shadow validation, canary rollout, latency and error-rate monitoring, and business KPI measurement on live traffic.
- A/B testing support:
  experiment definitions, traffic allocation, guardrail metrics, winner selection criteria, and rollback procedures.
- Monitoring:
  system health, data quality, feature freshness, feature drift, embedding drift, prediction drift, latency, throughput, and model-quality proxies.

## Dataset Strategy
### Primary Offline Dataset
Use the `H&M Personalized Fashion Recommendations` dataset as the historical source of truth for:
- customers,
- articles,
- article metadata,
- article images,
- historical transactions.

This dataset is a strong base because it provides enough catalog, interaction, and visual data to justify a realistic multimodal recommendation stack.

### Synthetic Streaming Layer
Historical transactions alone are not enough to demonstrate real-time architecture, so we will replay and enrich the offline dataset into synthetic live events:
- `product_view`
- `product_click`
- `add_to_cart`
- `wishlist_add`
- `purchase`
- `search_query`
- `inventory_update`
- `price_change`

These events will be published to Kafka and consumed by Spark Structured Streaming jobs to update near-real-time features and monitoring signals.

### Multimodal Enrichment
- Text embeddings from product descriptions, categories, color/style attributes, and user search queries.
- Image embeddings from catalog images.
- Optional fused embeddings for multimodal retrieval.

### Why This Dataset Choice Works
- It is realistic enough for system-design credibility.
- It naturally supports images plus structured/text metadata.
- It gives a strong retrieval-plus-ranking story.
- It can be replayed into a streaming architecture without inventing the entire domain model.

## Proposed Model Approach
### Retrieval
Two-tower retrieval model using user/session context on one side and product multimodal embeddings on the other, with approximate nearest-neighbor search in a vector database.

### Ranking
A deeper ranking model that combines:
- user history features,
- session intent features,
- catalog attributes,
- real-time engagement features,
- retrieval scores and embedding similarities.

The ranking model can start with a DLRM-style or MLP-based architecture and evolve toward transformer-enhanced sequence modeling for user behavior.

## Core Metrics
### Offline Metrics
- Recall@K
- Precision@K
- MAP@K
- NDCG@K
- MRR
- Coverage and novelty
- Calibration and slice metrics

### Online Metrics
- CTR
- Add-to-cart rate
- Conversion rate
- Revenue per session
- Latency p50/p95/p99
- Error rate
- Timeout rate
- Experiment guardrails such as bounce rate and null-result rate

## Serving, Monitoring, and Retraining
### Serving
- Retrieval service queries the vector DB for candidate generation.
- Ranking service fetches online features from Feast/Redis and returns ordered recommendations.
- Feature hydration and inference paths are instrumented for latency and availability.
- FastAPI exposes `/recommendations`, `/healthz`, and `/metrics` endpoints for local development and smoke checks.

### Monitoring
- Infrastructure metrics: CPU, memory, network, disk, queue lag.
- Data metrics: volume, schema changes, null rates, freshness.
- Feature metrics: distribution shifts, staleness, missingness.
- Model metrics: latency, score drift, prediction drift, online KPI deltas.
- Embedding metrics: norm drift, nearest-neighbor quality drift, index freshness.
- Prometheus scrapes the FastAPI metrics endpoint and Grafana provisions a baseline recommendation dashboard for request rate, API latency, retrieval/ranking latency, and fallback rate.

### Retraining
- Scheduled retraining from point-in-time correct feature snapshots.
- Automatic model registration for qualified models.
- Promotion gated by offline thresholds and online experiment policy.

## Stack Direction
- Data source: H&M offline data + synthetic event generators
- Messaging: Kafka
- Stream processing: Spark Structured Streaming
- Offline compute: Spark
- Offline storage: Hive-compatible tables on object storage or local dev equivalent
- Feature store: Feast
- Online feature store: Redis
- Vector database: Qdrant or Milvus
- Experiment tracking / registry: MLflow
- Orchestration: Dagster
- Orchestration implementation: Dagster user code, jobs, and schedules under `orchestration/projects/recsys_orchestration/`
- Serving: FastAPI model services
- Monitoring: Prometheus + Grafana, plus data/model monitoring components
- Local infrastructure: `infra/local/docker-compose.yml`
- Prod promotion path: Terraform + Argo CD / Flux style GitOps

## Runtime Ownership Matrix

| Surface | Owns | Does not own | Local process |
| --- | --- | --- | --- |
| `backend/` | FastAPI serving, recommendation logic, online feature access, retrieval, ranking, and integration clients | Docker Compose manifests, Redpanda lifecycle, Dagster webserver/daemon | `uvicorn` from `backend/` |
| `orchestration/` | Dagster user code, schedules, jobs, and orchestration packaging | Backend API runtime, shared service containers | `dg dev` from `orchestration/projects/recsys_orchestration/` |
| `infra/local/` | Redpanda, Redis, Qdrant, MLflow, Prometheus, Grafana, local env defaults, broker bootstrap helper | FastAPI code, Dagster definitions, frontend code | `docker compose -f infra/local/docker-compose.yml ...` |
| `frontend/` | Browser app, Vite workflow, HTTP client layer | Shared infra containers, backend internals, Dagster runtime | `vite` outside Compose |
| `ops/observability/` | Prometheus and Grafana provisioning assets | Application business logic, service lifecycle commands | Mounted into infra-owned services |
| future `simulator/` | Synthetic event generation and demo traffic | Backend serving and shared service lifecycle | Direct Python or orchestrated jobs |
| future `pipelines/` | Batch normalization, feature backfills, training-set assembly, offline jobs | Online API serving and shared service lifecycle | Direct Python or orchestrated jobs |

## Local Development Process Boundaries

Local development is intentionally split by runtime ownership:

1. Shared services start from `infra/local/` through Docker Compose.
2. The backend API starts directly from `backend/` with `uvicorn`.
3. Dagster starts directly from the orchestration workspace with `dg dev`.
4. The future frontend starts directly from its own Vite workspace.

This keeps edit-refresh loops fast for application code while preserving a realistic split between
application runtimes and shared platform dependencies.
