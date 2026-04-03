# Multimodal Fashion Recommendation Platform

This repository captures the design and implementation plan for a production-grade multimodal recommendation system focused on fashion e-commerce.

The project is intended as an ML systems design exercise with a strong platform focus. It covers data ingestion, streaming and batch pipelines, feature engineering, retrieval and ranking, evaluation, experimentation, observability, and deployment design.

## Current Status

The repository now includes a runnable backend stack for ingestion, normalization, replay, features, retrieval, ranking, evaluation, recommendation serving, experimentation logging, and local observability.

## Repository Structure

- `backend/`: Python backend package, scripts, and tests.
- `simulator/`: Simulator-owned synthetic event generation, replay manifests, and replay validation.
- `pipelines/`: Offline normalization, PIT dataset building, Feast batch flows, and ranking-dataset assembly.
- `infra/local/`: Docker Compose, env defaults, and bootstrap helpers for shared local services.
- `infra/helm/`: Helm charts and environment overlays for backend, orchestration, simulator, pipelines, and frontend deployment surfaces.
- `orchestration/`: Dagster workspace, user code, and deployment packaging.
- `frontend/`: Vite-based frontend workspace that runs outside Docker Compose during local development.
- `docs/`: Project context, charter, system design, and progress tracking.
- `plans/`: Versioned implementation plans.
- `checklists/`: Matching execution checklists for each plan version.

## Key Documents

- `docs/project-charter.md`: Project scope, objectives, constraints, and acceptance criteria.
- `docs/dataset-contract.md`: Source dataset contract for H&M entities and image assets.
- `docs/data-layout.md`: Local storage and dataset layout conventions for raw and derived data.
- `docs/offline-feature-spec.md`: Offline feature entities, feature views, and source mappings.
- `docs/online-feature-requirements.md`: Freshness and streaming-input requirements for online features.
- `docs/multimodal-representation-strategy.md`: Retrieval modality and fusion strategy for product representations.
- `plans/plan_v1.7.md`: Current implementation plan.
- `checklists/plan_v1.7_checklist.md`: Current execution checklist.

## Working Principles

- Keep the architecture production-oriented even when local development uses simplified infrastructure.
- Preserve versioned planning artifacts instead of rewriting history.
- Prefer explicit documentation of tradeoffs, assumptions, and operational concerns.

## Raw Ingestion

Use the raw-ingestion command to place the H&M source dataset into the local storage layout:

```bash
python3 backend/scripts/ingest_hm_raw.py ingest-hm-raw --source /path/to/hm_dataset
```

Use `--replace` if `data/raw/hm/` already contains a previous ingest and you want to overwrite it.

Normalize the ingested raw layer and validate the outputs with:

```bash
python3 backend/scripts/ingest_hm_raw.py normalize-hm
python3 backend/scripts/ingest_hm_raw.py validate-hm-normalized
```

Generate and validate local replay batches with:

```bash
python3 backend/scripts/ingest_hm_raw.py generate-hm-events
python3 backend/scripts/ingest_hm_raw.py validate-hm-events
```

Build the first point-in-time correct offline training dataset with:

```bash
python3 backend/scripts/ingest_hm_raw.py build-pit-training-set
```

Build the first ranking training dataset with observed positives and retrieval negatives with:

```bash
python3 backend/scripts/ingest_hm_raw.py build-ranking-dataset
```

Train the first local ranking baseline and write tracked model artifacts with:

```bash
python3 backend/scripts/ingest_hm_raw.py train-ranking-model
```

Register the latest trained ranking model into the local candidate registry with:

```bash
python3 backend/scripts/ingest_hm_raw.py register-ranking-model
```

Evaluate retrieval quality, the registered ranking model, and offline ranking quality with:

```bash
python3 backend/scripts/ingest_hm_raw.py evaluate-retrieval
python3 backend/scripts/ingest_hm_raw.py evaluate-ranking-model
python3 backend/scripts/ingest_hm_raw.py evaluate-ranking-quality
```

Compute local online feature snapshots from replayed events with:

```bash
python3 backend/scripts/ingest_hm_raw.py compute-online-features
```

Read one payload back from the local online feature store with:

```bash
python3 backend/scripts/ingest_hm_raw.py get-online-features --entity customer --customer-id 0001
```

Run the FastAPI recommendation service locally with:

