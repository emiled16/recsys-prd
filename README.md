# Multimodal Fashion Recommendation Platform

This repository captures the design and implementation plan for a production-grade multimodal recommendation system focused on fashion e-commerce.

The project is intended as an ML systems design exercise with a strong platform focus. It covers data ingestion, streaming and batch pipelines, feature engineering, retrieval and ranking, evaluation, experimentation, observability, and deployment design.

## Current Status

The repository currently contains project documentation and versioned implementation plans. Application code and infrastructure definitions will be added incrementally as the execution plan is carried out.

The first implementation slice now includes backend Python scaffolding plus a raw H&M ingestion command that lands dataset assets under `data/raw/hm/`.

## Repository Structure

- `backend/`: Python backend package, scripts, and tests.
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
- `plans/plan_v1.1.md`: Current granular implementation plan.
- `checklists/plan_v1.1_checklist.md`: Current execution checklist.

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

Compute local online feature snapshots from replayed events with:

```bash
python3 backend/scripts/ingest_hm_raw.py compute-online-features
```

Read one payload back from the local online feature store with:

```bash
python3 backend/scripts/ingest_hm_raw.py get-online-features --entity customer --customer-id 0001
```

Validate online freshness and offline-online feature parity with:

```bash
python3 backend/scripts/ingest_hm_raw.py validate-feature-parity
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
