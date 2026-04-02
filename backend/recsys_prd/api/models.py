from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class RecommendationRequest(BaseModel):
    customer_id: str = ""
    session_id: str = ""
    query_text: str = ""
    seed_article_ids: list[str] = Field(default_factory=list)
    limit: int = Field(default=10, ge=1, le=50)
    timeout_ms: int = Field(default=300, ge=50, le=2_000)

    @model_validator(mode="after")
    def validate_request_context(self) -> "RecommendationRequest":
        has_request_context = bool(
            self.customer_id or self.session_id or self.query_text.strip() or self.seed_article_ids
        )
        if not has_request_context:
            raise ValueError(
                "At least one of customer_id, session_id, query_text, "
                "or seed_article_ids is required."
            )
        if self.session_id and not self.customer_id:
            raise ValueError("session_id requires customer_id so online context keys stay stable.")
        return self


class RecommendationItem(BaseModel):
    article_id: str
    score: float
    source: str
    rank: int
    metadata: dict[str, str] = Field(default_factory=dict)


class RecommendationResponse(BaseModel):
    response_id: str
    experiment: str
    variant: str
    fallback_used: bool = False
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