```bash
cd backend
.venv/bin/poetry run uvicorn recsys_prd.api.app:create_app --factory --reload
```

The public application test surface now includes:

- `GET /healthz`: liveness.
- `GET /readyz`: readiness for retrieval, ranking fallback, and local event logging.
- `GET /diagnostics`: safe contract and capability diagnostics for frontend and local smoke tests.
- `POST /recommendations`: deterministic recommendation request contract.
- `POST /events`: append-only recommendation exposure, click, and feedback tracking.
- `GET /metrics`: Prometheus metrics.

Start the local shared infra stack, Prometheus, and Grafana with:

```bash
docker compose -f infra/local/docker-compose.yml --env-file infra/local/.env.example up -d
```

Grafana is available at `http://localhost:3000` and Prometheus at `http://localhost:9090`.

Bootstrap Redpanda topics from the infra-owned helper after the broker is up:

```bash
backend/.venv/bin/python infra/local/scripts/bootstrap_redpanda_topics.py
```

Run the frontend outside Compose with Vite:

```bash
cd frontend
npm install
npm run dev
```

An end-to-end local developer loop is also available through the helper script:

```bash
infra/local/scripts/run_local_app.sh
```

This script expects shared services to already be running from `infra/local/docker-compose.yml`.

Run Dagster locally from the dedicated orchestration workspace:

```bash
cd orchestration/projects/recsys_orchestration
uv sync
uv run dg check defs
uv run dg dev
```

Offline pipeline jobs use Spark as their default execution runtime. Local jobs currently target
`local[*]` with configuration sourced from:
- `RECSYS_PRD_SPARK_APP_NAME`
- `RECSYS_PRD_SPARK_MASTER`
- `RECSYS_PRD_SPARK_WAREHOUSE_DIR`
- `RECSYS_PRD_SPARK_DRIVER_BIND_ADDRESS`
- `RECSYS_PRD_SPARK_UI_ENABLED`
- `RECSYS_PRD_SPARK_SHUFFLE_PARTITIONS`

The pipeline runtime contract is:
- initialize Spark only from pipeline-owned helpers such as `pipelines.spark.build_spark_session`
- read and write offline datasets through `pipelines.spark.io`
- keep Spark imports out of FastAPI, serving, and online feature modules
- preserve the existing artifact paths under `data/normalized/`, `data/features/offline/`, and `data/models/training_sets/` even when the execution engine changes
- validate Spark migrations against the pre-Spark outputs with row-count, schema, key, and timestamp parity checks before deleting compatibility paths

Spark is intended for offline-only pipeline stages such as normalization, validation, and
training-set preparation. It is not part of the FastAPI serving path.

Validate online freshness and offline-online feature parity with:

```bash
python3 backend/scripts/ingest_hm_raw.py validate-feature-parity
```

Package the deployment surfaces with Helm by selecting the chart that matches the top-level runtime:

```bash
helm template backend-api infra/helm/backend-api -f infra/helm/environments/local.yaml
helm template orchestration infra/helm/orchestration -f infra/helm/environments/demo.yaml
```

## Planned System Capabilities

- Historical dataset ingestion and normalization
- Synthetic online event generation and replay
- Offline and online feature computation
- Multimodal retrieval and ranking
- Offline and online evaluation
- Experimentation support
- Monitoring and orchestration
- Local development infrastructure and production deployment design

## Local Development Topology

- `infra/local/` owns Redpanda, Redis, Qdrant, MLflow, Prometheus, and Grafana through Docker
  Compose.
- `backend/` owns the FastAPI app, serving logic, feature access, retrieval, ranking, and service
  integrations. It consumes shared services only through configuration.
- `simulator/` owns synthetic traffic generation, replay-batch publication, and replay contract
  validation.
- Shared replay helpers such as JSONL artifact IO and deterministic event ID builders live under
  `backend/recsys_prd/io/` because they are consumed across simulator, pipelines, and backend
  surfaces.
- `pipelines/` owns normalization, offline feature generation, Feast materialization, and ranking
  dataset assembly.
- `orchestration/` owns Dagster definitions, schedules, and local Dagster runtime commands.
- `frontend/` runs outside Compose with Vite and calls the backend over HTTP through a thin
  `fetch`-based client.
- `infra/helm/` owns production-like packaging for backend API, frontend, orchestration, simulator
  jobs, and pipelines jobs.
