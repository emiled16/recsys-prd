from __future__ import annotations

import base64
import hashlib
import math
from dataclasses import asdict, dataclass
from dataclasses import field as dataclass_field
from typing import Any

NUMERIC_FEATURE_FIELDS = (
    "candidate_rank",
    "candidate_score",
    "customer_age",
    "customer_has_fn_flag",
    "customer_has_active_flag",
    "article_has_detail_desc",
    "article_has_image",
    "customer_purchase_count_30d",
    "customer_purchase_count_all_time",
    "customer_days_since_last_purchase",
    "customer_distinct_articles_purchased_30d",
    "customer_avg_purchase_price_30d",
    "article_purchase_count_7d",
    "article_purchase_count_30d",
    "article_unique_customers_30d",
    "article_avg_article_price_30d",
    "article_days_since_last_article_purchase",
    "customer_article_historical_purchase_count",
    "customer_article_days_since_last_purchase",
    "customer_article_has_purchased_before",
    "customer_article_last_purchase_price",
)

CATEGORICAL_FEATURE_FIELDS = (
    "candidate_source",
    "customer_club_member_status",
    "customer_fashion_news_frequency",
    "article_product_type_name",
    "article_product_group_name",
    "article_colour_group_name",
    "article_department_name",
    "article_index_group_name",
)


@dataclass(frozen=True)
class NumericFieldStats:
    mean: float
    std: float


@dataclass(frozen=True)
class RankingFeatureSchema:
    numeric_fields: tuple[str, ...]
    categorical_fields: tuple[str, ...]
    categorical_hash_buckets: int
    numeric_stats: dict[str, NumericFieldStats]
    feature_dimension: int


@dataclass(frozen=True)
class RankingTrainingConfig:
    epochs: int = 120
    learning_rate: float = 0.15
    l2_regularization: float = 0.001
    categorical_hash_buckets: int = 128


@dataclass(frozen=True)
class RankingModel:
    model_name: str
    model_version: str
    feature_schema: RankingFeatureSchema
    training_config: RankingTrainingConfig
    weights: list[float] | None = None
    model_family: str = "logistic_baseline"
    backend_payload: str | None = None
    _predictor: Any | None = dataclass_field(default=None, repr=False, compare=False)

    def predict_probability(self, row: dict[str, str]) -> float:
        """Predict purchase probability for a ranking row."""
        sparse_features = vectorize_ranking_row(row, self.feature_schema)
        if self.model_family == "xgboost_ranker":
            predictor = self._predictor or _load_xgboost_predictor(self.backend_payload)
            if self._predictor is None:
                object.__setattr__(self, "_predictor", predictor)
            dense_features = _dense_feature_vector(sparse_features, self.feature_schema)
            raw_score = float(predictor.predict([dense_features])[0])
            bounded_score = max(min(raw_score, 35.0), -35.0)
            return 1.0 / (1.0 + math.exp(-bounded_score))
        if self.weights is None:
            raise RuntimeError("Linear ranking model is missing weights.")
        return _predict_probability(self.weights, sparse_features)

    def to_dict(self) -> dict[str, object]:
        """Serialize the model artifact into JSON-compatible primitives."""
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "model_family": self.model_family,
            "feature_schema": {
                "numeric_fields": list(self.feature_schema.numeric_fields),
                "categorical_fields": list(self.feature_schema.categorical_fields),
                "categorical_hash_buckets": self.feature_schema.categorical_hash_buckets,
                "numeric_stats": {
                    field: asdict(stats)
                    for field, stats in self.feature_schema.numeric_stats.items()
                },
                "feature_dimension": self.feature_schema.feature_dimension,
            },
            "training_config": asdict(self.training_config),
            "weights": self.weights,
            "backend_payload": self.backend_payload,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> RankingModel:
        """Restore a ranking model from a JSON-compatible payload."""
        schema_payload = payload["feature_schema"]
        return cls(
            model_name=str(payload["model_name"]),
            model_version=str(payload["model_version"]),
            feature_schema=RankingFeatureSchema(
                numeric_fields=tuple(schema_payload["numeric_fields"]),
                categorical_fields=tuple(schema_payload["categorical_fields"]),
                categorical_hash_buckets=int(schema_payload["categorical_hash_buckets"]),
                numeric_stats={
                    field: NumericFieldStats(
                        mean=float(stats["mean"]),
                        std=float(stats["std"]),
                    )
                    for field, stats in schema_payload["numeric_stats"].items()
                },
                feature_dimension=int(schema_payload["feature_dimension"]),
            ),
            training_config=RankingTrainingConfig(
                epochs=int(payload["training_config"]["epochs"]),
                learning_rate=float(payload["training_config"]["learning_rate"]),
                l2_regularization=float(payload["training_config"]["l2_regularization"]),
                categorical_hash_buckets=int(payload["training_config"]["categorical_hash_buckets"]),
            ),
            weights=(
                [float(value) for value in payload["weights"]]
                if payload.get("weights") is not None
                else None
            ),
            model_family=str(payload.get("model_family", "logistic_baseline")),
            backend_payload=(
                str(payload["backend_payload"])
                if payload.get("backend_payload") is not None
                else None
            ),
        )


