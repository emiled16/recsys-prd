from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.features.online_store import RedisOnlineFeatureStore


class OnlineFeatureService:
    """Read online feature payloads from the local file-backed serving store."""

    def __init__(
        self,
        store_root: Path | None = None,
        settings: AppSettings | None = None,
        store: Any | None = None,
    ) -> None:
        settings = settings or get_app_settings()
        self.store_root = store_root
        self.store = store or (
            RedisOnlineFeatureStore(settings=settings) if store_root is None else None
        )

    def get_session_intent_features(self, *, customer_id: str, session_id: str) -> dict:
        if self.store is not None:
            return self.store.get_session_features(customer_id, session_id)
        payload = self._read_payload("session_intent_features.json")
        return payload.get(f"{customer_id}::{session_id}", {})

    def get_customer_realtime_features(self, *, customer_id: str) -> dict:
        if self.store is not None:
            return self.store.get_customer_features(customer_id)
        payload = self._read_payload("customer_realtime_features.json")
        return payload.get(customer_id, {})

    def get_article_realtime_features(self, *, article_id: str) -> dict:
        if self.store is not None:
            return self.store.get_article_features(article_id)
        payload = self._read_payload("article_realtime_features.json")
        return payload.get(article_id, {})

    def _read_payload(self, filename: str) -> dict:
        path = self.store_root / filename
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))
