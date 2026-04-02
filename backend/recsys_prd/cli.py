from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.events.replay import publish_local_replay
from recsys_prd.events.validation import validate_local_replay
from recsys_prd.features.consumer import consume_feature_updates
from recsys_prd.features.online_service import OnlineFeatureService
from recsys_prd.features.online_store import RedisOnlineFeatureStore
from recsys_prd.features.parity_validation import validate_feature_parity_and_freshness
from recsys_prd.features.streaming_features import compute_online_feature_store
from recsys_prd.features.training_dataset import build_point_in_time_training_dataset
from recsys_prd.ingestion.hm_raw import ingest_hm_raw
from recsys_prd.normalization.pipeline import run_hm_normalization
from recsys_prd.ranking.dataset import build_ranking_dataset
from recsys_prd.ranking.registry import register_candidate_ranking_model
from recsys_prd.ranking.training import train_local_ranking_model
from recsys_prd.retrieval.candidate_retrieval import CandidateRetriever
from recsys_prd.retrieval.contracts import RetrievalRequest
from recsys_prd.retrieval.embedding_pipeline import build_embedding_artifacts
from recsys_prd.retrieval.vector_index import build_vector_indexes
from recsys_prd.services.mlflow_store import probe_mlflow_tracking
from recsys_prd.services.qdrant_store import ensure_qdrant_connection
from recsys_prd.services.redpanda import (
    KafkaReplayPublisher,
    bootstrap_redpanda_topics,
    validate_broker_replay,
)
from recsys_prd.validation.hm_normalized import validate_hm_normalized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="recsys-prd-backend")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser(
        "ingest-hm-raw",
        help="Ingest the raw H&M dataset into data/raw/hm.",
    )
    ingest_parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Path to the unpacked H&M dataset directory or a zip archive.",
    )
    ingest_parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing files under data/raw/hm.",
    )
    subparsers.add_parser(
        "normalize-hm",
        help="Normalize ingested H&M raw datasets into data/normalized/.",
    )
    subparsers.add_parser(
        "validate-hm-normalized",
        help="Validate normalized H&M datasets and write a data quality report.",
    )
    subparsers.add_parser(
        "generate-hm-events",
        help="Generate local replay batches for interaction and catalog events.",
    )
    subparsers.add_parser(
        "validate-hm-events",
        help="Validate generated local replay batches.",
    )
    subparsers.add_parser(
        "bootstrap-redpanda-topics",
        help="Create the local Redpanda topics needed by replay and serving.",
    )
    subparsers.add_parser(
        "build-pit-training-set",
        help="Build a point-in-time correct offline training dataset.",
    )
    subparsers.add_parser(
        "compute-online-features",
        help="Compute local online feature snapshots from replayed events.",
    )
    get_online_parser = subparsers.add_parser(
        "get-online-features",
        help="Fetch one online feature payload from the local serving store.",
    )
    get_online_parser.add_argument(
        "--entity",
        choices=["session", "customer", "article"],
        required=True,
        help="Online entity type to fetch.",
    )
    get_online_parser.add_argument("--customer-id", help="Customer identifier.")
    get_online_parser.add_argument("--session-id", help="Session identifier.")
    get_online_parser.add_argument("--article-id", help="Article identifier.")
    subparsers.add_parser(
        "validate-feature-parity",
        help="Validate online feature freshness and offline-online parity.",
    )
    subparsers.add_parser(
        "consume-feature-updates",
        help="Consume broker events and apply Redis online feature updates.",
    )
    subparsers.add_parser(
        "probe-redis",
        help="Verify Redis connectivity for the online feature store.",
    )
    subparsers.add_parser(
        "build-embeddings",
        help="Build deterministic text, image, and fused retrieval embeddings.",
    )
    subparsers.add_parser(
        "build-vector-index",
        help="Build local vector index artifacts from embedding outputs.",
    )
    subparsers.add_parser(
        "probe-qdrant",
        help="Verify Qdrant connectivity and collection setup.",
    )
    subparsers.add_parser(
        "publish-replay-to-kafka",
        help="Publish replay artifacts into broker topics.",
    )
    subparsers.add_parser(
        "validate-broker-replay",
        help="Validate replay message counts after broker publishing.",
    )
    subparsers.add_parser(
        "build-ranking-dataset",
        help="Build a ranking training dataset from labels, retrieval, and PIT features.",
    )
    subparsers.add_parser(
        "train-ranking-model",
        help="Train the local baseline ranking model and write tracked artifacts.",
    )
    subparsers.add_parser(
        "register-ranking-model",
        help="Register the latest trained ranking model as a candidate model version.",
    )
    subparsers.add_parser(
        "probe-mlflow",
        help="Verify MLflow tracking and artifact logging.",
    )
    retrieve_parser = subparsers.add_parser(
        "retrieve-candidates",
        help="Retrieve ranked product candidates from the local vector index.",
    )
    retrieve_parser.add_argument("--query-text", default="", help="Free-text retrieval query.")
    retrieve_parser.add_argument(
        "--seed-article-id",
        action="append",
        default=[],
        help="Article ID to use as a seed item. Repeat to provide multiple seeds.",
    )
    retrieve_parser.add_argument("--customer-id", default="", help="Customer identifier.")
    retrieve_parser.add_argument("--session-id", default="", help="Session identifier.")
    retrieve_parser.add_argument(
        "--index-name",
        choices=["text", "fused"],
        default="fused",
        help="Local index artifact to query.",
    )
    retrieve_parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of candidates to return.",
    )

    return parser