def train_ranking_model(
    rows: list[dict[str, str]],
    *,
    config: RankingTrainingConfig | None = None,
    model_name: str = "ranking_logistic_baseline",
    model_version: str = "v1",
) -> tuple[RankingModel, dict[str, float]]:
    """Train a deterministic linear ranking baseline from ranking rows."""
    config = config or RankingTrainingConfig()
    feature_schema = build_feature_schema(
        rows,
        categorical_hash_buckets=config.categorical_hash_buckets,
    )
    training_examples = [
        (vectorize_ranking_row(row, feature_schema), int(row["label_purchase"]))
        for row in rows
    ]
    weights = [0.0] * feature_schema.feature_dimension

    for _ in range(config.epochs):
        for features, label in training_examples:
            probability = _predict_probability(weights, features)
            error = probability - label
            for index, value in features.items():
                regularization = config.l2_regularization * weights[index] if index != 0 else 0.0
                weights[index] -= config.learning_rate * ((error * value) + regularization)

    model = RankingModel(
        model_name=model_name,
        model_version=model_version,
        feature_schema=feature_schema,
        training_config=config,
        weights=weights,
    )
    metrics = evaluate_ranking_model(model, rows)
    return model, metrics


def evaluate_ranking_model(model: RankingModel, rows: list[dict[str, str]]) -> dict[str, float]:
    """Evaluate the trained baseline on the provided ranking rows."""
    if not rows:
        return {
            "row_count": 0.0,
            "positive_row_count": 0.0,
            "negative_row_count": 0.0,
            "log_loss": 0.0,
            "accuracy": 0.0,
            "mean_positive_score": 0.0,
            "mean_negative_score": 0.0,
            "pairwise_accuracy": 0.0,
        }

    losses: list[float] = []
    predictions: list[tuple[dict[str, str], float]] = []
    correct = 0
    positive_scores: list[float] = []
    negative_scores: list[float] = []

    for row in rows:
        probability = model.predict_probability(row)
        label = int(row["label_purchase"])
        clipped_probability = min(max(probability, 1e-9), 1 - 1e-9)
        losses.append(
            -(
                label * math.log(clipped_probability)
                + (1 - label) * math.log(1 - clipped_probability)
            )
        )
        correct += int((probability >= 0.5) == bool(label))
        predictions.append((row, probability))
        if label == 1:
            positive_scores.append(probability)
        else:
            negative_scores.append(probability)

    pairwise_accuracy = _pairwise_accuracy(predictions)
    return {
        "row_count": float(len(rows)),
        "positive_row_count": float(len(positive_scores)),
        "negative_row_count": float(len(negative_scores)),
        "log_loss": round(sum(losses) / len(losses), 6),
        "accuracy": round(correct / len(rows), 6),
        "mean_positive_score": round(sum(positive_scores) / len(positive_scores), 6),
        "mean_negative_score": round(sum(negative_scores) / len(negative_scores), 6)
        if negative_scores
        else 0.0,
        "pairwise_accuracy": round(pairwise_accuracy, 6),
    }


