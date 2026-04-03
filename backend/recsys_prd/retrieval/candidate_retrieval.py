from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.features.feast_online_service import FeastOnlineFeatureService
from recsys_prd.features.online_service import OnlineFeatureService
from recsys_prd.io.jsonl_ops import read_jsonl
from recsys_prd.retrieval.contracts import CandidateRecord, RetrievalRequest, RetrievalResult
from recsys_prd.retrieval.embedding_support import EMBEDDING_DIMENSION, hash_embedding_payload


class QdrantCandidateRetriever:
    """Retrieve candidates from Qdrant while preserving the existing request contract."""

    def __init__(
        self,
        indexes_root: Path | None = None,
        online_feature_service: OnlineFeatureService | None = None,
        feast_online_feature_service: FeastOnlineFeatureService | None = None,
        settings: AppSettings | None = None,
        client: Any | None = None,
    ) -> None:
        self.settings = settings or get_app_settings()
        self.indexes_root = indexes_root or self.settings.paths.indexes_root
        self.online_feature_service = online_feature_service or OnlineFeatureService(
            settings=self.settings
        )
        self.feast_online_feature_service = feast_online_feature_service or (
            FeastOnlineFeatureService(settings=self.settings)
        )
        self.client = client or QdrantClient(
            host=self.settings.services.qdrant.host,
            port=self.settings.services.qdrant.port,
        )
        self.collection_by_index = {
            "text": self.settings.services.qdrant.text_collection,
            "fused": self.settings.services.qdrant.fused_collection,
        }

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        seed_article_ids = set(request.seed_article_ids)
        context_tokens = self._context_tokens(request)
        query_vector = self._build_query_vector(
            request=request,
            index_records=self._load_index(request.index_name),
            context_tokens=context_tokens,
        )
        if query_vector is None:
            return RetrievalResult(
                candidates=(),
                index_name=request.index_name,
                context_tokens=tuple(context_tokens),
            )

        collection_name = self.collection_by_index[request.index_name]
        try:
            raw_points = self._search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=request.limit + len(seed_article_ids),
            )
            candidates = [
                candidate
                for candidate in self._candidate_records(raw_points)
                if candidate.article_id not in seed_article_ids
            ]
        except Exception:
            candidates = self._local_candidates(
                index_records=self._load_index(request.index_name),
                query_vector=query_vector,
                seed_article_ids=seed_article_ids,
            )
        return RetrievalResult(
            candidates=tuple(candidates[: request.limit]),
            index_name=request.index_name,
            context_tokens=tuple(context_tokens),
        )

    def _search(
        self,
        *,
        collection_name: str,
        query_vector: list[float],
        limit: int,
    ) -> list[Any]:
        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                with_payload=True,
            )
            return list(getattr(response, "points", response))
        return list(
            self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
            )
        )

    def _candidate_records(self, raw_points: list[Any]) -> list[CandidateRecord]:
        candidates: list[CandidateRecord] = []
        for point in raw_points:
            if isinstance(point, dict):
                payload = point.get("payload", {})
                score = point.get("score", 0.0)
            else:
                payload = getattr(point, "payload", {})
                score = getattr(point, "score", 0.0)
            candidates.append(
                CandidateRecord(
                    article_id=payload["article_id"],
                    score=round(float(score), 6),
                    structured_metadata=payload.get("structured_metadata", {}),
                    modality_availability=payload.get("modality_availability", {}),
                )
            )
        return candidates

    def _load_index(self, index_name: str) -> list[dict]:
        index_path = self.indexes_root / index_name / f"article_{index_name}_index.jsonl"
        if not index_path.exists():
            return []
        return read_jsonl(index_path)

    def _local_candidates(
        self,
        *,
        index_records: list[dict],
        query_vector: list[float],
        seed_article_ids: set[str],
    ) -> list[CandidateRecord]:
        scored_candidates: list[CandidateRecord] = []
        for record in index_records:
            if record["article_id"] in seed_article_ids:
                continue
            score = _cosine_similarity(
                query_vector,
                record["vector"],
                record.get("vector_norm", 0.0),
            )
            scored_candidates.append(
                CandidateRecord(
                    article_id=record["article_id"],
                    score=round(score, 6),
                    structured_metadata=record["structured_metadata"],
                    modality_availability=record["modality_availability"],
                )
            )
        return sorted(scored_candidates, key=lambda item: (-item.score, item.article_id))

    def _build_query_vector(
        self,
        *,
        request: RetrievalRequest,
        index_records: list[dict],
        context_tokens: list[str],
    ) -> list[float] | None:
        vectors: list[list[float]] = []
        if request.query_text.strip():
            vectors.append(
                hash_embedding_payload(
                    request.query_text.lower(),
                    dimension=EMBEDDING_DIMENSION,
                )
            )
        if context_tokens:
            vectors.append(
                hash_embedding_payload(
                    " ".join(context_tokens),
                    dimension=EMBEDDING_DIMENSION,
                )
            )

        index_by_article = {record["article_id"]: record for record in index_records}
        for article_id in request.seed_article_ids:
            record = index_by_article.get(article_id)
            if record is not None:
                vectors.append(record["vector"])

        if not vectors:
            return None
        return _average_vectors(vectors)

    def _context_tokens(self, request: RetrievalRequest) -> list[str]:
        tokens: list[str] = []
        if request.customer_id and request.session_id:
            session_payloads = (
                self.online_feature_service.get_session_intent_features(
                    customer_id=request.customer_id,
                    session_id=request.session_id,
                ),
                self.feast_online_feature_service.get_session_intent_features(
                    customer_id=request.customer_id,
                    session_id=request.session_id,
                ),
            )
            for payload in session_payloads:
                tokens.extend(_payload_tokens("session", payload))
        if request.customer_id:
            customer_payloads = (
                self.online_feature_service.get_customer_realtime_features(
                    customer_id=request.customer_id,
                ),
                self.feast_online_feature_service.get_customer_realtime_features(
                    customer_id=request.customer_id,
                ),
            )
            for payload in customer_payloads:
                tokens.extend(_payload_tokens("customer", payload))
        return list(dict.fromkeys(tokens))


class CandidateRetriever(QdrantCandidateRetriever):
    """Compatibility alias for the Qdrant-backed retriever."""


def _payload_tokens(prefix: str, payload: dict) -> list[str]:
    tokens: list[str] = []
    for key in sorted(payload.keys()):
        value = payload[key]
        if value in ("", None, 0, 0.0, False):
            continue
        tokens.append(f"{prefix}:{key}={str(value).lower()}")
    return tokens


def _average_vectors(vectors: list[list[float]]) -> list[float]:
    dimension = len(vectors[0])
    averaged = [0.0] * dimension
    for vector in vectors:
        for index, value in enumerate(vector):
            averaged[index] += value
    return [value / len(vectors) for value in averaged]


def _cosine_similarity(
    query_vector: list[float],
    item_vector: list[float],
    item_norm: float,
) -> float:
    query_norm = math.sqrt(sum(component * component for component in query_vector))
    if query_norm == 0.0 or item_norm == 0.0:
        return 0.0
    dot = sum(
        query_component * item_component
        for query_component, item_component in zip(query_vector, item_vector, strict=True)
    )
    return dot / (query_norm * item_norm)
