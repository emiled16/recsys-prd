from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.events.io import write_jsonl
from recsys_prd.io.json_ops import write_json
from recsys_prd.schemas.artifacts import ReplayBatchManifest, ReplayTopicManifest

from simulator.catalog_generator import generate_catalog_events
from simulator.interaction_generator import generate_interaction_events


def publish_local_replay(
    *,
    normalized_root: Path | None = None,
    events_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path]:
    """Generate local replay batches and a manifest for interaction and catalog topics."""
    settings = settings or get_app_settings()
    normalized_root = normalized_root or settings.paths.normalized_root
    events_root = events_root or settings.paths.events_root
    replay_dir = events_root / "replay_batches"
    interaction_events = generate_interaction_events(normalized_root)
    catalog_events = generate_catalog_events(normalized_root)

    interaction_path = replay_dir / "interaction_events.jsonl"
    catalog_path = replay_dir / "catalog_events.jsonl"
    write_jsonl(interaction_path, interaction_events)
    write_jsonl(catalog_path, catalog_events)

    manifest_path = replay_dir / "manifest.json"
    write_json(
        manifest_path,
        ReplayBatchManifest(
            generated_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            topics={
                "interaction_events": ReplayTopicManifest(
                    path=str(interaction_path),
                    row_count=len(interaction_events),
                ),
                "catalog_events": ReplayTopicManifest(
                    path=str(catalog_path),
                    row_count=len(catalog_events),
                ),
            },
        ).model_dump(),
    )
    return {
        "interaction_events": interaction_path,
        "catalog_events": catalog_path,
        "manifest": manifest_path,
    }

