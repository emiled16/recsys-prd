from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.events.io import read_jsonl, write_jsonl
from recsys_prd.io.json_ops import write_json


def build_vector_indexes(
    *,
    embeddings_root: Path | None = None,
    indexes_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path]:
    """Build local vector index artifacts from embedding outputs."""
    settings = settings or get_app_settings()
    embeddings_root = embeddings_root or settings.paths.embeddings_root
    indexes_root = indexes_root or settings.paths.indexes_root
    built_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    text_source = embeddings_root / "text" / "article_text_embeddings.jsonl"
    fused_source = embeddings_root / "fused" / "article_fused_embeddings.jsonl"

    text_index_path = indexes_root / "text" / "article_text_index.jsonl"
    fused_index_path = indexes_root / "fused" / "article_fused_index.jsonl"

    text_records = _build_index_records(read_jsonl(text_source))
    fused_records = _build_index_records(read_jsonl(fused_source))
    write_jsonl(text_index_path, text_records)
    write_jsonl(fused_index_path, fused_records)

    manifest_path = indexes_root / "manifest.json"
    write_json(
        manifest_path,
        {
            "built_at_utc": built_at,
            "distance_metric": "cosine",
            "indexes": {
                "text": _index_manifest(
                    path=text_index_path,
                    source_path=text_source,
                    row_count=len(text_records),
                    dimension=_dimension(text_records),
                    strategy_name="text_first_baseline",
                ),
                "fused": _index_manifest(
                    path=fused_index_path,
                    source_path=fused_source,
                    row_count=len(fused_records),
                    dimension=_dimension(fused_records),
                    strategy_name="late_fusion_multimodal",
                ),
            },
        },
    )
    return {
        "text_index": text_index_path,
        "fused_index": fused_index_path,
        "manifest": manifest_path,
    }


def _build_index_records(embedding_records: list[dict]) -> list[dict]:
    return [
        {
            "article_id": record["article_id"],
            "vector": record["vector"],
            "vector_dimension": record["vector_dimension"],
            "vector_norm": round(_vector_norm(record["vector"]), 6),
            "strategy_name": record["strategy_name"],
            "model_name": record["model_name"],
            "model_version": record["model_version"],
            "structured_metadata": record["structured_metadata"],
            "modality_availability": record["modality_availability"],
        }
        for record in embedding_records
    ]


def _index_manifest(
    *,
    path: Path,
    source_path: Path,
    row_count: int,
    dimension: int,
    strategy_name: str,
) -> dict[str, object]:
    return {
        "path": str(path),
        "source_embedding_path": str(source_path),
        "row_count": row_count,
        "dimension": dimension,
        "strategy_name": strategy_name,
    }


def _dimension(records: list[dict]) -> int:
    if not records:
        return 0
    return int(records[0]["vector_dimension"])


def _vector_norm(vector: list[float]) -> float:
    return math.sqrt(sum(component * component for component in vector))
