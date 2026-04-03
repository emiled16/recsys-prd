from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.io.json_ops import write_json
from recsys_prd.io.jsonl_ops import read_jsonl, write_jsonl
from recsys_prd.retrieval.embedding_support import stable_digest


def build_vector_indexes(
    *,
    embeddings_root: Path | None = None,
    indexes_root: Path | None = None,
    embedding_manifest_path: Path | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path]:
    """Build local vector index artifacts from embedding outputs."""
    settings = settings or get_app_settings()
    embeddings_root = embeddings_root or settings.paths.embeddings_root
    indexes_root = indexes_root or settings.paths.indexes_root
    embedding_manifest_path = embedding_manifest_path or embeddings_root / "manifest.json"
    built_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    embedding_manifest = _load_manifest(embedding_manifest_path)

    text_source = embeddings_root / "text" / "article_text_embeddings.jsonl"
    fused_source = embeddings_root / "fused" / "article_fused_embeddings.jsonl"

    text_index_path = indexes_root / "text" / "article_text_index.jsonl"
    fused_index_path = indexes_root / "fused" / "article_fused_index.jsonl"

    text_records = _build_index_records(
        read_jsonl(text_source),
        source_embedding_manifest_path=embedding_manifest_path,
        source_embedding_manifest=embedding_manifest,
        built_at=built_at,
    )
    fused_records = _build_index_records(
        read_jsonl(fused_source),
        source_embedding_manifest_path=embedding_manifest_path,
        source_embedding_manifest=embedding_manifest,
        built_at=built_at,
    )
    write_jsonl(text_index_path, text_records)
    write_jsonl(fused_index_path, fused_records)

    manifest_path = indexes_root / "manifest.json"
    write_json(
        manifest_path,
        {
            "built_at_utc": built_at,
            "distance_metric": "cosine",
            "source_embedding_manifest_path": str(embedding_manifest_path),
            "source_embedding_digest": embedding_manifest.get("source", {}).get("digest", ""),
            "indexes": {
                "text": _index_manifest(
                    path=text_index_path,
                    source_path=text_source,
                    row_count=len(text_records),
                    dimension=_dimension(text_records),
                    strategy_name="text_first_baseline",
                    built_at=built_at,
                    source_embedding_manifest_path=embedding_manifest_path,
                    source_embedding_manifest=embedding_manifest,
                    artifact_digest=stable_digest(text_records),
                ),
                "fused": _index_manifest(
                    path=fused_index_path,
                    source_path=fused_source,
                    row_count=len(fused_records),
                    dimension=_dimension(fused_records),
                    strategy_name="late_fusion_multimodal",
                    built_at=built_at,
                    source_embedding_manifest_path=embedding_manifest_path,
                    source_embedding_manifest=embedding_manifest,
                    artifact_digest=stable_digest(fused_records),
                ),
            },
        },
    )
    return {
        "text_index": text_index_path,
        "fused_index": fused_index_path,
        "manifest": manifest_path,
    }


def _build_index_records(
    embedding_records: list[dict],
    *,
    source_embedding_manifest_path: Path,
    source_embedding_manifest: dict[str, object],
    built_at: str,
) -> list[dict]:
    return [
        {
            "article_id": record["article_id"],
            "vector": record["vector"],
            "vector_dimension": record["vector_dimension"],
            "vector_norm": round(_vector_norm(record["vector"]), 6),
            "strategy_name": record["strategy_name"],
            "model_name": record["model_name"],
            "model_version": record["model_version"],
            "backend": record.get("backend", ""),
            "structured_metadata": record["structured_metadata"],
            "modality_availability": record["modality_availability"],
            "lineage": {
                "source_embedding_manifest_path": str(source_embedding_manifest_path),
                "source_embedding_digest": source_embedding_manifest.get("source", {}).get(
                    "digest", ""
                ),
                "source_embedding_generated_at_utc": source_embedding_manifest.get(
                    "generated_at_utc", ""
                ),
                "built_at_utc": built_at,
                "artifact_digest": stable_digest(record),
            },
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
    built_at: str,
    source_embedding_manifest_path: Path,
    source_embedding_manifest: dict[str, object],
    artifact_digest: str,
) -> dict[str, object]:
    return {
        "path": str(path),
        "source_embedding_path": str(source_path),
        "source_embedding_manifest_path": str(source_embedding_manifest_path),
        "source_embedding_digest": source_embedding_manifest.get("source", {}).get("digest", ""),
        "source_embedding_generated_at_utc": source_embedding_manifest.get("generated_at_utc", ""),
        "row_count": row_count,
        "dimension": dimension,
        "strategy_name": strategy_name,
        "built_at_utc": built_at,
        "artifact_digest": artifact_digest,
    }


def _dimension(records: list[dict]) -> int:
    if not records:
        return 0
    return int(records[0]["vector_dimension"])


def _vector_norm(vector: list[float]) -> float:
    return math.sqrt(sum(component * component for component in vector))


def _load_manifest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
