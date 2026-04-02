from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from recsys_prd.config import AppSettings, get_app_settings


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
        points = [
            PointStruct(
                id=index,
                vector=record["vector"],
                payload={
                    "article_id": record["article_id"],
                    "structured_metadata": record["structured_metadata"],
                    "modality_availability": record["modality_availability"],
                    "model_name": record["model_name"],
                    "model_version": record["model_version"],
                },
            )
            for index, record in enumerate(records, start=1)
        ]
        self.client.upsert(collection_name=collection_name, points=points)
        return len(points)
