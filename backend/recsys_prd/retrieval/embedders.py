from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from recsys_prd.retrieval.embedding_support import (
    IMAGE_MODEL_NAME,
    IMAGE_MODEL_VERSION,
    TEXT_MODEL_NAME,
    TEXT_MODEL_VERSION,
    embedding_record,
    hash_embedding_payload,
    image_payload,
    stable_digest,
    structured_metadata,
    text_payload,
)
from recsys_prd.retrieval.representation_strategy import (
    LATE_FUSION_MULTIMODAL,
    STRUCTURED_MODALITY,
    TEXT_FIRST_BASELINE,
    TEXT_MODALITY,
)
from recsys_prd.schemas.artifacts import EmbeddingArtifactRecord


class TextEmbedder(ABC):
    """Produce text embedding records for normalized article rows."""

    @abstractmethod
    def embed_articles(
        self,
        rows: Sequence[dict[str, str]],
        *,
        generated_at: str,
    ) -> list[EmbeddingArtifactRecord]:
        """Build text embedding records for article rows."""


class ImageEmbedder(ABC):
    """Produce image embedding records for image manifest rows."""

    @abstractmethod
    def embed_images(
        self,
        rows: Sequence[dict[str, str]],
        *,
        generated_at: str,
    ) -> list[EmbeddingArtifactRecord]:
        """Build image embedding records for image manifest rows."""


def _torch_is_available() -> bool:
    try:
        import torch  # noqa: F401
    except ImportError:
        return False
    return True


def _project_vector(vector: list[float], *, seed: int) -> list[float]:
    if _torch_is_available():
        import torch

        tensor = torch.tensor(vector, dtype=torch.float32)
        matrix = torch.tensor(_projection_matrix(len(vector), seed), dtype=torch.float32)
        projected = torch.matmul(matrix, tensor)
        normalized_tensor = torch.nn.functional.normalize(projected, dim=0)
        return [round(float(value), 6) for value in normalized_tensor.tolist()]
    projected = [
        sum(row_index_value * value for row_index_value, value in zip(row, vector, strict=True))
        for row in _projection_matrix(len(vector), seed)
    ]
    return normalized(projected)


def _projection_matrix(dimension: int, seed: int) -> list[list[float]]:
    rng = random.Random(seed)
    return [[rng.uniform(-1.0, 1.0) for _ in range(dimension)] for _ in range(dimension)]


class _ProjectedEmbedder:
    """Shared deterministic projection path for torch-backed local embeddings."""

    backend_name = "torch_projection"

    def __init__(
        self,
        *,
        dimension: int,
        model_name: str,
        model_version: str,
        seed: int,
    ) -> None:
        self.dimension = dimension
        self.model_name = model_name
        self.model_version = model_version
        self.seed = seed

    def _lineage(
        self, *, payload: str, generated_at: str, source_path: str | None = None
    ) -> dict[str, Any]:
        lineage: dict[str, Any] = {
            "backend": self.backend_name,
            "payload_digest": stable_digest(payload),
            "projection_seed": self.seed,
            "torch_available": _torch_is_available(),
            "generated_at_utc": generated_at,
        }
        if source_path is not None:
            lineage["source_path"] = source_path
        return lineage

    def _project(self, payload: str) -> list[float]:
        seed_payload = f"{self.seed}:{payload}"
        base_vector = hash_embedding_payload(seed_payload, dimension=self.dimension)
        return _project_vector(base_vector, seed=self.seed)

    def runtime_metadata(self) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "backend": self.backend_name,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "dimension": self.dimension,
            "seed": self.seed,
            "torch_available": _torch_is_available(),
        }
        if _torch_is_available():
            import torch

            metadata["torch_version"] = torch.__version__
        return metadata


class TorchTextEmbedder(TextEmbedder, _ProjectedEmbedder):
    """Torch-native text embedding path with deterministic local projections."""

    def __init__(
        self,
        *,
        dimension: int,
        model_name: str = "torch_text_projection",
        model_version: str = "v1",
        seed: int = 13,
    ) -> None:
        _ProjectedEmbedder.__init__(
            self,
            dimension=dimension,
            model_name=model_name,
            model_version=model_version,
            seed=seed,
        )

    def embed_articles(
        self,
        rows: Sequence[dict[str, str]],
        *,
        generated_at: str,
    ) -> list[EmbeddingArtifactRecord]:
        records: list[EmbeddingArtifactRecord] = []
        for row in rows:
            image_available = bool(row.get("image_path"))
            payload = text_payload(row, TEXT_MODALITY.input_fields)
            vector = self._project(payload)
            records.append(
                EmbeddingArtifactRecord.model_validate(
                    embedding_record(
                        article_id=row["article_id"],
                        generated_at=generated_at,
                        model_name=self.model_name,
                        model_version=self.model_version,
                        backend=self.backend_name,
                        modality="text",
                        strategy_name=TEXT_FIRST_BASELINE.name,
                        vector=vector,
                        structured_metadata=structured_metadata(row),
                        modality_availability={
                            "text": True,
                            "image": image_available,
                            "structured": True,
                        },
                        lineage=self._lineage(
                            payload=payload,
                            generated_at=generated_at,
                            source_path=row.get("image_path"),
                        ),
                    )
                )
            )
        return records


