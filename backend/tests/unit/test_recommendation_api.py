from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError

from recsys_prd.api.app import create_app
from recsys_prd.api.models import RecommendationRequest
from recsys_prd.retrieval.contracts import CandidateRecord, RetrievalResult
from recsys_prd.serving.experimentation import ExperimentAssigner, ExposureLogger
from recsys_prd.serving.recommendation_service import RecommendationService


class FakeRetriever:
    def retrieve(self, request) -> RetrievalResult:
        del request
        return RetrievalResult(
            candidates=(
                CandidateRecord(
                    article_id="a-1",
                    score=0.6,
                    structured_metadata={"department_name": "ladies dresses"},
                    modality_availability={"text": True},
                ),
                CandidateRecord(
                    article_id="a-2",
                    score=0.3,
                    structured_metadata={"department_name": "ladies tops"},
                    modality_availability={"text": True},
                ),
            ),
            index_name="fused",
            context_tokens=(),
        )


class FakeRanker:
    def predict_probability(self, row: dict[str, str]) -> float:
        return 0.2 if row["article_department_name"] == "ladies tops" else 0.9


class SlowRecommendationService(RecommendationService):
    def recommend(self, request: RecommendationRequest):
        time.sleep(0.2)
        return super().recommend(request)


class RecommendationApiTests(unittest.TestCase):
    def test_request_model_requires_context(self) -> None:
        with self.assertRaises(ValidationError):
            RecommendationRequest()

    def test_service_ranks_candidates_and_logs_exposures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            exposure_path = Path(tmp_dir) / "exposures.jsonl"
            service = RecommendationService(
                retriever=FakeRetriever(),
                ranker=FakeRanker(),
                assigner=ExperimentAssigner("test_experiment"),
                exposure_logger=ExposureLogger(path=exposure_path),
            )

            response = service.recommend(
                RecommendationRequest(customer_id="c1", query_text="dress", limit=2)
            )

            self.assertFalse(response.fallback_used)
            self.assertEqual(response.recommendations[0].article_id, "a-1")
            exposure_rows = [
                json.loads(line)
                for line in exposure_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(exposure_rows[0]["experiment"], "test_experiment")

    def test_api_returns_timeout_fallback(self) -> None:
        service = SlowRecommendationService(
            retriever=FakeRetriever(),
            ranker=FakeRanker(),
        )
        client = TestClient(create_app(service))

        response = client.post(
            "/recommendations",
            json={"customer_id": "c1", "query_text": "dress", "limit": 2, "timeout_ms": 50},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["fallback_used"])
        self.assertIn("timeout_fallback", payload["warnings"])

    def test_metrics_endpoint_exposes_prometheus_payload(self) -> None:
        client = TestClient(
            create_app(RecommendationService(retriever=FakeRetriever(), ranker=FakeRanker()))
        )

        response = client.get("/metrics")

        self.assertEqual(response.status_code, 200)
        self.assertIn("recsys_api_requests_total", response.text)


if __name__ == "__main__":
    unittest.main()
