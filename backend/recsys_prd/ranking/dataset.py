from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.features.feast_training_dataset import FeastPointInTimeDatasetBuilder
from recsys_prd.features.training_dataset import (
    TRAINING_FEATURE_FIELDS,
    build_point_in_time_feature_row,
    load_training_inputs,
    recent_seed_article_ids,
    record_transaction_history,
)
from recsys_prd.io.json_ops import write_json
from recsys_prd.normalization.writer import write_dataset_bundle
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
    normalized_root: Path | None = None,
    features_root: Path | None = None,
    indexes_root: Path | None = None,
    models_root: Path | None = None,
    index_name: str = "fused",
    negative_sample_count: int = 4,
    max_seed_articles: int = 3,
    pit_builder: FeastPointInTimeDatasetBuilder | None = None,
    settings: AppSettings | None = None,
) -> Path:
    """Build a ranking dataset with one positive row and retrieved negatives per label event."""
    settings = settings or get_app_settings()
    normalized_root = normalized_root or settings.paths.normalized_root
    features_root = features_root or (
        settings.paths.features_offline_root
        if normalized_root == settings.paths.normalized_root
        else normalized_root.parent / "features" / "offline"
    )
    indexes_root = indexes_root or settings.paths.indexes_root
    models_root = models_root or settings.paths.models_root / "training_sets"
    customers, products, image_presence, ordered_transactions = load_training_inputs(
        normalized_root
    )
    retriever = CandidateRetriever(indexes_root=indexes_root, settings=settings)
    pit_builder = pit_builder or FeastPointInTimeDatasetBuilder(settings=settings)

    ranking_requests: list[dict[str, str]] = []
    ranking_metadata: list[dict[str, object]] = []
    customer_history = {}
    article_history = {}
    customer_article_history = {}
    baseline_feature_rows: list[dict[str, str]] = []
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

        ranking_requests.append(
            {
                "event_id": transaction["event_id"],
                "event_time": transaction["event_time"],
                "customer_id": transaction["customer_id"],
                "target_article_id": target_article_id,
                "candidate_article_id": target_article_id,
            }
        )
        ranking_metadata.append(
            {
                "label_event_id": transaction["event_id"],
                "label_timestamp": transaction["event_time"],
                "customer_id": transaction["customer_id"],
                "target_article_id": target_article_id,
                "candidate_article_id": target_article_id,
                "candidate_source": "observed_positive",
                "candidate_rank": "0",
                "candidate_score": "",
                "retrieval_query_text": retrieval_query_text,
                "retrieval_seed_article_ids": seed_article_ids,
            }
        )
        baseline_feature_rows.append(
            build_point_in_time_feature_row(
                transaction=transaction,
                candidate_article_id=target_article_id,
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
            ranking_requests.append(
                {
                    "event_id": transaction["event_id"],
                    "event_time": transaction["event_time"],
                    "customer_id": transaction["customer_id"],
                    "target_article_id": target_article_id,
                    "candidate_article_id": candidate.article_id,
                }
            )
            ranking_metadata.append(
                {
                    "label_event_id": transaction["event_id"],
                    "label_timestamp": transaction["event_time"],
                    "customer_id": transaction["customer_id"],
                    "target_article_id": target_article_id,
                    "candidate_article_id": candidate.article_id,
                    "candidate_source": "retrieval_negative",
                    "candidate_rank": str(negative_rank),
                    "candidate_score": f"{candidate.score:.6f}",
                    "retrieval_query_text": retrieval_query_text,
                    "retrieval_seed_article_ids": seed_article_ids,
                }
            )
            baseline_feature_rows.append(
                build_point_in_time_feature_row(
                    transaction=transaction,
                    candidate_article_id=candidate.article_id,
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

    feature_source = "feast"
    try:
        feature_rows = pit_builder.build_training_rows(
            requests=ranking_requests,
            normalized_root=normalized_root,
            features_root=features_root,
        )
    except Exception:
        feature_rows = baseline_feature_rows
        feature_source = "baseline_fallback"

    rows = _build_ranking_rows(
        metadata=ranking_metadata,
        feature_rows=feature_rows,
    )

    dataset_dir = models_root / "ranking_dataset"
    dataset_path = write_dataset_bundle(
        dataset_dir=dataset_dir,
        dataset_filename="ranking_dataset.parquet",
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
            "feature_source": feature_source,
            "positive_row_count": positive_row_count,
            "negative_row_count": negative_row_count,
            "row_count": len(rows),
        },
    )
    return dataset_path


def _build_ranking_rows(
    *,
    metadata: list[dict[str, object]],
    feature_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    if len(metadata) != len(feature_rows):
        raise ValueError("Ranking metadata rows and Feast feature rows must align.")
    rows: list[dict[str, str]] = []
    for metadata_row, feature_row in zip(metadata, feature_rows, strict=True):
        rows.append(
            {
                "ranking_example_id": (
                    f"{metadata_row['label_event_id']}::{metadata_row['candidate_article_id']}"
                ),
                "label_event_id": str(metadata_row["label_event_id"]),
                "label_timestamp": str(metadata_row["label_timestamp"]),
                "customer_id": str(metadata_row["customer_id"]),
                "target_article_id": str(metadata_row["target_article_id"]),
                "candidate_article_id": str(metadata_row["candidate_article_id"]),
                "label_purchase": feature_row["label_purchase"],
                "candidate_source": str(metadata_row["candidate_source"]),
                "candidate_rank": str(metadata_row["candidate_rank"]),
                "candidate_score": str(metadata_row["candidate_score"]),
                "retrieval_query_text": str(metadata_row["retrieval_query_text"]),
                "retrieval_seed_article_ids": "|".join(
                    metadata_row["retrieval_seed_article_ids"]
                ),
                **{field: feature_row[field] for field in TRAINING_FEATURE_FIELDS},
            }
        )
    return rows


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
