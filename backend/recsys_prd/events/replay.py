from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from recsys_prd.events.catalog_generator import generate_catalog_events
from recsys_prd.events.interaction_generator import generate_interaction_events
from recsys_prd.events.io import write_jsonl
from recsys_prd.io.json_ops import write_json
from recsys_prd.paths import DATA_ROOT, NORMALIZED_ROOT


def publish_local_replay(
    *,
    normalized_root: Path = NORMALIZED_ROOT,
    events_root: Path = DATA_ROOT / "events",
) -> dict[str, Path]:
    """Generate local replay batches and a manifest for interaction and catalog topics."""
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
        {
            "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "topics": {
                "interaction_events": {
                    "path": str(interaction_path),
                    "row_count": len(interaction_events),
                },
                "catalog_events": {
                    "path": str(catalog_path),
                    "row_count": len(catalog_events),
                },
            },
        },
    )
    return {
        "interaction_events": interaction_path,
        "catalog_events": catalog_path,
        "manifest": manifest_path,
    }
