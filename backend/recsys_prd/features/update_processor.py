from __future__ import annotations

from typing import Any

from recsys_prd.features.online_state import empty_online_state, trim_event_pairs, trim_times
from recsys_prd.features.streaming_features import _apply_event, _latest_time, _session_key
from recsys_prd.schemas.artifacts import FeatureStoreWriteRecord


class FeatureUpdateProcessor:
    """Convert one broker event into online feature store writes."""

    def __init__(self) -> None:
        self.state = empty_online_state()

    def apply(self, event: dict[str, Any]) -> list[FeatureStoreWriteRecord]:
        _apply_event(self.state, event)
        writes: list[FeatureStoreWriteRecord] = []
        event_type = event["event_type"]

        if event_type in {
            "product_view",
            "product_click",
            "add_to_cart",
            "wishlist_add",
            "search_query",
        }:
            writes.append(self._build_session_write(event))
        if event_type in {"purchase", "add_to_cart", "wishlist_add"}:
            writes.append(self._build_customer_write(event))
        if event_type in {
            "purchase",
            "inventory_update",
            "price_change",
            "product_metadata_update",
        }:
            writes.append(self._build_article_write(event))
        return writes

    def _build_session_write(self, event: dict[str, Any]) -> FeatureStoreWriteRecord:
        key = _session_key(event["customer_id"], event["session_id"])
        session = self.state["sessions"][key]
        viewed = trim_event_pairs(session.viewed, session.last_event_time, days=7)
        clicked = trim_event_pairs(session.clicked, session.last_event_time, days=7)
        searches = trim_event_pairs(session.searches, session.last_event_time, days=7)
        cart_adds = trim_times(session.cart_adds, session.last_event_time, minutes=30)
        wishlist_adds = trim_times(session.wishlist_adds, session.last_event_time, days=7)
        return FeatureStoreWriteRecord(
            entity_type="session",
            entity_key=key,
            feature_view="session_intent_features",
            event_id=event["event_id"],
            event_time=event["event_time"],
            payload={
                "recent_viewed_article_ids": [article_id for _, article_id in viewed[-5:]],
                "recent_clicked_article_ids": [article_id for _, article_id in clicked[-5:]],
                "recent_search_terms": [query for _, query in searches[-5:] if query],
                "cart_add_count_30m": len(cart_adds),
                "wishlist_add_count_7d": len(wishlist_adds),
                "last_event_time": session.last_event_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )

    def _build_customer_write(self, event: dict[str, Any]) -> FeatureStoreWriteRecord:
        customer = self.state["customers"][event["customer_id"]]
        reference_time = _latest_time(
            customer.purchases + customer.cart_adds + customer.wishlist_adds
        )
        purchases_30d = trim_times(customer.purchases, reference_time, days=30)
        purchases_7d = trim_times(customer.purchases, reference_time, days=7)
        cart_adds_7d = trim_times(customer.cart_adds, reference_time, days=7)
        wishlist_adds_30d = trim_times(customer.wishlist_adds, reference_time, days=30)
        last_purchase = customer.purchases[-1] if customer.purchases else None
        return FeatureStoreWriteRecord(
            entity_type="customer",
            entity_key=event["customer_id"],
            feature_view="customer_realtime_features",
            event_id=event["event_id"],
            event_time=event["event_time"],
            payload={
                "purchase_count_30d_rt": len(purchases_30d),
                "purchase_count_7d_rt": len(purchases_7d),
                "days_since_last_purchase_rt": (
                    (reference_time - last_purchase).days if last_purchase else -1
                ),
                "cart_add_count_7d_rt": len(cart_adds_7d),
                "wishlist_add_count_30d_rt": len(wishlist_adds_30d),
            },
        )

    def _build_article_write(self, event: dict[str, Any]) -> FeatureStoreWriteRecord:
        article = self.state["articles"][event["article_id"]]
        purchase_times = [event_time for event_time, _ in article.purchases]
        purchase_reference = _latest_time(purchase_times)
        catalog_reference = article.last_catalog_update
        reference_time = _latest_time(
            [time for time in [purchase_reference, catalog_reference] if time]
        )
        return FeatureStoreWriteRecord(
            entity_type="article",
            entity_key=event["article_id"],
            feature_view="article_realtime_features",
            event_id=event["event_id"],
            event_time=event["event_time"],
            payload={
                "purchase_count_1d_rt": len(trim_times(purchase_times, reference_time, days=1)),
                "purchase_count_7d_rt": len(trim_times(purchase_times, reference_time, days=7)),
                "inventory_level_rt": article.inventory_level,
                "is_in_stock_rt": article.inventory_level > 0,
                "current_price_rt": article.current_price,
                "minutes_since_last_catalog_update": (
                    int((reference_time - article.last_catalog_update).total_seconds() / 60)
                    if article.last_catalog_update
                    else -1
                ),
            },
        )
