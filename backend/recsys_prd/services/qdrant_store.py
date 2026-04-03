from __future__ import annotations

from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.io.jsonl_ops import read_jsonl


def ensure_qdrant_connection(
    settings: AppSettings | None = None,
    *,
    client: Any | None = None,
) -> dict[str, Any]:
    """Verify Qdrant connectivity and ensure the configured collections exist."""
    settings = settings or get_app_settings()
    manager = QdrantIndexManager(settings=settings, client=client)
    existing_collections = manager.list_collections()
    manager.ensure_collection(settings.services.qdrant.text_collection, dimension=12)
    manager.ensure_collection(settings.services.qdrant.fused_collection, dimension=12)
    return {
        "url": settings.services.qdrant.url,
        "existing_collections": existing_collections,
        "managed_collections": [
            settings.services.qdrant.text_collection,
            settings.services.qdrant.fused_collection,
        ],
    }


def load_qdrant_indexes(
    *,
    embeddings_root: Path | None = None,
    settings: AppSettings | None = None,
    manager: "QdrantIndexManager" | None = None,
) -> dict[str, Any]:
    """Load persisted text and fused embedding artifacts into Qdrant collections."""
    settings = settings or get_app_settings()
    embeddings_root = embeddings_root or settings.paths.embeddings_root
    manager = manager or QdrantIndexManager(settings=settings)

    text_path = embeddings_root / "text" / "article_text_embeddings.jsonl"
    fused_path = embeddings_root / "fused" / "article_fused_embeddings.jsonl"
    text_count = manager.upsert_artifact(
        settings.services.qdrant.text_collection,
        text_path,
    )
    fused_count = manager.upsert_artifact(
        settings.services.qdrant.fused_collection,
        fused_path,
    )
    return {
        "text_collection": settings.services.qdrant.text_collection,
        "text_path": str(text_path),
        "text_count": text_count,
        "fused_collection": settings.services.qdrant.fused_collection,
        "fused_path": str(fused_path),
        "fused_count": fused_count,
    }


class QdrantIndexManager:
    """Manage Qdrant collections and upserts for retrieval embeddings."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        client: Any | None = None,
    ) -> None:
        self.settings = settings or get_app_settings()
        self.client = client or QdrantClient(
            host=self.settings.services.qdrant.host,
            port=self.settings.services.qdrant.port,
        )

    def list_collections(self) -> list[str]:
        response = self.client.get_collections()
        collections = getattr(response, "collections", response)
        return [collection.name for collection in collections]

    def ensure_collection(self, name: str, dimension: int) -> None:
        if name in self.list_collections():
            return
        self.client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
        )

    def upsert(self, collection_name: str, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
        self.ensure_collection(collection_name, dimension=_record_dimension(records[0]))
        points = [
            PointStruct(
                id=record["article_id"],
                vector=record["vector"],
                payload={
                    "article_id": record["article_id"],
                    "structured_metadata": record["structured_metadata"],
                    "modality_availability": record["modality_availability"],
                    "model_name": record["model_name"],
                    "model_version": record["model_version"],
                },
            )
            for record in records
        ]
        self.client.upsert(collection_name=collection_name, points=points)
        return len(points)

    def upsert_artifact(self, collection_name: str, artifact_path: Path) -> int:
        records = read_jsonl(artifact_path) if artifact_path.exists() else []
        return self.upsert(collection_name, records)


def _record_dimension(record: dict[str, Any]) -> int:
    if "vector_dimension" in record:
        return int(record["vector_dimension"])
    return len(record.get("vector", []))
