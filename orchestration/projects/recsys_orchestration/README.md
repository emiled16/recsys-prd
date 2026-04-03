# recsys_orchestration

Dagster user code for the recommendation platform lives here. This project orchestrates backend
jobs from a dedicated runtime surface instead of placing Dagster inside the backend package.

## Local Workflow

Install the project and sync dependencies:

```bash
uv sync
```

Validate that Dagster definitions load:

```bash
uv run dg check defs
```

Start the local Dagster webserver and daemon:

```bash
dg dev
```

The orchestration environment expects the backend source tree to remain available at the repository
root so Dagster definitions can call backend modules by contract during local development.

Current asset groups cover simulator replay, feature refresh, retrieval artifacts, ranking
training, evaluation, API smoke checks, online guardrail summaries, and promotion-gate reports.
