from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import redis

from recsys_prd.config import AppSettings, get_app_settings
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


class RedisOnlineFeatureStore:
    """Persist online feature payloads in Redis JSON records."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        client: Any | None = None,
        key_prefix: str = "recsys_prd",
    ) -> None:
        self.settings = settings or get_app_settings()
        self.client = client or redis.Redis.from_url(self.settings.services.redis.url)
        self.key_prefix = key_prefix

    def put_session_features(
        self,
        customer_id: str,
        session_id: str,
        payload: dict[str, Any],
    ) -> None:
        self.client.set(self._session_key(customer_id, session_id), json.dumps(payload))

    def put_customer_features(self, customer_id: str, payload: dict[str, Any]) -> None:
        self.client.set(self._customer_key(customer_id), json.dumps(payload))

    def put_article_features(self, article_id: str, payload: dict[str, Any]) -> None:
        self.client.set(self._article_key(article_id), json.dumps(payload))

    def get_session_features(self, customer_id: str, session_id: str) -> dict[str, Any]:
        return self._read_json(self._session_key(customer_id, session_id))

    def get_customer_features(self, customer_id: str) -> dict[str, Any]:
        return self._read_json(self._customer_key(customer_id))

    def get_article_features(self, article_id: str) -> dict[str, Any]:
        return self._read_json(self._article_key(article_id))

    def probe(self) -> dict[str, Any]:
        return {"ok": bool(self.client.ping()), "url": self.settings.services.redis.url}

    def _session_key(self, customer_id: str, session_id: str) -> str:
        return f"{self.key_prefix}:session:{customer_id}::{session_id}"

    def _customer_key(self, customer_id: str) -> str:
        return f"{self.key_prefix}:customer:{customer_id}"

    def _article_key(self, article_id: str) -> str:
        return f"{self.key_prefix}:article:{article_id}"

    def _read_json(self, key: str) -> dict[str, Any]:
        value = self.client.get(key)
        if not value:
            return {}
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return json.loads(value)
