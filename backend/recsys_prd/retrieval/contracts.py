from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModalitySpec:
    name: str
    input_fields: tuple[str, ...]
    output_artifact: str
    description: str


@dataclass(frozen=True)
class FusionStrategy:
    name: str
    stage: str
    required_modalities: tuple[str, ...]
    output_artifact: str
    description: str


@dataclass(frozen=True)
class RetrievalRequest:
    query_text: str = ""
    seed_article_ids: tuple[str, ...] = ()
    customer_id: str = ""
    session_id: str = ""
    limit: int = 10
    index_name: str = "fused"


@dataclass(frozen=True)
class CandidateRecord:
    article_id: str
    score: float
    structured_metadata: dict[str, str]
    modality_availability: dict[str, bool]


@dataclass(frozen=True)
class RetrievalResult:
    candidates: tuple[CandidateRecord, ...]
    index_name: str
    context_tokens: tuple[str, ...]
