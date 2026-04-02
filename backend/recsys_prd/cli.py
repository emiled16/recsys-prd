from __future__ import annotations

import argparse
from pathlib import Path

from recsys_prd.events.replay import publish_local_replay
from recsys_prd.events.validation import validate_local_replay
from recsys_prd.ingestion.hm_raw import ingest_hm_raw
from recsys_prd.features.online_service import OnlineFeatureService
from recsys_prd.features.streaming_features import compute_online_feature_store
from recsys_prd.features.training_dataset import build_point_in_time_training_dataset
from recsys_prd.normalization.pipeline import run_hm_normalization
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

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "ingest-hm-raw":
        result = ingest_hm_raw(args.source, replace=args.replace)
        print(f"Ingested H&M raw dataset from {result.source}")
        print(f"Target root: {result.target_root}")
        print(f"Images copied: {result.image_count}")
        print(f"Manifest: {result.manifest_path}")
        return 0

    if args.command == "normalize-hm":
        outputs = run_hm_normalization()
        for name, path in outputs.items():
            print(f"{name}: {path}")
        return 0

    if args.command == "validate-hm-normalized":
        result = validate_hm_normalized()
        print(f"Validation OK: {result['ok']}")
        return 0

    if args.command == "generate-hm-events":
        outputs = publish_local_replay()
        for name, path in outputs.items():
            print(f"{name}: {path}")
        return 0

    if args.command == "validate-hm-events":
        result = validate_local_replay()
        print(f"Validation OK: {result['ok']}")
        return 0

    if args.command == "build-pit-training-set":
        path = build_point_in_time_training_dataset()
        print(f"training_dataset: {path}")
        return 0

    if args.command == "compute-online-features":
        outputs = compute_online_feature_store()
        for name, path in outputs.items():
            print(f"{name}: {path}")
        return 0

    if args.command == "get-online-features":
        service = OnlineFeatureService()
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

    parser.error(f"Unsupported command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
