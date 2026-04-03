# Infra Surfaces

Infrastructure is split by runtime purpose rather than collapsed into backend ownership.

## Directories

- `local/`: local shared-service runtime, env defaults, and helper scripts.
- `helm/`: production-like packaging for backend API, frontend, orchestration, simulator jobs, and
  pipelines jobs.

## Shared Dependency Ownership by Environment

| Dependency | Local | Demo | Production-like |
| --- | --- | --- | --- |
| Redpanda / Kafka | infra-owned container | platform-managed shared service | platform-managed shared service |
| Redis | infra-owned container | platform-managed shared service | platform-managed shared service |
| Qdrant | infra-owned container | platform-managed shared service | platform-managed shared service |
| MLflow | infra-owned container | app-managed or shared team service | platform-managed shared service |
| Prometheus / Grafana | infra-owned container | platform-managed shared service | platform-managed shared service |

Use the value files under `infra/helm/environments/` to express these ownership differences during
templating or deployment.
