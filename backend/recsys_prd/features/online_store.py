from __future__ import annotations

from pathlib import Path

from recsys_prd.io.json_ops import write_json


def write_online_store(
    *,
    store_root: Path,
    session_features: dict[str, dict],
    customer_features: dict[str, dict],
    article_features: dict[str, dict],
) -> dict[str, Path]:
    """Write the local online-serving store snapshots."""
    session_path = store_root / "session_intent_features.json"
    customer_path = store_root / "customer_realtime_features.json"
    article_path = store_root / "article_realtime_features.json"

    write_json(session_path, session_features)
    write_json(customer_path, customer_features)
    write_json(article_path, article_features)

    return {
        "session_intent_features": session_path,
        "customer_realtime_features": customer_path,
        "article_realtime_features": article_path,
    }
