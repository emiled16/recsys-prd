from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.events.io import read_jsonl
from recsys_prd.io.json_ops import write_json
from recsys_prd.observability.metrics import (
    ONLINE_EXPERIMENT_CTR,
    ONLINE_EXPERIMENT_FALLBACK_RATE,
    ONLINE_EXPERIMENT_NULL_RESULT_RATE,
    ONLINE_EXPERIMENT_ROLLBACK_RECOMMENDED,
)
from recsys_prd.schemas.artifacts import OnlineExperimentReport


def build_online_experiment_report(
    *,
    exposures_path: Path | None = None,
    events_path: Path | None = None,
    report_path: Path | None = None,
    settings: AppSettings | None = None,
    fallback_rate_threshold: float = 0.5,
    null_result_rate_threshold: float = 0.5,
    min_ctr: float = 0.0,
) -> dict[str, Path | dict[str, object]]:
    """Summarize exposure and tracking logs into experiment guardrail metrics."""
    settings = settings or get_app_settings()
    exposures_path = (
        exposures_path
        or settings.paths.reports_root / "experiments" / "exposures.jsonl"
    )
    events_path = events_path or settings.paths.reports_root / "experiments" / "api_events.jsonl"
    report_path = report_path or (
        settings.paths.reports_root / "experiments" / "online_evaluation_report.json"
    )

    exposures = read_jsonl(exposures_path) if exposures_path.exists() else []
    events = read_jsonl(events_path) if events_path.exists() else []
    click_events = [event for event in events if event.get("event_type") == "recommendation_click"]
    feedback_events = [
        event for event in events if event.get("event_type") == "recommendation_feedback"
    ]

    exposure_count = len(exposures)
    click_count = len(click_events)
    feedback_count = len(feedback_events)
    ctr = round(click_count / exposure_count, 6) if exposure_count else 0.0
    fallback_count = sum(
        1 for exposure in exposures if exposure.get("response", {}).get("fallback_used", False)
    )
    fallback_rate = round(fallback_count / exposure_count, 6) if exposure_count else 0.0
    null_result_count = sum(
        1
        for exposure in exposures
        if not exposure.get("response", {}).get("recommendations", [])
    )
    null_result_rate = round(null_result_count / exposure_count, 6) if exposure_count else 0.0

    blockers: list[str] = []
    if exposure_count == 0:
        blockers.append("no_exposures_logged")
    if ctr < min_ctr:
        blockers.append("ctr_below_threshold")
    if fallback_rate > fallback_rate_threshold:
        blockers.append("fallback_rate_above_threshold")
    if null_result_rate > null_result_rate_threshold:
        blockers.append("null_result_rate_above_threshold")

    rollback_recommended = any(
        blocker in {"fallback_rate_above_threshold", "null_result_rate_above_threshold"}
        for blocker in blockers
    )
    report = OnlineExperimentReport(
        evaluated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        exposure_count=exposure_count,
        click_count=click_count,
        feedback_count=feedback_count,
        ctr=ctr,
        fallback_rate=fallback_rate,
        null_result_rate=null_result_rate,
        guardrails={
            "min_ctr": min_ctr,
            "max_fallback_rate": fallback_rate_threshold,
            "max_null_result_rate": null_result_rate_threshold,
        },
        rollback_recommended=rollback_recommended,
        blockers=blockers,
    )
    _update_online_metrics(report)
    write_json(report_path, report.model_dump())
    return {"report": report_path, "metrics": report.model_dump()}


def _update_online_metrics(report: OnlineExperimentReport) -> None:
    ONLINE_EXPERIMENT_CTR.set(report.ctr)
    ONLINE_EXPERIMENT_FALLBACK_RATE.set(report.fallback_rate)
    ONLINE_EXPERIMENT_NULL_RESULT_RATE.set(report.null_result_rate)
    ONLINE_EXPERIMENT_ROLLBACK_RECOMMENDED.set(1 if report.rollback_recommended else 0)
