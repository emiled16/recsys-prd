from __future__ import annotations

import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.features.training_dataset import load_training_inputs
from recsys_prd.io.json_ops import write_json
from recsys_prd.retrieval.candidate_retrieval import CandidateRetriever
from recsys_prd.retrieval.contracts import RetrievalRequest
from recsys_prd.schemas.artifacts import (
    PromotionReadinessReport,
    RetrievalEvaluationReport,
    RetrievalSliceMetric,
)


class OfflineRetrievalEvaluator:
    """Evaluate retrieval quality from candidate generation outputs."""

    def __init__(
        self,
        *,
        retriever: CandidateRetriever | None = None,
        settings: AppSettings | None = None,
    ) -> None:
        self.settings = settings or get_app_settings()
        self.retriever = retriever or CandidateRetriever(settings=self.settings)

    def evaluate(
        self,
        *,
        normalized_root: Path | None = None,
        report_path: Path | None = None,
        indexes_root: Path | None = None,
        embeddings_root: Path | None = None,
        k: int = 10,
        readiness_thresholds: dict[str, float] | None = None,
    ) -> dict[str, Path | dict[str, float]]:
        normalized_root = normalized_root or self.settings.paths.normalized_root
        indexes_root = indexes_root or self.settings.paths.indexes_root
        embeddings_root = embeddings_root or self.settings.paths.embeddings_root
        _, products, image_presence, ordered_transactions = load_training_inputs(normalized_root)
        customer_history: dict[str, list[dict[str, str]]] = {}
        ranks: list[int] = []
        samples: list[dict[str, object]] = []

        for transaction in ordered_transactions:
            customer_id = transaction["customer_id"]
            target_article_id = transaction["article_id"]
            product = products.get(target_article_id, {})
            query_text = _build_retrieval_query_text(product)
            seed_article_ids = _recent_seed_article_ids(
                customer_history,
                customer_id=customer_id,
                limit=3,
            )
            result = self.retriever.retrieve(
                RetrievalRequest(
                    query_text=query_text,
                    seed_article_ids=seed_article_ids,
                    customer_id=customer_id,
                    limit=k,
                    index_name="fused",
                )
            )
            rank = _find_rank(result.candidates, target_article_id)
            if rank is not None:
                ranks.append(rank)
            samples.append(
                {
                    "rank": rank,
                    "target_has_image": bool(image_presence.get(target_article_id, False)),
                    "query_length_bucket": _query_length_bucket(query_text),
                    "department_name": product.get("department_name", "") or "unknown",
                }
            )
            customer_history.setdefault(customer_id, []).append(transaction)

        metrics = _retrieval_metrics(ranks=ranks, query_count=len(ordered_transactions), k=k)
        slice_metrics = _slice_metrics(samples=samples, k=k)
        embedding_manifest = _load_manifest(embeddings_root / "manifest.json")
        index_manifest = _load_manifest(indexes_root / "manifest.json")
        freshness = _freshness_summary(
            index_manifest=index_manifest,
            embedding_manifest=embedding_manifest,
        )
        readiness = _promotion_readiness(
            metrics=metrics,
            freshness=freshness,
            thresholds=readiness_thresholds,
        )
        report_path = report_path or (
            self.settings.paths.reports_root / "retrieval" / "offline_retrieval_evaluation.json"
        )
        report = RetrievalEvaluationReport(
            evaluated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            query_count=len(ordered_transactions),
            k=k,
            index_name="fused",
            index_manifest_path=str(indexes_root / "manifest.json") if index_manifest else None,
            embedding_manifest_path=str(embeddings_root / "manifest.json")
            if embedding_manifest
            else None,
            metrics=metrics,
            slices=slice_metrics,
            freshness=freshness,
            readiness=readiness,
        )
        write_json(report_path, report.model_dump())
        return {
            "report": report_path,
            "metrics": metrics,
            "slices": {name: metric.model_dump() for name, metric in slice_metrics.items()},
            "freshness": freshness,
            "readiness": readiness.model_dump(),
        }


def _build_retrieval_query_text(product: dict[str, str]) -> str:
    query_parts = [
        product.get("prod_name", ""),
        product.get("product_type_name", ""),
        product.get("product_group_name", ""),
        product.get("colour_group_name", ""),
        product.get("department_name", ""),
        product.get("section_name", ""),
        product.get("detail_desc", ""),
    ]
    return " ".join(part.strip() for part in query_parts if part.strip())


def _find_rank(candidates, target_article_id: str) -> int | None:
    for index, candidate in enumerate(candidates, start=1):
        if candidate.article_id == target_article_id:
            return index
    return None


