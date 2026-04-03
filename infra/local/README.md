# Local Runtime

`infra/local/` owns the shared local runtime for infrastructure services that the application
consumes by configuration:

- Redpanda
- Redis
- Qdrant
- MLflow
- Prometheus
- Grafana

The backend API, future frontend, and Dagster processes run outside Docker Compose during local
development. This directory owns the Compose manifest, environment defaults, and infra-scoped
bootstrap helpers for the shared services only.

## Commands

Start shared services:

```bash
docker compose -f infra/local/docker-compose.yml --env-file infra/local/.env.example up -d
```

Bootstrap Redpanda topics after the broker is healthy:

```bash
backend/.venv/bin/python infra/local/scripts/bootstrap_redpanda_topics.py
```
