from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError

from recsys_prd.api.app import create_app
from recsys_prd.api.contracts import TrackingEventRequest, TrackingEventsRequest
from recsys_prd.api.models import RecommendationRequest
from recsys_prd.retrieval.contracts import CandidateRecord, RetrievalResult
from recsys_prd.serving.event_tracking import RecommendationEventLogger
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

    def test_tracking_event_request_validates_session_and_response_contract(self) -> None:
        with self.assertRaises(ValidationError):
            TrackingEventRequest(event_type="recommendation_click", customer_id="c1")

        event = TrackingEventRequest(
            event_type="recommendation_click",
            customer_id="c1",
            session_id="s1",
            response_id="r1",
            article_id="a-1",
        )
        self.assertEqual(event.event_type, "recommendation_click")

    def test_api_healthz_reports_ok(self) -> None:
        client = TestClient(
            create_app(RecommendationService(retriever=FakeRetriever(), ranker=FakeRanker()))
        )

        response = client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

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

    def test_api_serves_ranked_recommendations(self) -> None:
        client = TestClient(
            create_app(
                RecommendationService(
                    retriever=FakeRetriever(),
                    ranker=FakeRanker(),
                    assigner=ExperimentAssigner("test_experiment"),
                )
            )
        )

        response = client.post(
            "/recommendations",
            json={"customer_id": "c1", "query_text": "dress", "limit": 2},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["fallback_used"])
        self.assertEqual(payload["recommendations"][0]["article_id"], "a-1")
        self.assertEqual(payload["experiment"], "test_experiment")

    def test_api_reports_readiness_and_diagnostics(self) -> None:
        service = RecommendationService(retriever=FakeRetriever(), ranker=FakeRanker())
        client = TestClient(create_app(service))

        ready_response = client.get("/readyz")
        diagnostics_response = client.get("/diagnostics")

        self.assertEqual(ready_response.status_code, 200)
        self.assertTrue(ready_response.json()["ready"])
        self.assertIn("retriever_loaded", ready_response.json()["components"])

        self.assertEqual(diagnostics_response.status_code, 200)
        diagnostics = diagnostics_response.json()
        self.assertEqual(diagnostics["service_name"], "recsys-prd-api")
        self.assertIn("/recommendations", diagnostics["supported_endpoints"])
        self.assertIn("recommendation_exposure", diagnostics["supported_event_types"])

    def test_api_records_tracking_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = RecommendationService(retriever=FakeRetriever(), ranker=FakeRanker())
            event_logger = RecommendationEventLogger(
                path=Path(tmp_dir) / "api_events.jsonl",
                settings=service.settings,
            )
            client = TestClient(create_app(service, event_logger=event_logger))

            response = client.post(
                "/events",
                json={
                    "events": [
                        {
                            "event_type": "recommendation_exposure",
                            "event_time": "2026-04-02T00:00:00Z",
                            "customer_id": "c1",
                            "session_id": "s1",
                            "response_id": "r1",
                            "metadata": {"surface": "home"},
                        },
                        {
                            "event_type": "recommendation_click",
                            "event_time": "2026-04-02T00:00:01Z",
                            "customer_id": "c1",
                            "session_id": "s1",
                            "response_id": "r1",
                            "article_id": "a-1",
                            "metadata": {"surface": "home"},
                        },
                    ]
                },
            )

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["accepted_count"], 2)
            self.assertEqual(
                payload["event_types"],
                ["recommendation_exposure", "recommendation_click"],
            )
            self.assertTrue(Path(payload["event_log_path"]).exists())
            logged_events = [
                json.loads(line)
                for line in Path(payload["event_log_path"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(logged_events[0]["response_id"], "r1")
            self.assertEqual(logged_events[1]["article_id"], "a-1")

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

    def test_tracking_events_request_requires_at_least_one_event(self) -> None:
        with self.assertRaises(ValidationError):
            TrackingEventsRequest()


if __name__ == "__main__":
    unittest.main()
