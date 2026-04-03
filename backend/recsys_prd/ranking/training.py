from __future__ import annotations

import json
from pathlib import Path

from pipelines.training.jobs import train_local_ranking_model

from recsys_prd.ranking.model import RankingModel

__all__ = ["load_ranking_model", "train_local_ranking_model"]


def load_ranking_model(path: Path) -> RankingModel:
    """Load a trained ranking model artifact from disk."""
    return RankingModel.from_dict(json.loads(path.read_text(encoding="utf-8")))
