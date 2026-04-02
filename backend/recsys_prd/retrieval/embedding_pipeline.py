from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.events.io import write_jsonl
from recsys_prd.features.static_lookups import load_image_manifest, load_product_catalog
from recsys_prd.io.json_ops import write_json
from recsys_prd.retrieval.embedders import (
    HashingImageEmbedder,
    HashingTextEmbedder,
    ImageEmbedder,
    TextEmbedder,
)
from recsys_prd.retrieval.embedding_support import (
    EMBEDDING_DIMENSION,
    FUSION_MODEL_NAME,
    FUSION_MODEL_VERSION,
    embedding_record,
    fuse_vectors,
)
from recsys_prd.retrieval.representation_strategy import (
    IMAGE_MODALITY,
    LATE_FUSION_MULTIMODAL,
    STRUCTURED_MODALITY,
    TEXT_FIRST_BASELINE,
)


def build_embedding_artifacts(
    *,
    normalized_root: Path | None = None,
    embeddings_root: Path | None = None,
    text_embedder: TextEmbedder | None = None,
    image_embedder: ImageEmbedder | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path]:
    """Build text, image, and fused embedding artifacts using pluggable embedders."""
    settings = settings or get_app_settings()
    normalized_root = normalized_root or settings.paths.normalized_root
    embeddings_root = embeddings_root or settings.paths.embeddings_root
    products = load_product_catalog(normalized_root)
    image_manifest = load_image_manifest(normalized_root)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    article_rows = _build_article_rows(products=products, image_manifest=image_manifest)
    text_embedder = text_embedder or HashingTextEmbedder(dimension=EMBEDDING_DIMENSION)
    image_embedder = image_embedder or HashingImageEmbedder(dimension=EMBEDDING_DIMENSION)

    text_record_models = text_embedder.embed_articles(article_rows, generated_at=generated_at)
    image_input_rows = [row for row in article_rows if row.get("image_path")]
    image_record_models = image_embedder.embed_images(image_input_rows, generated_at=generated_at)
    image_record_by_article = {record.article_id: record for record in image_record_models}

    fused_record_models = []
    for text_record in text_record_models:
        image_record = image_record_by_article.get(text_record.article_id)
        fused_record_models.append(
            embedding_record(
                article_id=text_record.article_id,
                generated_at=generated_at,
                model_name=FUSION_MODEL_NAME,
                model_version=FUSION_MODEL_VERSION,
                modality="fused",
                strategy_name=LATE_FUSION_MULTIMODAL.name,
                vector=fuse_vectors(
                    text_record.vector,
                    image_record.vector if image_record is not None else None,
                ),
                structured_metadata=text_record.structured_metadata,
                modality_availability={
                    "text": True,
                    "image": image_record is not None,
                    "structured": True,
                },
            )
        )

    text_records = [record.model_dump(exclude_none=True) for record in text_record_models]
    image_records = [record.model_dump(exclude_none=True) for record in image_record_models]
    fused_records = [record.model_dump(exclude_none=True) for record in fused_record_models]

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
            "dimension": _artifact_dimension(fused_record_models),
            "artifacts": {
                "text": _artifact_manifest(
                    path=text_path,
                    row_count=len(text_records),
                    model_name=text_record_models[0].model_name if text_record_models else "",
                    model_version=text_record_models[0].model_version if text_record_models else "",
                    strategy_name=TEXT_FIRST_BASELINE.name,
                    required_modalities=TEXT_FIRST_BASELINE.required_modalities,
                    dimension=_artifact_dimension(text_record_models),
                ),
                "image": _artifact_manifest(
                    path=image_path,
                    row_count=len(image_records),
                    model_name=image_record_models[0].model_name if image_record_models else "",
                    model_version=(
                        image_record_models[0].model_version if image_record_models else ""
                    ),
                    strategy_name=LATE_FUSION_MULTIMODAL.name,
                    required_modalities=(IMAGE_MODALITY.name, STRUCTURED_MODALITY.name),
                    dimension=_artifact_dimension(image_record_models),
                ),
                "fused": _artifact_manifest(
                    path=fused_path,
                    row_count=len(fused_records),
                    model_name=FUSION_MODEL_NAME,
                    model_version=FUSION_MODEL_VERSION,
                    strategy_name=LATE_FUSION_MULTIMODAL.name,
                    required_modalities=LATE_FUSION_MULTIMODAL.required_modalities,
                    dimension=_artifact_dimension(fused_record_models),
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


def _build_article_rows(
    *,
    products: dict[str, dict[str, str]],
    image_manifest: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    article_rows: list[dict[str, str]] = []
    for article_id in sorted(products.keys()):
        row = dict(products[article_id])
        image_row = image_manifest.get(article_id)
        if image_row is not None:
            row["image_path"] = image_row["image_path"]
        article_rows.append(row)
    return article_rows


def _artifact_manifest(
    *,
    path: Path,
    row_count: int,
    model_name: str,
    model_version: str,
    strategy_name: str,
    required_modalities: tuple[str, ...],
    dimension: int,
) -> dict[str, object]:
    return {
        "path": str(path),
        "row_count": row_count,
        "model_name": model_name,
        "model_version": model_version,
        "strategy_name": strategy_name,
        "required_modalities": list(required_modalities),
        "dimension": dimension,
    }


def _artifact_dimension(records: list) -> int:
    if not records:
        return 0
    return records[0].vector_dimension
