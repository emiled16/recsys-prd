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
- FastAPI exposes `/healthz`, `/readyz`, `/diagnostics`, `/recommendations`, `/events`, and
  `/metrics` so the application can be tested through public contracts instead of internal module
  calls.

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

## Public API Surface for Application Testing

The backend API is expected to support realistic frontend and smoke-test journeys without reaching
into internal Python modules.

### Endpoint Audit

| Endpoint | Purpose | Consumers |
| --- | --- | --- |
| `GET /healthz` | basic liveness | container probes, simple smoke checks |
| `GET /readyz` | readiness of retriever, ranker fallback, experiment assignment, and event sink | frontend bootstrap, deployment probes |
| `GET /diagnostics` | safe local diagnostics, supported event types, and capability flags | local development UI, contract tests |
| `POST /recommendations` | retrieval and ranking request/response contract | frontend recommendation surfaces, API tests |
| `POST /events` | append-only exposure, click, and feedback tracking contract | frontend telemetry flows, experiment analysis |
| `GET /metrics` | Prometheus scrape surface | infra-owned observability |

### Recommendation Contract

- Requests must include at least one of `customer_id`, `session_id`, `query_text`, or
  `seed_article_ids`.
- `session_id` requires `customer_id` to preserve stable online context and event correlation.
- Responses include `response_id`, `experiment`, `variant`, `fallback_used`, ranked items, and
  warnings so frontend and smoke tests can reason about fallback state explicitly.

### Tracking Contract

- `POST /events` accepts append-only batches of recommendation telemetry.
- Supported event types for the public contract are:
  - `recommendation_exposure`
  - `recommendation_click`
  - `recommendation_feedback`
- Exposure and click events require a `response_id`.
- Click events also require an `article_id`.
- Feedback events require a `response_id` plus either `article_id` or `query_text`.
- The local implementation writes JSONL audit records under `data/reports/experiments/` while
  preserving a contract that can later publish through a broker-backed path.

## Frontend-to-Backend Contract

The frontend is intentionally decoupled from backend internals. It communicates only through HTTP
contracts and does not import backend code or read local data files directly.

### Recommendation Request Flow

1. The browser creates or resumes a stable `session_id`.
2. The frontend calls `POST /recommendations` with `customer_id`, `session_id`, and optional query
   or seed items.
3. The backend returns a `response_id`, experiment assignment, and ordered items.
4. The frontend uses that `response_id` for follow-up telemetry.

### Event Emission Flow

1. The frontend emits `recommendation_exposure` after rendering results.
2. The frontend emits `recommendation_click` when a user selects an item.
3. The frontend emits `recommendation_feedback` for explicit negative or qualitative feedback.

### Local Frontend Development Boundary

- The frontend runs under Vite outside Docker Compose.
- HTTP calls use the browser `fetch` API or a thin wrapper around it.
- Axios is intentionally excluded to keep the client layer minimal and aligned with the Vite local
  loop.

## Embedding, Evaluation, and Promotion Lifecycle

### Embedding Rebuilds

- The retrieval stack must persist text, image, and fused embedding artifacts with explicit model
  metadata, dataset snapshot references, generation timestamps, and downstream index lineage.
- Rebuilds are treated as reproducible batch jobs owned by `pipelines/` and orchestrated by
  `orchestration/`.

### Promotion Gates

- Candidate retrieval and ranking artifacts must satisfy offline quality thresholds before
  promotion.
- Artifact manifests must include dataset references, config metadata, and linked evaluation
  outputs.
- API smoke checks and experiment-readiness checks must pass before an artifact is promoted from
  latest-run to candidate or serving-ready state.

### Online Evaluation Loop

- Recommendation responses generate exposure records keyed by `response_id`.
- Follow-up click and feedback events join back to those exposures for online analysis.
- Guardrails include timeout rate, null-result rate, error rate, fallback rate, and explicit drift
  signals for retrieval quality.
- Rollback triggers are owned by orchestration and should reference the latest candidate registry
  plus recent guardrail reports.

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
| `infra/helm/` | Deployment packaging, chart boundaries, environment overlays | Serving logic, pipeline code, frontend app logic | `helm template` or `helm upgrade` |
| `ops/observability/` | Prometheus and Grafana provisioning assets | Application business logic, service lifecycle commands | Mounted into infra-owned services |
| `simulator/` | Synthetic event generation and demo traffic | Backend serving and shared service lifecycle | Direct Python or orchestrated jobs |
| `pipelines/` | Batch normalization, feature backfills, embedding rebuilds, training-set assembly, offline jobs | Online API serving and shared service lifecycle | Direct Python or orchestrated jobs |

## Local Development Process Boundaries

Local development is intentionally split by runtime ownership:

1. Shared services start from `infra/local/` through Docker Compose.
2. The backend API starts directly from `backend/` with `uvicorn`.
3. Dagster starts directly from the orchestration workspace with `dg dev`.
4. The future frontend starts directly from its own Vite workspace.

This keeps edit-refresh loops fast for application code while preserving a realistic split between
application runtimes and shared platform dependencies.

## Deployment Topology

### Local Development Mode

- `infra/local/` runs Redpanda, Redis, Qdrant, MLflow, Prometheus, and Grafana.
- `backend/` runs directly with Uvicorn and talks to shared services through configuration.
- `frontend/` runs directly with Vite and uses HTTP calls into the backend API.
- `orchestration/` runs Dagster separately for local job launches, schedules, and promotion checks.

### Production-Like Mode

- `infra/helm/backend-api/` deploys the FastAPI service.
- `infra/helm/frontend/` deploys the frontend delivery surface.
- `infra/helm/orchestration/` deploys the Dagster control plane.
- `infra/helm/simulator-job/` deploys replay and synthetic-traffic jobs.
- `simulator/` owns replay generation, replay validation, and fake traffic producers.
- Shared replay artifact helpers such as JSONL readers/writers and deterministic event ID builders
  are treated as cross-runtime utilities under `recsys_prd.io.*`, not as backend-owned event
  runtime modules.
- `infra/helm/pipelines-job/` deploys offline batch jobs for normalization, features, embeddings,
  training, and evaluation.
- Shared dependencies such as Kafka/Redpanda, Redis, Qdrant, MLflow, and observability remain
  external or platform-managed depending on the target environment.
