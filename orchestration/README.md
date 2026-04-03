# Orchestration Workspace

`orchestration/` owns Dagster user code, the local Dagster development runtime, and deployment
packaging for orchestrated workloads. It is a top-level runtime surface, not a backend-internal
module.

## Local Development

Start shared infra first:

```bash
docker compose -f infra/local/docker-compose.yml --env-file infra/local/.env.example up -d
```

Run Dagster from the orchestration workspace:

```bash
cd orchestration/projects/recsys_orchestration
uv sync
uv run dg check defs
uv run dg dev
```

The backend API stays separate and should be started from `backend/` with `uvicorn`.
