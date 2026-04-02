from __future__ import annotations

import hashlib
import math
from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.events.io import write_jsonl
from recsys_prd.features.static_lookups import load_image_manifest, load_product_catalog
from recsys_prd.io.json_ops import write_json
from recsys_prd.paths import DATA_ROOT, NORMALIZED_ROOT
from recsys_prd.retrieval.representation_strategy import (
    IMAGE_MODALITY,
    LATE_FUSION_MULTIMODAL,
    STRUCTURED_MODALITY,
    TEXT_FIRST_BASELINE,
    TEXT_MODALITY,
)


EMBEDDING_DIMENSION = 12
TEXT_MODEL_NAME = "hashing_text_encoder"
TEXT_MODEL_VERSION = "v1"
IMAGE_MODEL_NAME = "hashing_image_encoder"
IMAGE_MODEL_VERSION = "v1"
FUSION_MODEL_NAME = "late_fusion_average"
FUSION_MODEL_VERSION = "v1"


def build_embedding_artifacts(
    *,
    normalized_root: Path = NORMALIZED_ROOT,
    embeddings_root: Path = DATA_ROOT / "embeddings",
) -> dict[str, Path]:
    """Build deterministic text, image, and fused embedding artifacts for retrieval."""
    products = load_product_catalog(normalized_root)
    image_manifest = load_image_manifest(normalized_root)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    text_records: list[dict] = []
    image_records: list[dict] = []
    fused_records: list[dict] = []

    for article_id in sorted(products.keys()):
        product = products[article_id]
        image_row = image_manifest.get(article_id)
        structured_metadata = _structured_metadata(product)

        text_vector = hash_embedding_payload(
            _text_payload(product, TEXT_MODALITY.input_fields),
            dimension=EMBEDDING_DIMENSION,
        )
        text_records.append(
            _embedding_record(
                article_id=article_id,
                generated_at=generated_at,
                model_name=TEXT_MODEL_NAME,
                model_version=TEXT_MODEL_VERSION,
                modality="text",
                strategy_name=TEXT_FIRST_BASELINE.name,
                vector=text_vector,
                structured_metadata=structured_metadata,
                modality_availability={
                    "text": True,
                    "image": image_row is not None,
                    "structured": True,
                },
            )
        )

        if image_row is not None:
            image_vector = hash_embedding_payload(
                _image_payload(article_id=article_id, image_path=image_row["image_path"]),
                dimension=EMBEDDING_DIMENSION,
            )
            image_records.append(
                _embedding_record(
                    article_id=article_id,
                    generated_at=generated_at,
                    model_name=IMAGE_MODEL_NAME,
                    model_version=IMAGE_MODEL_VERSION,
                    modality="image",
                    strategy_name=LATE_FUSION_MULTIMODAL.name,
                    vector=image_vector,
                    structured_metadata=structured_metadata,
                    modality_availability={
                        "text": True,
                        "image": True,
                        "structured": True,
                    },
                    source_path=image_row["image_path"],
                )
            )
        else:
            image_vector = None

        fused_records.append(
            _embedding_record(
                article_id=article_id,
                generated_at=generated_at,
                model_name=FUSION_MODEL_NAME,
                model_version=FUSION_MODEL_VERSION,
                modality="fused",
                strategy_name=LATE_FUSION_MULTIMODAL.name,
                vector=fuse_vectors(text_vector, image_vector),
                structured_metadata=structured_metadata,
                modality_availability={
                    "text": True,
                    "image": image_vector is not None,
                    "structured": True,
                },
            )
        )

    text_path = embeddings_root / "text" / "article_text_embeddings.jsonl"
    image_path = embeddings_root / "image" / "article_image_embeddings.jsonl"
    fused_path = embeddings_root / "fused" / "article_fused_embeddings.jsonl"
    write_jsonl(text_path, text_records)
    write_jsonl(image_path, image_records)
    write_jsonl(fused_path, fused_records)

    manifest_path = embeddings_root / "manifest.json"
    write_json(
        manifest_path,
        {
            "generated_at_utc": generated_at,
            "dimension": EMBEDDING_DIMENSION,
            "artifacts": {
                "text": _artifact_manifest(
                    path=text_path,
                    row_count=len(text_records),
                    model_name=TEXT_MODEL_NAME,
                    model_version=TEXT_MODEL_VERSION,
                    strategy_name=TEXT_FIRST_BASELINE.name,
                    required_modalities=TEXT_FIRST_BASELINE.required_modalities,
                ),
                "image": _artifact_manifest(
                    path=image_path,
                    row_count=len(image_records),
                    model_name=IMAGE_MODEL_NAME,
                    model_version=IMAGE_MODEL_VERSION,
                    strategy_name=LATE_FUSION_MULTIMODAL.name,
                    required_modalities=(IMAGE_MODALITY.name, STRUCTURED_MODALITY.name),
                ),
                "fused": _artifact_manifest(
                    path=fused_path,
                    row_count=len(fused_records),
                    model_name=FUSION_MODEL_NAME,
                    model_version=FUSION_MODEL_VERSION,
                    strategy_name=LATE_FUSION_MULTIMODAL.name,
                    required_modalities=LATE_FUSION_MULTIMODAL.required_modalities,
                ),
            },
        },
    )
    return {
        "text_embeddings": text_path,
        "image_embeddings": image_path,
        "fused_embeddings": fused_path,
        "manifest": manifest_path,
    }