def _recent_seed_article_ids(
    customer_history: dict[str, list[dict[str, str]]],
    *,
    customer_id: str,
    limit: int,
) -> tuple[str, ...]:
    seed_article_ids: list[str] = []
    seen_article_ids: set[str] = set()
    for transaction in reversed(customer_history.get(customer_id, [])):
        article_id = transaction["article_id"]
        if article_id in seen_article_ids:
            continue
        seed_article_ids.append(article_id)
        seen_article_ids.add(article_id)
        if len(seed_article_ids) >= limit:
            break
    return tuple(seed_article_ids)


def _retrieval_metrics(*, ranks: list[int], query_count: int, k: int) -> dict[str, float]:
    if query_count == 0:
        return {"recall_at_k": 0.0, "mrr": 0.0, "ndcg_at_k": 0.0}
    hits = [rank for rank in ranks if rank <= k]
    recall_at_k = len(hits) / query_count
    reciprocal_ranks = [1 / rank for rank in hits]
    ndcg_scores = [1 / math.log2(rank + 1) for rank in hits]
    return {
        "recall_at_k": round(recall_at_k, 6),
        "mrr": round(sum(reciprocal_ranks) / query_count, 6),
        "ndcg_at_k": round(sum(ndcg_scores) / query_count, 6),
    }


def _slice_metrics(*, samples: list[dict[str, object]], k: int) -> dict[str, RetrievalSliceMetric]:
    grouped_samples: dict[str, list[dict[str, object]]] = defaultdict(list)
    for sample in samples:
        grouped_samples[f"target_has_image={sample['target_has_image']}"].append(sample)
        grouped_samples[f"query_length_bucket={sample['query_length_bucket']}"].append(sample)
        grouped_samples[f"department_name={sample['department_name']}"].append(sample)

    slice_metrics: dict[str, RetrievalSliceMetric] = {}
    for slice_name, slice_samples in grouped_samples.items():
        slice_ranks = [
            int(sample["rank"]) for sample in slice_samples if sample["rank"] is not None
        ]
        slice_metrics[slice_name] = RetrievalSliceMetric(
            slice_name=slice_name,
            query_count=len(slice_samples),
            metrics=_retrieval_metrics(
                ranks=slice_ranks,
                query_count=len(slice_samples),
                k=k,
            ),
        )
    return slice_metrics


def _query_length_bucket(query_text: str) -> str:
    word_count = len([token for token in query_text.split() if token])
    if word_count <= 4:
        return "short"
    if word_count <= 10:
        return "medium"
    return "long"


def _freshness_summary(
    *,
    index_manifest: dict[str, object],
    embedding_manifest: dict[str, object],
) -> dict[str, object]:
    summary: dict[str, object] = {
        "index_manifest_available": bool(index_manifest),
        "embedding_manifest_available": bool(embedding_manifest),
    }
    now = datetime.now(timezone.utc)
    index_built_at = _parse_timestamp(index_manifest.get("built_at_utc", ""))
    embedding_generated_at = _parse_timestamp(embedding_manifest.get("generated_at_utc", ""))
    if index_built_at is not None:
        summary["index_age_seconds"] = int((now - index_built_at).total_seconds())
    if embedding_generated_at is not None:
        summary["embedding_age_seconds"] = int((now - embedding_generated_at).total_seconds())
    if index_manifest:
        summary["index_manifest_path"] = index_manifest.get("path", "")
        summary["source_embedding_digest"] = index_manifest.get("source_embedding_digest", "")
    if embedding_manifest:
        summary["embedding_manifest_path"] = embedding_manifest.get("path", "")
        summary["source_digest"] = embedding_manifest.get("source", {}).get("digest", "")
    return summary


def _promotion_readiness(
    *,
    metrics: dict[str, float],
    freshness: dict[str, object],
    thresholds: dict[str, float] | None,
) -> PromotionReadinessReport:
    required_metrics = thresholds or {
        "recall_at_k": 0.0,
        "mrr": 0.0,
        "ndcg_at_k": 0.0,
    }
    blockers: list[str] = []
    actual_metrics = {key: float(metrics.get(key, 0.0)) for key in required_metrics}
    for key, minimum_value in required_metrics.items():
        if actual_metrics[key] < minimum_value:
            blockers.append(f"metric_below_threshold:{key}")
    if not freshness.get("index_manifest_available", False):
        blockers.append("index_manifest_missing")
    if not freshness.get("embedding_manifest_available", False):
        blockers.append("embedding_manifest_missing")
    return PromotionReadinessReport(
        ready_for_promotion=not blockers,
        required_metrics=required_metrics,
        actual_metrics=actual_metrics,
        freshness=freshness,
        blockers=blockers,
    )


def _load_manifest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
