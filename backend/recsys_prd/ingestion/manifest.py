from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def write_manifest(
    *,
    manifest_path: Path,
    source_kind: str,
    source_path: Path,
    target_root: Path,
    customers_path: Path,
    articles_path: Path,
    transactions_path: Path,
    images_root: Path,
    image_count: int,
) -> None:
    """Write the raw-ingestion manifest for the copied dataset."""
    manifest = {
        "dataset": "hm_personalized_fashion_recommendations",
        "ingested_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_kind": source_kind,
        "source_path": str(source_path),
        "target_root": str(target_root),
        "files": {
            "customers": str(customers_path),
            "articles": str(articles_path),
            "transactions": str(transactions_path),
            "images_root": str(images_root),
        },
        "image_count": image_count,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
