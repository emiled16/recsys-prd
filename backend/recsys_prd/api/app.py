from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from recsys_prd.api.models import RecommendationRequest
from recsys_prd.serving.recommendation_service import RecommendationService


def create_app(service: RecommendationService | None = None) -> FastAPI:
    service = service or RecommendationService()
    app = FastAPI(title="recsys-prd-api", version="0.1.0")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/recommendations")
    async def recommend(request: RecommendationRequest):
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(service.recommend, request),
                timeout=request.timeout_ms / 1000,
            )
            return response.model_dump()
        except asyncio.TimeoutError:
            fallback = service.fallback_response(request, reason="timeout_fallback")
            return JSONResponse(status_code=200, content=fallback.model_dump())
        except ValueError as exc:
            fallback = service.fallback_response(request, reason=str(exc))
            return JSONResponse(status_code=200, content=fallback.model_dump())

    return app
