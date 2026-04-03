from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.ranking.model import RankingModel
from recsys_prd.ranking.training import load_ranking_model


@dataclass(frozen=True)
class RegisteredRankingModel:
    registration_path: Path
    model_path: Path
    dataset_path: Path
    model_name: str
    model_version: str
    source_run_id: str
    stage: str
    model: RankingModel


def load_registered_ranking_model(
    registration_path: Path,
) -> RegisteredRankingModel | None:
    """Load one registered ranking model bundle for serving or evaluation."""
    registration = json.loads(registration_path.read_text(encoding="utf-8"))
    model_path = Path(registration["artifacts"]["model_path"])
    if not model_path.exists():
        return None
    return RegisteredRankingModel(
        registration_path=registration_path,
        model_path=model_path,
        dataset_path=Path(registration["dataset"]["path"]),
        model_name=registration["model_name"],
        model_version=registration["model_version"],
        source_run_id=registration["source_run_id"],
        stage=registration["stage"],
        model=load_ranking_model(model_path),
    )


def load_latest_registered_ranking_model(
    *,
    models_root: Path | None = None,
    settings: AppSettings | None = None,
) -> RegisteredRankingModel | None:
    """Load the latest registered ranking model bundle for backend-serving callers."""
    settings = settings or get_app_settings()
    models_root = models_root or settings.paths.models_root
    latest_candidates = sorted((models_root / "registry").glob("*/latest_candidate.json"))
    if not latest_candidates:
        return None
    return load_registered_ranking_model(latest_candidates[-1])
