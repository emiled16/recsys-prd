from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

API_REQUESTS = Counter(
    "recsys_api_requests_total",
    "Recommendation API requests by outcome.",
    ["endpoint", "outcome"],
)
API_REQUEST_LATENCY = Histogram(
    "recsys_api_request_latency_seconds",
    "Recommendation API latency in seconds.",
    ["endpoint"],
)
RETRIEVAL_LATENCY = Histogram(
    "recsys_retrieval_latency_seconds",
    "Candidate retrieval latency in seconds.",
)
RANKING_LATENCY = Histogram(
    "recsys_ranking_latency_seconds",
    "Ranking latency in seconds.",
)
FEATURE_LOOKUP_LATENCY = Histogram(
    "recsys_feature_lookup_latency_seconds",
    "Online feature lookup latency in seconds.",
    ["service", "entity"],
)
FALLBACK_RESPONSES = Counter(
    "recsys_fallback_responses_total",
    "Fallback recommendation responses by reason.",
    ["reason"],
)


def metrics_response() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
