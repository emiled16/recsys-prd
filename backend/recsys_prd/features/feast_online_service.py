from __future__ import annotations

from time import perf_counter
from typing import Any

from feast import FeatureStore

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.observability.metrics import FEATURE_LOOKUP_LATENCY

SESSION_INTENT_FIELDS = (
    "recent_viewed_article_ids",
    "recent_clicked_article_ids",
    "recent_search_terms",
    "cart_add_count_30m",
    "wishlist_add_count_7d",
    "last_event_time",
)
CUSTOMER_REALTIME_FIELDS = (
    "purchase_count_30d_rt",
    "purchase_count_7d_rt",
    "days_since_last_purchase_rt",
    "cart_add_count_7d_rt",
    "wishlist_add_count_30d_rt",
)


class FeastOnlineFeatureService:
    """Fetch online retrieval context from Feast when the online store is available."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        store: Any | None = None,
    ) -> None:
        self.settings = settings or get_app_settings()
        self.store = store

    def get_session_intent_features(self, *, customer_id: str, session_id: str) -> dict[str, Any]:
        return self._get_online_features(
            feature_view="session_intent_features",
            field_names=SESSION_INTENT_FIELDS,
            entity_rows=[{"customer_session_id": f"{customer_id}::{session_id}"}],
        )

    def get_customer_realtime_features(self, *, customer_id: str) -> dict[str, Any]:
        return self._get_online_features(
            feature_view="customer_realtime_features",
            field_names=CUSTOMER_REALTIME_FIELDS,
            entity_rows=[{"customer_id": customer_id}],
        )

    def _get_online_features(
        self,
        *,
        feature_view: str,
        field_names: tuple[str, ...],
        entity_rows: list[dict[str, str]],
    ) -> dict[str, Any]:
        started_at = perf_counter()
        try:
            store = self.store or FeatureStore(repo_path=str(self.settings.paths.feast_repo_root))
            response = store.get_online_features(
                features=[f"{feature_view}:{field_name}" for field_name in field_names],
                entity_rows=entity_rows,
            )
        except Exception:
            return {}
        finally:
            entity_name = feature_view.removesuffix("_features").replace("_realtime", "")
            FEATURE_LOOKUP_LATENCY.labels(service="feast", entity=entity_name).observe(
                perf_counter() - started_at
            )

        payload = response.to_dict() if hasattr(response, "to_dict") else dict(response)
        features: dict[str, Any] = {}
        for field_name in field_names:
            values = payload.get(field_name, [])
            if not values:
                continue
            value = values[0]
            if value in ("", None):
                continue
            features[field_name] = value
        return features
