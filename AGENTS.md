# Repository Guidelines

## Project Structure & Module Organization
`backend/recsys_prd/` contains the application code, split by subsystem: `api/`, `ingestion/`, `normalization/`, `events/`, `features/`, `retrieval/`, `ranking/`, `serving/`, `services/`, and `orchestration/`. Tests live in `backend/tests/unit/` and should mirror the subsystem they cover. Supporting definitions live in `backend/feast_repo/`, helper entrypoints in `backend/scripts/`, observability config in `ops/observability/`, and design/planning artifacts in `docs/`, `plans/`, and `checklists/`.

## Build, Test, and Development Commands
Run backend Python commands from `backend/` and prefer the checked-in virtual environment at `backend/.venv/`. When using Poetry, invoke `backend/.venv/bin/poetry` instead of a global install.

```bash
cd backend && .venv/bin/poetry install
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/python -m uvicorn recsys_prd.api.app:create_app --factory --reload
```

Use the repo root for local infrastructure:

```bash
docker compose up -d
backend/.venv/bin/python backend/scripts/ingest_hm_raw.py normalize-hm
backend/.venv/bin/python backend/scripts/ingest_hm_raw.py train-ranking-model
```

`docker compose up -d` starts Redpanda, Redis, Qdrant, MLflow, Prometheus, and Grafana. The CLI script drives ingestion, replay, feature computation, retrieval, and ranking workflows.

## Coding Style & Naming Conventions
Target Python 3.13. Use 4-space indentation, type hints on public interfaces, and keep lines within Ruff’s 100-character limit. Follow existing naming patterns: `snake_case` for modules/functions, `PascalCase` for classes, and `test_*.py` for test files. Keep subsystem boundaries intact; add code to the closest existing package instead of creating broad utility modules. Per `python-best-practices`, keep modules lightweight and segregated by concern: do not mix unrelated API models, persistence code, orchestration, and business logic in one file.

## Testing Guidelines
Use `pytest` for unit coverage. Add or update tests in `backend/tests/unit/` alongside the affected area, for example `test_ranking_training.py` for `ranking/training.py`. Prefer focused tests over large integration fixtures. There is no explicit coverage gate in the repo today, so contributors should at minimum cover changed behavior and failure paths.

## Commit & Pull Request Guidelines
Recent history follows scoped Conventional Commit subjects such as `feat(api): ...`, `fix(ranking): ...`, `docs(system): ...`, and `build(deps): ...`. Keep commits narrow and descriptive. PRs should summarize subsystem impact, list local verification commands, link any relevant plan or checklist updates, and include screenshots only when changing dashboards or other UI-facing observability surfaces.

## Configuration & Data Tips
Runtime settings are driven by `RECSYS_PRD_*` environment variables in `backend/recsys_prd/config.py`. By default, generated artifacts go under `data/`; avoid hardcoding alternate paths, and do not commit local datasets, model artifacts, or cache directories.
