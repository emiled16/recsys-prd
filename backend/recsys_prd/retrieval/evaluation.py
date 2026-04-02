from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.features.training_dataset import load_training_inputs
from recsys_prd.io.json_ops import write_json
from recsys_prd.retrieval.candidate_retrieval import CandidateRetriever
from recsys_prd.retrieval.contracts import RetrievalRequest


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
        k: int = 10,
    ) -> dict[str, Path | dict[str, float]]:
        normalized_root = normalized_root or self.settings.paths.normalized_root
        _, products, _, ordered_transactions = load_training_inputs(normalized_root)
        customer_history: dict[str, list[dict[str, str]]] = {}
        ranks: list[int] = []

        for transaction in ordered_transactions:
            customer_id = transaction["customer_id"]
            target_article_id = transaction["article_id"]
            seed_article_ids = _recent_seed_article_ids(
                customer_history,
                customer_id=customer_id,
                limit=3,
            )
            result = self.retriever.retrieve(
                RetrievalRequest(
                    query_text=_build_retrieval_query_text(products.get(target_article_id, {})),
                    seed_article_ids=seed_article_ids,
                    customer_id=customer_id,
                    limit=k,
                    index_name="fused",
                )
            )
            rank = _find_rank(result.candidates, target_article_id)
            if rank is not None:
                ranks.append(rank)
            customer_history.setdefault(customer_id, []).append(transaction)

        metrics = _retrieval_metrics(ranks=ranks, query_count=len(ordered_transactions), k=k)
        report_path = report_path or (
            self.settings.paths.reports_root / "retrieval" / "offline_retrieval_evaluation.json"
        )
        write_json(
            report_path,
            {
                "evaluated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "query_count": len(ordered_transactions),
                "k": k,
                "metrics": metrics,
            },
        )
        return {"report": report_path, "metrics": metrics}


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