def run_ingestion_command(args: argparse.Namespace, settings: AppSettings) -> int:
    if args.command == "ingest-hm-raw":
        result = ingest_hm_raw(args.source, replace=args.replace)
        print(f"Ingested H&M raw dataset from {result.source}")
        print(f"Target root: {result.target_root}")
        print(f"Images copied: {result.image_count}")
        print(f"Manifest: {result.manifest_path}")
        return 0

    if args.command == "normalize-hm":
        outputs = run_hm_normalization(settings=settings)
        for name, path in outputs.items():
            print(f"{name}: {path}")
        return 0

    if args.command == "validate-hm-normalized":
        result = validate_hm_normalized(settings=settings)
        print(f"Validation OK: {result['ok']}")
        return 0
    return -1


def run_event_command(args: argparse.Namespace, settings: AppSettings) -> int:
    if args.command == "generate-hm-events":
        outputs = publish_local_replay(settings=settings)
        for name, path in outputs.items():
            print(f"{name}: {path}")
        return 0

    if args.command == "validate-hm-events":
        result = validate_local_replay(settings=settings)
        print(f"Validation OK: {result['ok']}")
        return 0
    if args.command == "bootstrap-redpanda-topics":
        result = bootstrap_redpanda_topics(settings=settings)
        print(result)
        return 0
    if args.command == "publish-replay-to-kafka":
        manifest_path = settings.paths.events_root / "replay_batches" / "manifest.json"
        result = KafkaReplayPublisher(settings=settings).publish_manifest(manifest_path)
        print(result)
        return 0
    if args.command == "validate-broker-replay":
        manifest_path = settings.paths.events_root / "replay_batches" / "manifest.json"
        result = validate_broker_replay(settings=settings, manifest_path=manifest_path)
        print(result)
        return 0
    return -1


def run_feature_command(args: argparse.Namespace, settings: AppSettings) -> int:
    if args.command == "build-pit-training-set":
        path = build_point_in_time_training_dataset(settings=settings)
        print(f"training_dataset: {path}")
        return 0

    if args.command == "compute-online-features":
        outputs = compute_online_feature_store(settings=settings)
        for name, path in outputs.items():
            print(f"{name}: {path}")
        return 0

    if args.command == "get-online-features":
        service = OnlineFeatureService(settings=settings)
        if args.entity == "session":
            print(
                service.get_session_intent_features(
                    customer_id=args.customer_id or "",
                    session_id=args.session_id or "",
                )
            )
            return 0
        if args.entity == "customer":
            print(service.get_customer_realtime_features(customer_id=args.customer_id or ""))
            return 0
        print(service.get_article_realtime_features(article_id=args.article_id or ""))
        return 0

    if args.command == "validate-feature-parity":
        result = validate_feature_parity_and_freshness(settings=settings)
        print(f"Validation OK: {result['ok']}")
        return 0
    if args.command == "consume-feature-updates":
        print(consume_feature_updates(settings=settings))
        return 0
    if args.command == "probe-redis":
        print(RedisOnlineFeatureStore(settings=settings).probe())
        return 0
    return -1


def run_retrieval_command(args: argparse.Namespace, settings: AppSettings) -> int:
    if args.command == "build-embeddings":
        outputs = build_embedding_artifacts(settings=settings)
        for name, path in outputs.items():
            print(f"{name}: {path}")
        return 0

    if args.command == "build-vector-index":
        outputs = build_vector_indexes(settings=settings)
        for name, path in outputs.items():
            print(f"{name}: {path}")
        return 0
    if args.command == "probe-qdrant":
        print(ensure_qdrant_connection(settings=settings))
        return 0
    if args.command == "retrieve-candidates":
        retriever = CandidateRetriever(settings=settings)
        result = retriever.retrieve(
            RetrievalRequest(
                query_text=args.query_text,
                seed_article_ids=tuple(args.seed_article_id),
                customer_id=args.customer_id,
                session_id=args.session_id,
                limit=args.limit,
                index_name=args.index_name,
            )
        )
        print(f"index_name: {result.index_name}")
        print(f"context_tokens: {list(result.context_tokens)}")
        for candidate in result.candidates:
            print(
                f"candidate: article_id={candidate.article_id} "
                f"score={candidate.score:.6f} "
                f"department={candidate.structured_metadata.get('department_name', '')}"
            )
        return 0
    return -1


def run_ranking_command(args: argparse.Namespace, settings: AppSettings) -> int:
    if args.command == "build-ranking-dataset":
        path = build_ranking_dataset(settings=settings)
        print(f"ranking_dataset: {path}")
        return 0

    if args.command == "train-ranking-model":
        outputs = train_local_ranking_model(settings=settings)
        for name, path in outputs.items():
            print(f"{name}: {path}")
        return 0

    if args.command == "register-ranking-model":
        outputs = register_candidate_ranking_model(settings=settings)
        for name, path in outputs.items():
            print(f"{name}: {path}")
        return 0
    if args.command == "probe-mlflow":
        print(probe_mlflow_tracking(settings=settings))
        return 0
    return -1


def main(argv: Sequence[str] | None = None, settings: AppSettings | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = settings or get_app_settings()

    for handler in (
        run_ingestion_command,
        run_event_command,
        run_feature_command,
        run_retrieval_command,
        run_ranking_command,
    ):
        result = handler(args, settings)
        if result >= 0:
            return result

    parser.error(f"Unsupported command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
