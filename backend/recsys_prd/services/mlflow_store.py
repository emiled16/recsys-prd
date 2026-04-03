from __future__ import annotations

from pathlib import Path
from typing import Any

import mlflow
from mlflow.tracking import MlflowClient

from recsys_prd.config import AppSettings, get_app_settings


def probe_mlflow_tracking(
    settings: AppSettings | None = None,
    *,
    client: Any | None = None,
) -> dict[str, Any]:
    """Verify MLflow tracking by logging a probe run."""
    logger = MLflowRunLogger(settings=settings, client=client)
    result = logger.log_training_run(
        run_name="connectivity_probe",
        params={"probe": "true"},
        metrics={"ok": 1.0},
        tags={"component": "mlflow_probe"},
        artifact_paths=[],
    )
    return {
        "tracking_uri": logger.tracking_uri,
        "run_id": result["run_id"],
    }


class MLflowRunLogger:
    """Log params, metrics, tags, and artifacts to MLflow."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        client: Any | None = None,
    ) -> None:
        self.settings = settings or get_app_settings()
        self.tracking_uri = self.settings.services.mlflow.tracking_uri
        mlflow.set_tracking_uri(self.tracking_uri)
        self.client = client or MlflowClient(tracking_uri=self.tracking_uri)

    def log_training_run(
        self,
        *,
        run_name: str,
        params: dict[str, Any],
        metrics: dict[str, float],
        tags: dict[str, str],
        artifact_paths: list[Path],
        lineage: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        run = self.client.create_run(
            experiment_id="0",
            tags={"mlflow.runName": run_name, **tags},
        )
        for key, value in _flatten_mapping(params).items():
            self.client.log_param(run.info.run_id, key, value)
        for key, value in _flatten_mapping(lineage or {}).items():
            self.client.log_param(run.info.run_id, f"lineage.{key}", value)
        for key, value in _flatten_mapping(metrics).items():
            self.client.log_metric(run.info.run_id, key, float(value))
        for artifact_path in artifact_paths:
            self.client.log_artifact(run.info.run_id, str(artifact_path))
        return {"run_id": run.info.run_id}


class MLflowModelRegistrar:
    """Register ranking models into the MLflow Model Registry."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        client: Any | None = None,
    ) -> None:
        self.settings = settings or get_app_settings()
        self.client = client or MlflowClient(
            tracking_uri=self.settings.services.mlflow.tracking_uri
        )

    def register(self, model_uri: str, name: str, tags: dict[str, str]) -> dict[str, Any]:
        try:
            self.client.create_registered_model(name)
        except Exception:
            pass
        version = self.client.create_model_version(name=name, source=model_uri, run_id="")
        for key, value in tags.items():
            self.client.set_model_version_tag(name, version.version, key, value)
        return {"name": name, "version": version.version}


def _flatten_mapping(values: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key, value in values.items():
        compound_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flattened.update(_flatten_mapping(value, prefix=compound_key))
            continue
        flattened[compound_key] = value
    return flattened
