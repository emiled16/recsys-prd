from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.api.smoke import build_api_smoke_report
from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.io.json_ops import write_json
from recsys_prd.observability.metrics import RETRIEVAL_PROMOTION_READY
from recsys_prd.schemas.artifacts import PromotionGateDecision
from recsys_prd.serving.online_evaluation import build_online_experiment_report


def evaluate_promotion_gate(
    *,
    retrieval_report_path: Path | None = None,
    ranking_evaluation_path: Path | None = None,
    api_smoke_report_path: Path | None = None,
    online_evaluation_report_path: Path | None = None,
    output_path: Path | None = None,
    ranking_thresholds: dict[str, float] | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path | dict[str, object]]:
    """Combine offline retrieval, ranking, API smoke, and online guardrails into one decision."""
    settings = settings or get_app_settings()
    retrieval_report_path = retrieval_report_path or (
        settings.paths.reports_root / "retrieval" / "offline_retrieval_evaluation.json"
    )
    ranking_evaluation_path = ranking_evaluation_path or _latest_ranking_evaluation_path(settings)
    api_smoke_report_path = api_smoke_report_path or (
        settings.paths.reports_root / "serving" / "api_smoke_report.json"
    )
    online_evaluation_report_path = online_evaluation_report_path or (
        settings.paths.reports_root / "experiments" / "online_evaluation_report.json"
    )
    output_path = output_path or settings.paths.reports_root / "promotion" / "gate_report.json"

    if not api_smoke_report_path.exists():
        build_api_smoke_report(report_path=api_smoke_report_path, settings=settings)
    if not online_evaluation_report_path.exists():
        build_online_experiment_report(
            report_path=online_evaluation_report_path,
            settings=settings,
        )

    retrieval_report = _load_json(retrieval_report_path)
    ranking_report = _load_json(ranking_evaluation_path)
    api_smoke_report = _load_json(api_smoke_report_path)
    online_report = _load_json(online_evaluation_report_path)

    ranking_thresholds = ranking_thresholds or {
        "precision_at_k": 0.0,
        "map_at_k": 0.0,
        "ndcg_at_k": 0.0,
        "pairwise_quality": 0.0,
    }
    blockers: list[str] = []
    retrieval_ready = bool(retrieval_report.get("readiness", {}).get("ready_for_promotion", False))
    if not retrieval_ready:
        blockers.append("retrieval_not_ready")

    ranking_metrics = ranking_report.get("metrics", {})
    ranking_ready = True
    for metric_name, threshold in ranking_thresholds.items():
        if float(ranking_metrics.get(metric_name, 0.0)) < threshold:
            blockers.append(f"ranking_metric_below_threshold:{metric_name}")
            ranking_ready = False

    api_smoke_ok = not api_smoke_report.get("blockers", [])
    if not api_smoke_ok:
        blockers.append("api_smoke_failed")

    experiment_ready = not online_report.get("rollback_recommended", False)
    if not experiment_ready:
        blockers.append("online_guardrail_failed")

    ready_for_promotion = retrieval_ready and ranking_ready and api_smoke_ok and experiment_ready
    RETRIEVAL_PROMOTION_READY.set(1 if ready_for_promotion else 0)
    decision = PromotionGateDecision(
        checked_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        ready_for_promotion=ready_for_promotion,
        retrieval_ready=retrieval_ready,
        ranking_ready=ranking_ready,
        api_smoke_ok=api_smoke_ok,
        experiment_ready=experiment_ready,
        blockers=blockers,
        details={
            "retrieval_report_path": str(retrieval_report_path),
            "ranking_evaluation_path": str(ranking_evaluation_path),
            "api_smoke_report_path": str(api_smoke_report_path),
            "online_evaluation_report_path": str(online_evaluation_report_path),
            "ranking_thresholds": ranking_thresholds,
        },
    )
    write_json(output_path, decision.model_dump())
    return {"report": output_path, "decision": decision.model_dump()}


def _latest_ranking_evaluation_path(settings: AppSettings) -> Path:
    evaluation_root = settings.paths.models_root / "evaluations"
    evaluation_paths = sorted(evaluation_root.glob("*/*/evaluation.json"))
    if not evaluation_paths:
        raise FileNotFoundError(
            "No ranking evaluation report was found under data/models/evaluations."
        )
    return evaluation_paths[-1]


def _load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
