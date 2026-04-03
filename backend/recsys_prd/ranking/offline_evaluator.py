from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.io.json_ops import write_json
from recsys_prd.io.tabular_ops import read_tabular_rows
from recsys_prd.ranking.model import evaluate_ranking_model
from recsys_prd.ranking.serving import load_registered_ranking_model


class OfflineRankingEvaluator:
    """Evaluate ranking quality over grouped ranking examples."""

    def __init__(self, *, settings: AppSettings | None = None) -> None:
        self.settings = settings or get_app_settings()

    def evaluate(
        self,
        *,
        models_root: Path | None = None,
        registration_path: Path | None = None,
        k: int = 5,
    ) -> dict[str, Path | dict[str, float]]:
        models_root = models_root or self.settings.paths.models_root
        registration_path = registration_path or _latest_registration_path(models_root)
        registration = json.loads(registration_path.read_text(encoding="utf-8"))
        bundle = load_registered_ranking_model(registration_path)
        if bundle is None:
            raise FileNotFoundError("The registered ranking model artifact could not be loaded.")
        rows = read_tabular_rows(bundle.dataset_path)

        ranked_groups = _rank_groups(rows, bundle.model)
        metrics = {
            **_topk_metrics(ranked_groups, k=k),
            "pairwise_quality": evaluate_ranking_model(bundle.model, rows)["pairwise_accuracy"],
        }
        report_path = (
            models_root
            / "evaluations"
            / registration["model_name"]
            / registration["source_run_id"]
            / f"ranking_quality_at_{k}.json"
        )
        write_json(
            report_path,
            {
                "evaluated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "k": k,
                "registration_path": str(registration_path),
                "metrics": metrics,
            },
        )
        return {"report": report_path, "metrics": metrics}


def _latest_registration_path(models_root: Path) -> Path:
    latest_candidates = sorted((models_root / "registry").glob("*/latest_candidate.json"))
    if not latest_candidates:
        raise FileNotFoundError("No registered ranking model was found under the model registry.")
    return latest_candidates[-1]


def _rank_groups(rows: list[dict[str, str]], model) -> list[list[tuple[dict[str, str], float]]]:
    grouped_rows: dict[str, list[tuple[dict[str, str], float]]] = {}
    for row in rows:
        grouped_rows.setdefault(row["label_event_id"], []).append(
            (row, model.predict_probability(row))
        )
    return [
        sorted(group_rows, key=lambda item: (-item[1], item[0]["candidate_article_id"]))
        for group_rows in grouped_rows.values()
    ]


def _topk_metrics(
    ranked_groups: list[list[tuple[dict[str, str], float]]],
    *,
    k: int,
) -> dict[str, float]:
    if not ranked_groups:
        return {
            "precision_at_k": 0.0,
            "map_at_k": 0.0,
            "ndcg_at_k": 0.0,
        }
    precision_scores: list[float] = []
    average_precisions: list[float] = []
    ndcg_scores: list[float] = []
    for group in ranked_groups:
        topk = group[:k]
        positive_rank = next(
            (
                index
                for index, (row, _) in enumerate(topk, start=1)
                if row["label_purchase"] == "1"
            ),
            None,
        )
        precision_scores.append((1 / k) if positive_rank is not None else 0.0)
        average_precisions.append((1 / positive_rank) if positive_rank is not None else 0.0)
        ndcg_scores.append(
            (1 / math.log2(positive_rank + 1)) if positive_rank is not None else 0.0
        )
    group_count = len(ranked_groups)
    return {
        "precision_at_k": round(sum(precision_scores) / group_count, 6),
        "map_at_k": round(sum(average_precisions) / group_count, 6),
        "ndcg_at_k": round(sum(ndcg_scores) / group_count, 6),
    }
