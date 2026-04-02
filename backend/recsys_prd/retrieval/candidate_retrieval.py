from __future__ import annotations

import math
from pathlib import Path

from recsys_prd.events.io import read_jsonl
from recsys_prd.features.online_service import OnlineFeatureService
from recsys_prd.paths import DATA_ROOT
from recsys_prd.retrieval.contracts import CandidateRecord, RetrievalRequest, RetrievalResult
from recsys_prd.retrieval.embedding_pipeline import EMBEDDING_DIMENSION, hash_embedding_payload


class CandidateRetriever:
    """Retrieve candidates from the local file-backed vector index."""

    def __init__(
        self,
        indexes_root: Path = DATA_ROOT / "indexes",
        online_feature_service: OnlineFeatureService | None = None,
    ) -> None:
        self.indexes_root = indexes_root
        self.online_feature_service = online_feature_service or OnlineFeatureService()

    def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        index_records = self._load_index(request.index_name)
        seed_article_ids = set(request.seed_article_ids)
        context_tokens = self._context_tokens(request)
        query_vector = self._build_query_vector(
            request=request,
            index_records=index_records,
            context_tokens=context_tokens,
        )
        if query_vector is None:
            return RetrievalResult(
                candidates=(),
                index_name=request.index_name,
                context_tokens=tuple(context_tokens),
            )

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

        ranked = sorted(scored_candidates, key=lambda item: (-item.score, item.article_id))
        return RetrievalResult(
            candidates=tuple(ranked[: request.limit]),
            index_name=request.index_name,
            context_tokens=tuple(context_tokens),
        )

    def _load_index(self, index_name: str) -> list[dict]:
        index_path = self.indexes_root / index_name / f"article_{index_name}_index.jsonl"
        if not index_path.exists():
            return []
        return read_jsonl(index_path)

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
            session_payload = self.online_feature_service.get_session_intent_features(
                customer_id=request.customer_id,
                session_id=request.session_id,
            )
            tokens.extend(_payload_tokens("session", session_payload))
        if request.customer_id:
            customer_payload = self.online_feature_service.get_customer_realtime_features(
                customer_id=request.customer_id,
            )
            tokens.extend(_payload_tokens("customer", customer_payload))
        return tokens


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
    return _normalize([value / len(vectors) for value in averaged])


def _normalize(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0.0:
        return values
    return [value / norm for value in values]


def _cosine_similarity(query_vector: list[float], item_vector: list[float], item_norm: float) -> float:
    query_norm = math.sqrt(sum(component * component for component in query_vector))
    if query_norm == 0.0 or item_norm == 0.0:
        return 0.0
    dot = sum(
        query_component * item_component
        for query_component, item_component in zip(query_vector, item_vector, strict=True)
    )
    return dot / (query_norm * item_norm)
