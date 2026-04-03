from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.events.io import read_jsonl
from recsys_prd.io.json_ops import write_json

from simulator.contracts import CATALOG_REQUIRED_FIELDS, INTERACTION_REQUIRED_FIELDS


def validate_local_replay(
    *,
    events_root: Path | None = None,
    reports_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict:
    """Validate local replay batches for ordering and payload completeness."""
    settings = settings or get_app_settings()
    events_root = events_root or settings.paths.events_root
    reports_root = reports_root or settings.paths.reports_root
    replay_dir = events_root / "replay_batches"
    interaction_events = read_jsonl(replay_dir / "interaction_events.jsonl")
    catalog_events = read_jsonl(replay_dir / "catalog_events.jsonl")

    result = {
        "ok": True,
        "checks": {
            "interaction_events": _validate_topic(
                interaction_events,
                required_fields=INTERACTION_REQUIRED_FIELDS,
            ),
            "catalog_events": _validate_topic(
                catalog_events,
                required_fields=CATALOG_REQUIRED_FIELDS,
            ),
        },
    }
    result["ok"] = all(check["ok"] for check in result["checks"].values())
    write_json(reports_root / "data_quality" / "hm_replay_validation.json", result)
    return result


def _validate_topic(events: list[dict], *, required_fields: list[str]) -> dict:
    missing_fields = sorted(
        {
            field
            for event in events
            for field in required_fields
            if event.get(field, "") == ""
        }
    )
    is_sorted = events == sorted(events, key=lambda event: (event["event_time"], event["event_id"]))
    return {
        "ok": bool(events) and not missing_fields and is_sorted,
        "row_count": len(events),
        "missing_required_fields": missing_fields,
        "is_time_sorted": is_sorted,
    }
