from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.events.io import read_jsonl, write_jsonl
from recsys_prd.io.json_ops import write_json
from recsys_prd.ranking.training import train_local_ranking_model
from recsys_prd.schemas.artifacts import ModelRegistrationRecord


def register_candidate_ranking_model(
    *,
    models_root: Path | None = None,
    normalized_root: Path | None = None,
    indexes_root: Path | None = None,
    manifest_path: Path | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path]:
    """Register the latest trained ranking model as a candidate model version."""
    settings = settings or get_app_settings()
    models_root = models_root or settings.paths.models_root
    normalized_root = normalized_root or settings.paths.normalized_root
    indexes_root = indexes_root or settings.paths.indexes_root
    manifest_path = manifest_path or _resolve_training_manifest(
        models_root=models_root,
        normalized_root=normalized_root,
        indexes_root=indexes_root,
        settings=settings,
    )
    training_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    registry_dir = models_root / "registry" / training_manifest["model_name"]
    registration_path = registry_dir / training_manifest["run_id"] / "registration.json"
    latest_candidate_path = registry_dir / "latest_candidate.json"
    registry_log_path = registry_dir / "registered_models.jsonl"

    registration_payload = ModelRegistrationRecord(
        registration_id=f"{training_manifest['model_name']}::{training_manifest['run_id']}",
        registered_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        model_name=training_manifest["model_name"],
        model_version=training_manifest["model_version"],
        stage="candidate",
        source_run_id=training_manifest["run_id"],
        training_manifest_path=str(manifest_path),
        dataset=training_manifest["dataset"],
        training_config=training_manifest["training_config"],
        metrics=training_manifest["metrics"],
        artifacts=training_manifest["artifacts"],
        lineage={
            "training_dataset_path": training_manifest["dataset"]["path"],
            "training_manifest_path": str(manifest_path),
            "model_artifact_path": training_manifest["artifacts"]["model_path"],
            "metrics_artifact_path": training_manifest["artifacts"]["metrics_path"],
        },
        registration_path=str(registration_path),
    ).model_dump()

    write_json(registration_path, registration_payload)
    write_json(latest_candidate_path, registration_payload)
    _append_registry_log(registry_log_path, registration_payload)

    return {
        "registration": registration_path,
        "latest_candidate": latest_candidate_path,
        "registry_log": registry_log_path,
    }


def _resolve_training_manifest(
    *,
    models_root: Path,
    normalized_root: Path,
    indexes_root: Path,
    settings: AppSettings | None = None,
) -> Path:
    run_log_path = models_root / "training_runs" / "ranking_logistic_baseline_runs.jsonl"
    if not run_log_path.exists():
        outputs = train_local_ranking_model(
            normalized_root=normalized_root,
            indexes_root=indexes_root,
            models_root=models_root,
            settings=settings,
        )
        return outputs["manifest"]

    run_rows = read_jsonl(run_log_path)
    latest_run = run_rows[-1]
    return Path(latest_run["manifest_path"])


def _append_registry_log(path: Path, registration_payload: dict[str, object]) -> None:
    existing_rows = read_jsonl(path) if path.exists() else []
    existing_rows.append(
        {
            "registration_id": registration_payload["registration_id"],
            "registered_at_utc": registration_payload["registered_at_utc"],
            "model_name": registration_payload["model_name"],
            "model_version": registration_payload["model_version"],
            "stage": registration_payload["stage"],
            "source_run_id": registration_payload["source_run_id"],
            "metrics": registration_payload["metrics"],
            "registration_path": registration_payload["registration_path"],
        }
    )
    write_jsonl(path, existing_rows)
