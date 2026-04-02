from __future__ import annotations

from pathlib import Path

from recsys_prd.features.training_dataset import (
    TRAINING_FEATURE_FIELDS,
    build_point_in_time_feature_row,
    load_training_inputs,
    recent_seed_article_ids,
    record_transaction_history,
)
from recsys_prd.io.json_ops import write_json
from recsys_prd.normalization.writer import write_dataset_bundle
from recsys_prd.paths import DATA_ROOT, NORMALIZED_ROOT
from recsys_prd.retrieval.candidate_retrieval import CandidateRetriever
from recsys_prd.retrieval.contracts import RetrievalRequest


RANKING_FIELDS = [
    "ranking_example_id",
    "label_event_id",
    "label_timestamp",
    "customer_id",
    "target_article_id",
    "candidate_article_id",
    "label_purchase",
    "candidate_source",
    "candidate_rank",
    "candidate_score",
    "retrieval_query_text",
    "retrieval_seed_article_ids",
    *TRAINING_FEATURE_FIELDS,
]


def build_ranking_dataset(
    *,
    normalized_root: Path = NORMALIZED_ROOT,
    indexes_root: Path = DATA_ROOT / "indexes",
    models_root: Path = DATA_ROOT / "models" / "training_sets",
    index_name: str = "fused",
    negative_sample_count: int = 4,
    max_seed_articles: int = 3,
) -> Path:
    """Build a ranking dataset with one positive row and retrieved negatives per label event."""
    customers, products, image_presence, ordered_transactions = load_training_inputs(normalized_root)
    retriever = CandidateRetriever(indexes_root=indexes_root)

    rows: list[dict[str, str]] = []
    customer_history = {}
    article_history = {}
    customer_article_history = {}
    positive_row_count = 0
    negative_row_count = 0

    for transaction in ordered_transactions:
        customer_id = transaction["customer_id"]
        target_article_id = transaction["article_id"]
        seed_article_ids = recent_seed_article_ids(
            customer_history,
            customer_id=customer_id,
            limit=max_seed_articles,
        )
        retrieval_query_text = _build_retrieval_query_text(products.get(target_article_id, {}))
        result = retriever.retrieve(
            RetrievalRequest(
                query_text=retrieval_query_text,
                seed_article_ids=seed_article_ids,
                limit=max(negative_sample_count * 3, negative_sample_count),
                index_name=index_name,
            )
        )

        rows.append(
            _build_ranking_row(
                transaction=transaction,
                candidate_article_id=target_article_id,
                target_article_id=target_article_id,
                candidate_source="observed_positive",
                candidate_rank=0,
                candidate_score="",
                retrieval_query_text=retrieval_query_text,
                retrieval_seed_article_ids=seed_article_ids,
                customers=customers,
                products=products,
                image_presence=image_presence,
                customer_history=customer_history,
                article_history=article_history,
                customer_article_history=customer_article_history,
            )
        )
        positive_row_count += 1

        negative_candidates = _select_negative_candidates(
            result=result,
            target_article_id=target_article_id,
            limit=negative_sample_count,
        )
        for negative_rank, candidate in enumerate(negative_candidates, start=1):
            rows.append(
                _build_ranking_row(
                    transaction=transaction,
                    candidate_article_id=candidate.article_id,
                    target_article_id=target_article_id,
                    candidate_source="retrieval_negative",
                    candidate_rank=negative_rank,
                    candidate_score=f"{candidate.score:.6f}",
                    retrieval_query_text=retrieval_query_text,
                    retrieval_seed_article_ids=seed_article_ids,
                    customers=customers,
                    products=products,
                    image_presence=image_presence,
                    customer_history=customer_history,
                    article_history=article_history,
                    customer_article_history=customer_article_history,
                )
            )
            negative_row_count += 1

        record_transaction_history(
            transaction=transaction,
            customer_history=customer_history,
            article_history=article_history,
            customer_article_history=customer_article_history,
        )

    dataset_dir = models_root / "ranking_dataset"
    dataset_path = write_dataset_bundle(
        dataset_dir=dataset_dir,
        dataset_filename="ranking_dataset.csv",
        fieldnames=RANKING_FIELDS,
        rows=rows,
        primary_key="ranking_example_id",
    )
    write_json(
        dataset_dir / "manifest.json",
        {
            "label_source": "transactions_normalized",
            "candidate_source": "candidate_retrieval",
            "index_name": index_name,
            "negative_sample_count": negative_sample_count,
            "max_seed_articles": max_seed_articles,
            "positive_row_count": positive_row_count,
            "negative_row_count": negative_row_count,
            "row_count": len(rows),
        },
    )
    return dataset_path


def _build_ranking_row(
    *,
    transaction: dict[str, str],
    candidate_article_id: str,
    target_article_id: str,
    candidate_source: str,
    candidate_rank: int,
    candidate_score: str,
    retrieval_query_text: str,
    retrieval_seed_article_ids: tuple[str, ...],
    customers: dict[str, dict[str, str]],
    products: dict[str, dict[str, str]],
    image_presence: dict[str, bool],
    customer_history: dict,
    article_history: dict,
    customer_article_history: dict,
) -> dict[str, str]:
    feature_row = build_point_in_time_feature_row(
        transaction=transaction,
        candidate_article_id=candidate_article_id,
        customers=customers,
        products=products,
        image_presence=image_presence,
        customer_history=customer_history,
        article_history=article_history,
        customer_article_history=customer_article_history,
    )
    return {
        "ranking_example_id": f"{transaction['event_id']}::{candidate_article_id}",
        "label_event_id": transaction["event_id"],
        "label_timestamp": transaction["event_time"],
        "customer_id": transaction["customer_id"],
        "target_article_id": target_article_id,
        "candidate_article_id": candidate_article_id,
        "label_purchase": feature_row["label_purchase"],
        "candidate_source": candidate_source,
        "candidate_rank": str(candidate_rank),
        "candidate_score": candidate_score,
        "retrieval_query_text": retrieval_query_text,
        "retrieval_seed_article_ids": "|".join(retrieval_seed_article_ids),
        **{field: feature_row[field] for field in TRAINING_FEATURE_FIELDS},
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


def _select_negative_candidates(*, result, target_article_id: str, limit: int) -> list:
    selected_candidates = []
    seen_article_ids = {target_article_id}
    for candidate in result.candidates:
        if candidate.article_id in seen_article_ids:
            continue
        selected_candidates.append(candidate)
        seen_article_ids.add(candidate.article_id)
        if len(selected_candidates) >= limit:
            break
    return selected_candidates
