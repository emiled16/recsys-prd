from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

TrackingEventType = Literal[
    "recommendation_exposure",
    "recommendation_click",
    "recommendation_feedback",
]


class TrackingEventRequest(BaseModel):
    event_type: TrackingEventType
    event_time: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    customer_id: str = ""
    session_id: str = ""
    response_id: str = ""
    article_id: str = ""
    query_text: str = ""
    source: str = "frontend"
    metadata: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_tracking_event(self) -> "TrackingEventRequest":
        if self.session_id and not self.customer_id:
            raise ValueError("session_id requires customer_id so session state remains stable.")
        if self.event_type in {"recommendation_exposure", "recommendation_click"}:
            if not self.response_id:
                raise ValueError("response_id is required for recommendation tracking events.")
        if self.event_type == "recommendation_click" and not self.article_id:
            raise ValueError("article_id is required for recommendation click events.")
        if self.event_type == "recommendation_feedback" and not self.response_id:
            raise ValueError("response_id is required for recommendation feedback events.")
        if self.event_type == "recommendation_feedback" and not (
            self.article_id or self.query_text.strip()
        ):
            raise ValueError("article_id or query_text is required for feedback events.")
        return self


class TrackingEventsRequest(BaseModel):
    events: list[TrackingEventRequest] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_batch(self) -> "TrackingEventsRequest":
        if not self.events:
            raise ValueError("at least one tracking event is required.")
        return self


class TrackingEventsResponse(BaseModel):
    accepted_count: int
    event_types: list[str]
    event_log_path: str


class ReadinessResponse(BaseModel):
    ready: bool
    checked_at_utc: str
    components: dict[str, bool]


class DiagnosticsResponse(BaseModel):
    service_name: str
    version: str
    environment: str
    ready: bool
    supported_endpoints: list[str]
    supported_event_types: list[str]
    capability_flags: dict[str, bool]
    contract_notes: list[str]
    safe_state: dict[str, Any] = Field(default_factory=dict)
