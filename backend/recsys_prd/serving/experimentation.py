from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings


@dataclass(frozen=True)
class ExperimentAssignment:
    experiment: str
    variant: str
    bucket: int


class ExperimentAssigner:
    """Assign requests into a deterministic experiment bucket."""

    def __init__(self, experiment_name: str = "recommendation_ranking_v1") -> None:
        self.experiment_name = experiment_name

    def assign(self, *, customer_id: str, session_id: str) -> ExperimentAssignment:
        assignment_key = f"{customer_id}::{session_id or 'anonymous'}::{self.experiment_name}"
        digest = hashlib.sha256(assignment_key.encode("utf-8")).hexdigest()
        bucket = int(digest[:8], 16) % 100
        variant = "ranked" if bucket < 50 else "retrieval_only"
        return ExperimentAssignment(
            experiment=self.experiment_name,
            variant=variant,
            bucket=bucket,
        )


class ExposureLogger:
    """Append recommendation exposures to a JSONL audit log."""

    def __init__(
        self,
        *,
        path: Path | None = None,
        settings: AppSettings | None = None,
    ) -> None:
        settings = settings or get_app_settings()
        self.path = path or settings.paths.reports_root / "experiments" / "exposures.jsonl"

    def log_exposure(
        self,
        *,
        response_id: str,
        assignment: ExperimentAssignment,
        request_payload: dict[str, object],
        response_payload: dict[str, object],
        recommendation_payload: list[dict[str, object]],
    ) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "response_id": response_id,
                        "experiment": assignment.experiment,
                        "variant": assignment.variant,
                        "bucket": assignment.bucket,
                        "request": request_payload,
                        "response": response_payload,
                        "recommendations": recommendation_payload,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
