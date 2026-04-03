from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import perf_counter

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

from recsys_prd.api.contracts import (
    DiagnosticsResponse,
    ReadinessResponse,
    TrackingEventsRequest,
    TrackingEventsResponse,
)
from recsys_prd.api.models import RecommendationRequest
from recsys_prd.observability.metrics import API_REQUEST_LATENCY, API_REQUESTS, metrics_response
from recsys_prd.serving.event_tracking import RecommendationEventLogger
from recsys_prd.serving.recommendation_service import RecommendationService


def create_app(
    service: RecommendationService | None = None,
    event_logger: RecommendationEventLogger | None = None,
) -> FastAPI:
    service = service or RecommendationService()
    event_logger = event_logger or RecommendationEventLogger(settings=service.settings)
    app = FastAPI(title="recsys-prd-api", version="0.1.0")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", response_model=ReadinessResponse)
    async def readyz() -> ReadinessResponse:
        components = {
            "retriever_loaded": service.retriever is not None,
            "ranker_loaded": service.ranker is not None,
            "experiment_assigner_loaded": service.assigner is not None,
            "exposure_logger_ready": service.exposure_logger is not None,
            "event_logger_ready": event_logger is not None,
        }
        return ReadinessResponse(
            ready=all(
                [
                    components["retriever_loaded"],
                    components["experiment_assigner_loaded"],
                    components["exposure_logger_ready"],
                    components["event_logger_ready"],
                ]
            ),
            checked_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            components=components,
        )

    @app.get("/diagnostics", response_model=DiagnosticsResponse)
    async def diagnostics() -> DiagnosticsResponse:
        ready = all(
            [
                service.retriever is not None,
                service.assigner is not None,
                service.exposure_logger is not None,
                event_logger is not None,
            ]
        )
        return DiagnosticsResponse(
            service_name=app.title,
            version=app.version,
            environment=service.settings.environment,
            ready=ready,
            supported_endpoints=[
                "/healthz",
                "/readyz",
                "/diagnostics",
                "/metrics",
                "/recommendations",
                "/events",
            ],
            supported_event_types=[
                "recommendation_exposure",
                "recommendation_click",
                "recommendation_feedback",
            ],
            capability_flags={
                "recommendations": True,
                "fallback_ranking": service.ranker is not None,
                "event_tracking": True,
                "safe_diagnostics": True,
            },
            contract_notes=[
                (
                    "Recommendation requests require either customer_id, session_id, "
                    "query_text, or seed_article_ids."
                ),
                "session_id requires customer_id to keep event correlation stable.",
                "Tracking events are append-only JSONL records.",
            ],
            safe_state={
                "fallback_mode": service.ranker is None,
                "experiment_name": service.assigner.experiment_name,
                "tracking_sink": "reports/experiments/api_events.jsonl",
            },
        )

    @app.get("/metrics")
    async def metrics() -> Response:
        payload, content_type = metrics_response()
        return Response(content=payload, media_type=content_type)

    @app.post("/events", response_model=TrackingEventsResponse)
    async def events(request: TrackingEventsRequest) -> TrackingEventsResponse:
        payload = [event.model_dump() for event in request.events]
        result = event_logger.log_events(payload)
        return TrackingEventsResponse(
            accepted_count=int(result["accepted_count"]),
            event_types=[event["event_type"] for event in payload],
            event_log_path=str(result["event_log_path"]),
        )

    @app.post("/recommendations")
    async def recommend(request: RecommendationRequest):
        started_at = perf_counter()
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(service.recommend, request),
                timeout=request.timeout_ms / 1000,
            )
            API_REQUESTS.labels(endpoint="/recommendations", outcome="ok").inc()
            API_REQUEST_LATENCY.labels(endpoint="/recommendations").observe(
                perf_counter() - started_at
            )
            return response.model_dump()
        except asyncio.TimeoutError:
            fallback = service.fallback_response(request, reason="timeout_fallback")
            API_REQUESTS.labels(endpoint="/recommendations", outcome="timeout").inc()
            API_REQUEST_LATENCY.labels(endpoint="/recommendations").observe(
                perf_counter() - started_at
            )
            return JSONResponse(status_code=200, content=fallback.model_dump())
        except ValueError as exc:
            fallback = service.fallback_response(request, reason=str(exc))
            API_REQUESTS.labels(endpoint="/recommendations", outcome="fallback").inc()
            API_REQUEST_LATENCY.labels(endpoint="/recommendations").observe(
                perf_counter() - started_at
            )
            return JSONResponse(status_code=200, content=fallback.model_dump())

    return app
