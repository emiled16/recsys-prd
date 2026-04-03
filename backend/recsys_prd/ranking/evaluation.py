from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.io.json_ops import write_json
from recsys_prd.io.tabular_ops import read_tabular_rows
from recsys_prd.ranking.model import evaluate_ranking_model
from recsys_prd.ranking.serving import load_registered_ranking_model


def evaluate_registered_ranking_model(
    *,
    models_root: Path | None = None,
    registration_path: Path | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path | str | dict[str, float]]:
    """Evaluate the latest registered ranking model against its tracked dataset."""
    settings = settings or get_app_settings()
    models_root = models_root or settings.paths.models_root
    registration_path = registration_path or _latest_registration_path(models_root)
    registration = json.loads(registration_path.read_text(encoding="utf-8"))
    bundle = load_registered_ranking_model(registration_path)
    if bundle is None:
        raise FileNotFoundError("The registered ranking model artifact could not be loaded.")

    rows = read_tabular_rows(bundle.dataset_path)
    metrics = evaluate_ranking_model(bundle.model, rows)
    evaluation_path = (
        models_root
        / "evaluations"
        / registration["model_name"]
        / registration["source_run_id"]
        / "evaluation.json"
    )
    payload = {
        "evaluated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model_name": registration["model_name"],
        "model_version": registration["model_version"],
        "source_run_id": registration["source_run_id"],
        "registration_path": str(registration_path),
        "registration_stage": registration["stage"],
        "mlflow_model": registration.get("mlflow_model", {}),
        "dataset": registration["dataset"],
        "metrics": metrics,
    }
    write_json(evaluation_path, payload)
    return {
        "evaluation": evaluation_path,
        "registration": registration_path,
        "metrics": metrics,
    }


def _latest_registration_path(models_root: Path) -> Path:
    registry_root = models_root / "registry"
    latest_candidates = sorted(registry_root.glob("*/latest_candidate.json"))
    if not latest_candidates:
        raise FileNotFoundError("No registered ranking model was found under the model registry.")
    return latest_candidates[-1]
