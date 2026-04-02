from __future__ import annotations

import json
from pathlib import Path

from recsys_prd.paths import DATA_ROOT


class OnlineFeatureService:
    """Read online feature payloads from the local file-backed serving store."""

    def __init__(self, store_root: Path = DATA_ROOT / "features" / "online_bootstrap") -> None:
        self.store_root = store_root

    def get_session_intent_features(self, *, customer_id: str, session_id: str) -> dict:
        payload = self._read_payload("session_intent_features.json")
        return payload.get(f"{customer_id}::{session_id}", {})

    def get_customer_realtime_features(self, *, customer_id: str) -> dict:
        payload = self._read_payload("customer_realtime_features.json")
        return payload.get(customer_id, {})

    def get_article_realtime_features(self, *, article_id: str) -> dict:
        payload = self._read_payload("article_realtime_features.json")
        return payload.get(article_id, {})

    def _read_payload(self, filename: str) -> dict:
        path = self.store_root / filename
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