class HashingTextEmbedder(TorchTextEmbedder):
    """Backward-compatible alias that preserves the legacy deterministic defaults."""

    def __init__(
        self,
        *,
        dimension: int,
        model_name: str = TEXT_MODEL_NAME,
        model_version: str = TEXT_MODEL_VERSION,
    ) -> None:
        super().__init__(
            dimension=dimension,
            model_name=model_name,
            model_version=model_version,
            seed=13,
        )


class SentenceTransformerTextEmbedder(TextEmbedder):
    """Build article text embeddings with a SentenceTransformer model."""

    def __init__(
        self,
        *,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        model_version: str = "latest",
        batch_size: int = 32,
        normalize_embeddings: bool = True,
        model: Any | None = None,
    ) -> None:
        self.model_name = model_name
        self.model_version = model_version
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings
        self._model = model

    def embed_articles(
        self,
        rows: Sequence[dict[str, str]],
        *,
        generated_at: str,
    ) -> list[EmbeddingArtifactRecord]:
        article_rows = list(rows)
        if not article_rows:
            return []

        payloads = [text_payload(row, TEXT_MODALITY.input_fields) for row in article_rows]
        vectors = self._encode(payloads)
        records: list[EmbeddingArtifactRecord] = []
        for row, vector in zip(article_rows, vectors, strict=True):
            records.append(
                EmbeddingArtifactRecord.model_validate(
                    embedding_record(
                        article_id=row["article_id"],
                        generated_at=generated_at,
                        model_name=self.model_name,
                        model_version=self.model_version,
                        modality="text",
                        strategy_name=TEXT_FIRST_BASELINE.name,
                        vector=vector,
                        structured_metadata=structured_metadata(row),
                        modality_availability={
                            "text": True,
                            "image": bool(row.get("image_path")),
                            "structured": True,
                        },
                    )
                )
            )
        return records

    def _encode(self, payloads: Sequence[str]) -> list[list[float]]:
        model = self._get_model()
        vectors = model.encode(
            list(payloads),
            batch_size=self.batch_size,
            normalize_embeddings=self.normalize_embeddings,
            show_progress_bar=False,
        )
        return [
            _coerce_vector(vector, normalize_vector=self.normalize_embeddings) for vector in vectors
        ]

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:  # pragma: no cover - exercised when dependency is absent.
            raise RuntimeError(
                "sentence-transformers is required to use SentenceTransformerTextEmbedder"
            ) from exc
        self._model = SentenceTransformer(self.model_name)
        return self._model


class HashingImageEmbedder(ImageEmbedder):
    """Backward-compatible alias for the deterministic projection image embedder."""

    def __init__(
        self,
        *,
        dimension: int,
        model_name: str = IMAGE_MODEL_NAME,
        model_version: str = IMAGE_MODEL_VERSION,
    ) -> None:
        self._delegate = TorchImageEmbedder(
            dimension=dimension,
            model_name=model_name,
            model_version=model_version,
            seed=29,
        )

    def embed_images(
        self,
        rows: Sequence[dict[str, str]],
        *,
        generated_at: str,
    ) -> list[EmbeddingArtifactRecord]:
        return self._delegate.embed_images(rows, generated_at=generated_at)


class TorchImageEmbedder(ImageEmbedder, _ProjectedEmbedder):
    """Torch-native image embedding path with deterministic local projections."""

    def __init__(
        self,
        *,
        dimension: int,
        model_name: str = "torch_image_projection",
        model_version: str = "v1",
        seed: int = 29,
    ) -> None:
        _ProjectedEmbedder.__init__(
            self,
            dimension=dimension,
            model_name=model_name,
            model_version=model_version,
            seed=seed,
        )

    def embed_images(
        self,
        rows: Sequence[dict[str, str]],
        *,
        generated_at: str,
    ) -> list[EmbeddingArtifactRecord]:
        records: list[EmbeddingArtifactRecord] = []
        for row in rows:
            payload = image_payload(article_id=row["article_id"], image_path=row["image_path"])
            vector = self._project(payload)
            records.append(
                EmbeddingArtifactRecord.model_validate(
                    embedding_record(
                        article_id=row["article_id"],
                        generated_at=generated_at,
                        model_name=self.model_name,
                        model_version=self.model_version,
                        backend=self.backend_name,
                        modality="image",
                        strategy_name=LATE_FUSION_MULTIMODAL.name,
                        vector=vector,
                        structured_metadata=structured_metadata(row),
                        modality_availability={
                            "text": True,
                            "image": True,
                            "structured": True,
                        },
                        lineage=self._lineage(
                            payload=payload,
                            generated_at=generated_at,
                            source_path=row["image_path"],
                        ),
                        source_path=row["image_path"],
                    )
                )
            )
        return records


