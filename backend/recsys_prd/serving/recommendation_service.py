from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from recsys_prd.api.models import RecommendationItem, RecommendationRequest, RecommendationResponse
from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.retrieval.candidate_retrieval import CandidateRetriever
from recsys_prd.retrieval.contracts import RetrievalRequest
from recsys_prd.serving.experimentation import ExperimentAssigner, ExposureLogger


class RecommendationService:
    """Orchestrate candidate retrieval, ranking, fallback, and exposure logging."""

    def __init__(
        self,
        *,
        retriever: CandidateRetriever | None = None,
        ranker: Any | None = None,
        assigner: ExperimentAssigner | None = None,
        exposure_logger: ExposureLogger | None = None,
        settings: AppSettings | None = None,
    ) -> None:
        self.settings = settings or get_app_settings()
        self.retriever = retriever or CandidateRetriever(settings=self.settings)
        self.ranker = ranker or _load_registered_ranker(self.settings.paths.models_root)
        self.assigner = assigner or ExperimentAssigner()
        self.exposure_logger = exposure_logger or ExposureLogger(settings=self.settings)

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        assignment = self.assigner.assign(
            customer_id=request.customer_id,
            session_id=request.session_id,
        )
        response_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        retrieval_result = self.retriever.retrieve(
            RetrievalRequest(
                query_text=request.query_text,
                seed_article_ids=tuple(request.seed_article_ids),
                customer_id=request.customer_id,
                session_id=request.session_id,
                limit=request.limit,
                index_name="fused",
            )
        )
        fallback_used = assignment.variant == "retrieval_only" or self.ranker is None
        recommendations = (
            self._build_fallback_recommendations(retrieval_result.candidates)
            if fallback_used
            else self._build_ranked_recommendations(retrieval_result.candidates)
        )
        response = RecommendationResponse(
            response_id=response_id,
            experiment=assignment.experiment,
            variant=assignment.variant,
            fallback_used=fallback_used,
            recommendations=recommendations[: request.limit],
            warnings=["retrieval_fallback"] if fallback_used else [],
        )
        self.exposure_logger.log_exposure(
            response_id=response_id,
            assignment=assignment,
            request_payload=request.model_dump(),
            recommendation_payload=[item.model_dump() for item in response.recommendations],
        )
        return response

    def fallback_response(
        self,
        request: RecommendationRequest,
        *,
        reason: str,
    ) -> RecommendationResponse:
        retrieval_result = self.retriever.retrieve(
            RetrievalRequest(
                query_text=request.query_text,
                seed_article_ids=tuple(request.seed_article_ids),
                customer_id=request.customer_id,
                session_id=request.session_id,
                limit=request.limit,
                index_name="fused",
            )
        )
        return RecommendationResponse(
            response_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"),
            experiment=self.assigner.experiment_name,
            variant="fallback",
            fallback_used=True,
            recommendations=self._build_fallback_recommendations(retrieval_result.candidates)[
                : request.limit
            ],
            warnings=[reason],
        )

    def _build_ranked_recommendations(self, candidates) -> list[RecommendationItem]:
        scored_candidates: list[tuple[float, Any]] = []
        for index, candidate in enumerate(candidates, start=1):
            ranking_row = {
                "candidate_rank": str(index),
                "candidate_score": f"{candidate.score:.6f}",
                "candidate_source": "retrieval",
                "article_product_type_name": candidate.structured_metadata.get(
                    "product_type_name", ""
                ),
                "article_product_group_name": candidate.structured_metadata.get(
                    "product_group_name", ""
                ),
                "article_colour_group_name": candidate.structured_metadata.get(
                    "colour_group_name", ""
                ),
                "article_department_name": candidate.structured_metadata.get(
                    "department_name", ""
                ),
                "article_index_group_name": candidate.structured_metadata.get(
                    "index_group_name", ""
                ),
            }
            scored_candidates.append((self.ranker.predict_probability(ranking_row), candidate))
        return [
            RecommendationItem(
                article_id=candidate.article_id,
                score=round(score, 6),
                source="ranked",
                rank=rank,
                metadata=candidate.structured_metadata,
            )
            for rank, (score, candidate) in enumerate(
                sorted(scored_candidates, key=lambda item: (-item[0], item[1].article_id)),
                start=1,
            )
        ]

    def _build_fallback_recommendations(self, candidates) -> list[RecommendationItem]:
        return [
            RecommendationItem(
                article_id=candidate.article_id,
                score=round(candidate.score, 6),
                source="retrieval",
                rank=rank,
                metadata=candidate.structured_metadata,
            )
            for rank, candidate in enumerate(candidates, start=1)
        ]


def _load_registered_ranker(models_root: Path):
    latest_candidates = sorted((models_root / "registry").glob("*/latest_candidate.json"))
    if not latest_candidates:
        return None
    registration = json.loads(latest_candidates[-1].read_text(encoding="utf-8"))
    model_path = Path(registration["artifacts"]["model_path"])
    if not model_path.exists():
        return None
    from recsys_prd.ranking.training import load_ranking_model

    return load_ranking_model(model_path)