def build_feature_schema(
    rows: list[dict[str, str]],
    *,
    categorical_hash_buckets: int,
) -> RankingFeatureSchema:
    """Build the deterministic feature schema used by the ranking baseline."""
    numeric_stats: dict[str, NumericFieldStats] = {}
    for field_name in NUMERIC_FEATURE_FIELDS:
        observed_values = [
            _parse_float(row.get(field_name, ""))
            for row in rows
            if row.get(field_name, "") != ""
        ]
        if not observed_values:
            numeric_stats[field_name] = NumericFieldStats(mean=0.0, std=1.0)
            continue
        mean = sum(observed_values) / len(observed_values)
        variance = sum((value - mean) ** 2 for value in observed_values) / len(observed_values)
        std = math.sqrt(variance) or 1.0
        numeric_stats[field_name] = NumericFieldStats(mean=mean, std=std)

    feature_dimension = 1 + (2 * len(NUMERIC_FEATURE_FIELDS)) + categorical_hash_buckets
    return RankingFeatureSchema(
        numeric_fields=NUMERIC_FEATURE_FIELDS,
        categorical_fields=CATEGORICAL_FEATURE_FIELDS,
        categorical_hash_buckets=categorical_hash_buckets,
        numeric_stats=numeric_stats,
        feature_dimension=feature_dimension,
    )


def vectorize_ranking_row(
    row: dict[str, str],
    feature_schema: RankingFeatureSchema,
) -> dict[int, float]:
    """Convert one ranking row into a sparse feature vector."""
    features: dict[int, float] = {0: 1.0}
    numeric_count = len(feature_schema.numeric_fields)

    for offset, field_name in enumerate(feature_schema.numeric_fields, start=1):
        missing_index = offset + numeric_count
        raw_value = row.get(field_name, "")
        if raw_value == "":
            features[missing_index] = 1.0
            continue
        stats = feature_schema.numeric_stats[field_name]
        standardized_value = (_parse_float(raw_value) - stats.mean) / stats.std
        if standardized_value != 0.0:
            features[offset] = standardized_value

    categorical_start = 1 + (2 * numeric_count)
    for field_name in feature_schema.categorical_fields:
        value = row.get(field_name, "").strip().lower()
        if not value:
            continue
        bucket = _stable_bucket(f"{field_name}={value}", feature_schema.categorical_hash_buckets)
        index = categorical_start + bucket
        features[index] = features.get(index, 0.0) + 1.0

    return features


def _parse_float(value: str) -> float:
    return float(value) if value else 0.0


def _predict_probability(weights: list[float], features: dict[int, float]) -> float:
    linear_score = sum(weights[index] * value for index, value in features.items())
    bounded_score = max(min(linear_score, 35.0), -35.0)
    return 1.0 / (1.0 + math.exp(-bounded_score))


def _dense_feature_vector(
    sparse_features: dict[int, float],
    feature_schema: RankingFeatureSchema,
) -> list[float]:
    vector = [0.0] * feature_schema.feature_dimension
    for index, value in sparse_features.items():
        vector[index] = value
    return vector


def _load_xgboost_predictor(encoded_model: str | None):
    if not encoded_model:
        raise RuntimeError("XGBoost ranking model is missing a serialized backend.")
    try:
        import xgboost
    except ImportError as exc:  # pragma: no cover - depends on runtime installation.
        raise RuntimeError("xgboost is required to load the XGBoost ranker.") from exc

    booster = xgboost.Booster()
    booster.load_model(bytearray(base64.b64decode(encoded_model.encode("ascii"))))
    return _BoosterPredictor(booster)


@dataclass(frozen=True)
class _BoosterPredictor:
    booster: Any

    def predict(self, feature_matrix: list[list[float]]) -> list[float]:
        try:
            import xgboost
        except ImportError as exc:  # pragma: no cover - depends on runtime installation.
            raise RuntimeError("xgboost is required to score the XGBoost ranker.") from exc
        return [float(value) for value in self.booster.predict(xgboost.DMatrix(feature_matrix))]


def _stable_bucket(value: str, bucket_count: int) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:16], 16) % bucket_count


def _pairwise_accuracy(predictions: list[tuple[dict[str, str], float]]) -> float:
    grouped_predictions: dict[str, dict[str, list[float]]] = {}
    for row, probability in predictions:
        group = grouped_predictions.setdefault(
            row["label_event_id"],
            {"positive": [], "negative": []},
        )
        if row["label_purchase"] == "1":
            group["positive"].append(probability)
        else:
            group["negative"].append(probability)

    comparable_groups = 0
    successful_groups = 0
    for group in grouped_predictions.values():
        if not group["positive"] or not group["negative"]:
            continue
        comparable_groups += 1
        if min(group["positive"]) > max(group["negative"]):
            successful_groups += 1

    if comparable_groups == 0:
        return 0.0
    return successful_groups / comparable_groups
