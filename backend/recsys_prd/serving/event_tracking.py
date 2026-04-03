from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from recsys_prd.config import AppSettings, get_app_settings


class RecommendationEventLogger:
    """Append recommendation tracking events to a local JSONL audit log."""

    def __init__(
        self,
        *,
        path: Path | None = None,
        settings: AppSettings | None = None,
    ) -> None:
        settings = settings or get_app_settings()
        self.path = path or settings.paths.reports_root / "experiments" / "api_events.jsonl"

    def log_events(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
        return {
            "accepted_count": len(events),
            "event_log_path": str(self.path),
        }
