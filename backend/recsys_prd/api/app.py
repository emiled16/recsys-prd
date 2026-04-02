from __future__ import annotations

import asyncio
from time import perf_counter

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

from recsys_prd.api.models import RecommendationRequest
from recsys_prd.observability.metrics import API_REQUEST_LATENCY, API_REQUESTS, metrics_response
from recsys_prd.serving.recommendation_service import RecommendationService


def create_app(service: RecommendationService | None = None) -> FastAPI:
    service = service or RecommendationService()
    app = FastAPI(title="recsys-prd-api", version="0.1.0")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics() -> Response:
        payload, content_type = metrics_response()
        return Response(content=payload, media_type=content_type)

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
