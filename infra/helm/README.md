# Helm Layout

This directory packages each top-level runtime surface independently so deployment ownership
matches the repository structure instead of collapsing everything into one backend release.

## Charts

- `backend-api/`: FastAPI serving surface and HTTP service.
- `frontend/`: Browser delivery surface served as a static deployment.
- `orchestration/`: Dagster webserver and daemon runtime.
- `simulator-job/`: Simulator-driven replay and fake-traffic jobs.
- `pipelines-job/`: Batch normalization, feature, embedding, and training jobs.

## Environment Value Files

- `environments/local.yaml`: local demo defaults that reference infra-owned local services.
- `environments/demo.yaml`: lightweight shared cluster defaults for review or demo environments.
- `environments/prod-like.yaml`: production-shaped ownership for managed dependencies and observability.