class OpenClipImageEmbedder(ImageEmbedder):
    """Build article image embeddings with an OpenCLIP vision encoder."""

    def __init__(
        self,
        *,
        model_name: str = "ViT-B-32",
        pretrained: str = "laion2b_s34b_b79k",
        model_version: str = "latest",
        batch_size: int = 16,
        normalize_embeddings: bool = True,
        model: Any | None = None,
        preprocess: Any | None = None,
    ) -> None:
        self.model_name = f"openclip::{model_name}"
        self.pretrained = pretrained
        self.model_version = model_version
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings
        self._model = model
        self._preprocess = preprocess

    def embed_images(
        self,
        rows: Sequence[dict[str, str]],
        *,
        generated_at: str,
    ) -> list[EmbeddingArtifactRecord]:
        image_rows = list(rows)
        if not image_rows:
            return []

        vectors = self._encode(image_rows)
        records: list[EmbeddingArtifactRecord] = []
        for row, vector in zip(image_rows, vectors, strict=True):
            records.append(
                EmbeddingArtifactRecord.model_validate(
                    embedding_record(
                        article_id=row["article_id"],
                        generated_at=generated_at,
                        model_name=self.model_name,
                        model_version=self.model_version,
                        modality="image",
                        strategy_name=LATE_FUSION_MULTIMODAL.name,
                        vector=vector,
                        structured_metadata={
                            field: row.get(field, "") for field in STRUCTURED_MODALITY.input_fields
                        },
                        modality_availability={
                            "text": True,
                            "image": True,
                            "structured": True,
                        },
                        source_path=row["image_path"],
                    )
                )
            )
        return records

    def _encode(self, rows: Sequence[dict[str, str]]) -> list[list[float]]:
        model = self._get_model()
        preprocess = self._get_preprocess()
        encoded_vectors: list[list[float]] = []
        batch: list[Any] = []
        for row in rows:
            batch.append(preprocess(row["image_path"]))
            if len(batch) >= self.batch_size:
                encoded_vectors.extend(self._encode_batch(model, batch))
                batch = []
        if batch:
            encoded_vectors.extend(self._encode_batch(model, batch))
        return encoded_vectors

    def _encode_batch(self, model: Any, batch: Sequence[Any]) -> list[list[float]]:
        if hasattr(model, "encode_image"):
            vectors = model.encode_image(list(batch))
        else:  # pragma: no cover - only used with custom injected doubles.
            vectors = model(list(batch))
        return [
            _coerce_vector(vector, normalize_vector=self.normalize_embeddings) for vector in vectors
        ]

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            import open_clip
        except ImportError as exc:  # pragma: no cover - exercised when dependency is absent.
            raise RuntimeError("open_clip_torch is required to use OpenClipImageEmbedder") from exc
        model, _, preprocess = open_clip.create_model_and_transforms(
            self.model_name.removeprefix("openclip::"),
            pretrained=self.pretrained,
        )
        self._model = model
        self._preprocess = preprocess
        return self._model

    def _get_preprocess(self) -> Any:
        if self._preprocess is not None:
            return self._preprocess
        self._get_model()
        assert self._preprocess is not None

        def _loader(path: str) -> Any:
            try:
                from PIL import Image
            except ImportError as exc:  # pragma: no cover - exercised when dependency is absent.
                raise RuntimeError("Pillow is required to use OpenClipImageEmbedder") from exc
            image = Image.open(Path(path)).convert("RGB")
            return self._preprocess(image)

        return _loader


def _coerce_vector(vector: Any, *, normalize_vector: bool) -> list[float]:
    if hasattr(vector, "tolist"):
        vector = vector.tolist()
    values = [float(value) for value in vector]
    if not normalize_vector:
        return values
    return normalized(values)


def normalized(values: list[float]) -> list[float]:
    norm = sum(value * value for value in values) ** 0.5
    if norm == 0.0:
        return [0.0 for _ in values]
    return [round(value / norm, 6) for value in values]
