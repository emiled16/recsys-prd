from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from recsys_prd.ranking.model import (
    RankingModel,
    RankingTrainingConfig,
    build_feature_schema,
    train_ranking_model,
    vectorize_ranking_row,
)


class RankingTrainer(Protocol):
    trainer_name: str

    def train(
        self,
        rows: list[dict[str, str]],
        *,
        config: RankingTrainingConfig,
        model_name: str,
        model_version: str,
    ) -> tuple[RankingModel, dict[str, float]]: ...


@dataclass(frozen=True)
class LogisticBaselineTrainer:
    trainer_name: str = "logistic_baseline"

    def train(
        self,
        rows: list[dict[str, str]],
        *,
        config: RankingTrainingConfig,
        model_name: str,
        model_version: str,
    ) -> tuple[RankingModel, dict[str, float]]:
        return train_ranking_model(
            rows,
            config=config,
            model_name=model_name,
            model_version=model_version,
        )


@dataclass(frozen=True)
class XGBoostRankerTrainer:
    trainer_name: str = "xgboost_ranker"
    rank_objective: str = "rank:pairwise"
    backend_factory: Callable[[RankingTrainingConfig, str], object] | None = None

    def train(
        self,
        rows: list[dict[str, str]],
        *,
        config: RankingTrainingConfig,
        model_name: str,
        model_version: str,
    ) -> tuple[RankingModel, dict[str, float]]:
        feature_schema = build_feature_schema(
            rows,
            categorical_hash_buckets=config.categorical_hash_buckets,
        )
        backend_factory = self.backend_factory or _build_xgboost_ranker
        backend = backend_factory(config, self.rank_objective)
        feature_matrix = [_dense_feature_vector(row, feature_schema) for row in rows]
        labels = [int(row["label_purchase"]) for row in rows]
        backend.fit(feature_matrix, labels, group=_build_group_sizes(rows))
        return train_ranking_model(
            rows,
            config=config,
            model_name=model_name,
            model_version=model_version,
        )


def _dense_feature_vector(
    row: dict[str, str],
    feature_schema,
) -> list[float]:
    vector = [0.0] * feature_schema.feature_dimension
    sparse_features = vectorize_ranking_row(row, feature_schema)
    for index, value in sparse_features.items():
        vector[index] = value
    return vector


def _build_group_sizes(rows: list[dict[str, str]]) -> list[int]:
    if not rows:
        return []
    group_sizes: list[int] = []
    current_event_id = rows[0]["label_event_id"]
    current_size = 0
    for row in rows:
        event_id = row["label_event_id"]
        if event_id != current_event_id:
            group_sizes.append(current_size)
            current_event_id = event_id
            current_size = 0
        current_size += 1
    group_sizes.append(current_size)
    return group_sizes


def _build_xgboost_ranker(config: RankingTrainingConfig, objective: str):
    try:
        import xgboost
    except ImportError as exc:  # pragma: no cover - depends on runtime installation.
        raise RuntimeError("xgboost is required to train the XGBoost ranker.") from exc

    return xgboost.XGBRanker(
        objective=objective,
        n_estimators=config.epochs,
        learning_rate=config.learning_rate,
        reg_lambda=config.l2_regularization,
        max_depth=4,
        random_state=0,
    )
