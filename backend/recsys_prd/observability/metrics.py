from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

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
RETRIEVAL_PROMOTION_READY = Gauge(
    "recsys_retrieval_promotion_ready",
    "Whether the latest retrieval and ranking stack is ready for promotion.",
)
ONLINE_EXPERIMENT_CTR = Gauge(
    "recsys_online_experiment_ctr",
    "Click-through rate from local online evaluation logs.",
)
ONLINE_EXPERIMENT_FALLBACK_RATE = Gauge(
    "recsys_online_experiment_fallback_rate",
    "Fallback rate from local online evaluation logs.",
)
ONLINE_EXPERIMENT_NULL_RESULT_RATE = Gauge(
    "recsys_online_experiment_null_result_rate",
    "Null-result rate from local online evaluation logs.",
)
ONLINE_EXPERIMENT_ROLLBACK_RECOMMENDED = Gauge(
    "recsys_online_experiment_rollback_recommended",
    "Whether online guardrails recommend a rollback.",
)


def metrics_response() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
