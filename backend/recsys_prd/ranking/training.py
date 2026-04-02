from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.events.io import read_jsonl, write_jsonl
from recsys_prd.io.json_ops import write_json
from recsys_prd.io.tabular_ops import read_tabular_rows
from recsys_prd.ranking.dataset import build_ranking_dataset
from recsys_prd.ranking.model import RankingModel, RankingTrainingConfig, train_ranking_model


def train_local_ranking_model(
    *,
    normalized_root: Path | None = None,
    indexes_root: Path | None = None,
    models_root: Path | None = None,
    config: RankingTrainingConfig | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path]:
    """Train the local ranking baseline and write tracked artifacts."""
    settings = settings or get_app_settings()
    normalized_root = normalized_root or settings.paths.normalized_root
    indexes_root = indexes_root or settings.paths.indexes_root
    models_root = models_root or settings.paths.models_root
    training_sets_root = models_root / "training_sets"
    dataset_path = training_sets_root / "ranking_dataset" / "ranking_dataset.parquet"
    if not dataset_path.exists():
        dataset_path = build_ranking_dataset(
            normalized_root=normalized_root,
            indexes_root=indexes_root,
            models_root=training_sets_root,
            settings=settings,
        )

    rows = read_tabular_rows(dataset_path)
    config = config or RankingTrainingConfig()
    model, metrics = train_ranking_model(rows, config=config)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = models_root / "artifacts" / model.model_name / run_id
    model_path = run_dir / "model.json"
    metrics_path = run_dir / "metrics.json"
    manifest_path = run_dir / "manifest.json"
    run_log_path = models_root / "training_runs" / f"{model.model_name}_runs.jsonl"

    write_json(model_path, model.to_dict())
    write_json(metrics_path, metrics)

    manifest_payload = {
        "run_id": run_id,
        "trained_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model_name": model.model_name,
        "model_version": model.model_version,
        "dataset": {
            "path": str(dataset_path),
            "row_count": len(rows),
            "positive_row_count": sum(int(row["label_purchase"]) for row in rows),
            "negative_row_count": sum(1 - int(row["label_purchase"]) for row in rows),
        },
        "training_config": {
            "epochs": config.epochs,
            "learning_rate": config.learning_rate,
            "l2_regularization": config.l2_regularization,
            "categorical_hash_buckets": config.categorical_hash_buckets,
        },
        "metrics": metrics,
        "artifacts": {
            "model_path": str(model_path),
            "metrics_path": str(metrics_path),
            "manifest_path": str(manifest_path),
        },
    }
    write_json(manifest_path, manifest_payload)
    _append_run_log(run_log_path, manifest_payload)

    return {
        "model": model_path,
        "metrics": metrics_path,
        "manifest": manifest_path,
        "run_log": run_log_path,
    }


def load_ranking_model(path: Path) -> RankingModel:
    """Load a trained ranking model artifact from disk."""
    return RankingModel.from_dict(json.loads(path.read_text(encoding="utf-8")))


def _append_run_log(path: Path, manifest_payload: dict[str, object]) -> None:
    existing_rows = read_jsonl(path) if path.exists() else []
    existing_rows.append(
        {
            "run_id": manifest_payload["run_id"],
            "trained_at_utc": manifest_payload["trained_at_utc"],
            "model_name": manifest_payload["model_name"],
            "model_version": manifest_payload["model_version"],
            "dataset_path": manifest_payload["dataset"]["path"],
            "row_count": manifest_payload["dataset"]["row_count"],
            "positive_row_count": manifest_payload["dataset"]["positive_row_count"],
            "negative_row_count": manifest_payload["dataset"]["negative_row_count"],
            "metrics": manifest_payload["metrics"],
            "manifest_path": manifest_payload["artifacts"]["manifest_path"],
        }
    )
    write_jsonl(path, existing_rows)
