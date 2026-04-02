from __future__ import annotations

import hashlib
import math

from recsys_prd.retrieval.representation_strategy import (
    STRUCTURED_MODALITY,
    TEXT_MODALITY,
)
from recsys_prd.schemas.artifacts import EmbeddingArtifactRecord

EMBEDDING_DIMENSION = 12
TEXT_MODEL_NAME = "hashing_text_encoder"
TEXT_MODEL_VERSION = "v1"
IMAGE_MODEL_NAME = "hashing_image_encoder"
IMAGE_MODEL_VERSION = "v1"
FUSION_MODEL_NAME = "late_fusion_average"
FUSION_MODEL_VERSION = "v1"


def embedding_record(
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
) -> EmbeddingArtifactRecord:
    return EmbeddingArtifactRecord(
        article_id=article_id,
        generated_at_utc=generated_at,
        model_name=model_name,
        model_version=model_version,
        modality=modality,
        strategy_name=strategy_name,
        vector=vector,
        vector_dimension=len(vector),
        structured_metadata=structured_metadata,
        modality_availability=modality_availability,
        source_path=source_path,
    )


def structured_metadata(product: dict[str, str]) -> dict[str, str]:
    return {
        field: product.get(field, "")
        for field in STRUCTURED_MODALITY.input_fields
    }


def text_payload(
    product: dict[str, str],
    fields: tuple[str, ...] = TEXT_MODALITY.input_fields,
) -> str:
    return " ".join(product.get(field, "").strip().lower() for field in fields).strip()


def image_payload(*, article_id: str, image_path: str) -> str:
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

    return normalize(values)


def fuse_vectors(
    text_vector: list[float],
    image_vector: list[float] | None,
) -> list[float]:
    if image_vector is None:
        return normalize(text_vector)
    aligned_image_vector = align_vector_dimension(image_vector, dimension=len(text_vector))
    fused = [
        (text_component + image_component) / 2.0
        for text_component, image_component in zip(
            normalize(text_vector),
            aligned_image_vector,
            strict=True,
        )
    ]
    return normalize(fused)


def align_vector_dimension(vector: list[float], *, dimension: int) -> list[float]:
    if len(vector) == dimension:
        return normalize(vector)
    if not vector:
        return [0.0] * dimension
    if len(vector) < dimension:
        padded = vector + [0.0] * (dimension - len(vector))
        return normalize(padded)

    buckets = [0.0] * dimension
    counts = [0] * dimension
    for index, value in enumerate(vector):
        bucket = index % dimension
        buckets[bucket] += value
        counts[bucket] += 1
    reduced = [
        bucket_total / count if count else 0.0
        for bucket_total, count in zip(buckets, counts, strict=True)
    ]
    return normalize(reduced)


def normalize(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0.0:
        return [0.0 for _ in values]
    return [round(value / norm, 6) for value in values]