def _embedding_record(
    *,
    article_id: str,
    generated_at: str,
    model_name: str,
    model_version: str,
    modality: str,
    strategy_name: str,
    vector: list[float],
    structured_metadata: dict[str, str],
    modality_availability: dict[str, bool],
    source_path: str | None = None,
) -> dict:
    record = {
        "article_id": article_id,
        "generated_at_utc": generated_at,
        "model_name": model_name,
        "model_version": model_version,
        "modality": modality,
        "strategy_name": strategy_name,
        "vector": vector,
        "vector_dimension": len(vector),
        "structured_metadata": structured_metadata,
        "modality_availability": modality_availability,
    }
    if source_path is not None:
        record["source_path"] = source_path
    return record


def _artifact_manifest(
    *,
    path: Path,
    row_count: int,
    model_name: str,
    model_version: str,
    strategy_name: str,
    required_modalities: tuple[str, ...],
) -> dict[str, object]:
    return {
        "path": str(path),
        "row_count": row_count,
        "model_name": model_name,
        "model_version": model_version,
        "strategy_name": strategy_name,
        "required_modalities": list(required_modalities),
    }


def _structured_metadata(product: dict[str, str]) -> dict[str, str]:
    return {
        field: product.get(field, "")
        for field in STRUCTURED_MODALITY.input_fields
    }


def _text_payload(product: dict[str, str], fields: tuple[str, ...]) -> str:
    return " ".join(product.get(field, "").strip().lower() for field in fields).strip()


def _image_payload(*, article_id: str, image_path: str) -> str:
    return f"{article_id} {image_path.lower()}"


def hash_embedding_payload(payload: str, *, dimension: int) -> list[float]:
    values = [0.0] * dimension
    tokens = [token for token in payload.split() if token]
    if not tokens:
        return values

    for token in tokens:
        token_hash = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = token_hash[0] % dimension
        magnitude = (int.from_bytes(token_hash[1:5], "big") / 2**32) + 0.5
        sign = 1.0 if token_hash[5] % 2 == 0 else -1.0
        values[bucket] += sign * magnitude

    return _normalize(values)


def fuse_vectors(text_vector: list[float], image_vector: list[float] | None) -> list[float]:
    if image_vector is None:
        return text_vector
    fused = [
        (text_component + image_component) / 2.0
        for text_component, image_component in zip(text_vector, image_vector, strict=True)
    ]
    return _normalize(fused)


def _normalize(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0.0:
        return [0.0 for _ in values]
    return [round(value / norm, 6) for value in values]
