from __future__ import annotations

from datetime import datetime
from pathlib import Path

from recsys_prd.events.io import read_jsonl
from recsys_prd.features.online_state import (
    empty_online_state,
    trim_event_pairs,
    trim_times,
)
from recsys_prd.features.online_store import write_online_store
from recsys_prd.paths import DATA_ROOT


def compute_online_feature_store(
    *,
    events_root: Path = DATA_ROOT / "events",
    store_root: Path = DATA_ROOT / "features" / "online_bootstrap",
) -> dict[str, Path]:
    """Compute local online feature snapshots from replayed events."""
    replay_dir = events_root / "replay_batches"
    interaction_events = read_jsonl(replay_dir / "interaction_events.jsonl")
    catalog_events = read_jsonl(replay_dir / "catalog_events.jsonl")
    state = empty_online_state()

    for event in sorted(interaction_events + catalog_events, key=_event_sort_key):
        _apply_event(state, event)

    session_features = _build_session_features(state["sessions"])
    customer_features = _build_customer_features(state["customers"])
    article_features = _build_article_features(state["articles"])
    return write_online_store(
        store_root=store_root,
        session_features=session_features,
        customer_features=customer_features,
        article_features=article_features,
    )


def _apply_event(state: dict[str, dict], event: dict) -> None:
    event_type = event["event_type"]
    event_time = _parse_time(event["event_time"])

    if event_type in {"product_view", "product_click", "add_to_cart", "wishlist_add", "search_query"}:
        session_key = _session_key(event["customer_id"], event["session_id"])
        session_state = state["sessions"][session_key]
        session_state.last_event_time = event_time
        if event_type == "product_view":
            session_state.viewed.append((event_time, event["article_id"]))
        elif event_type == "product_click":
            session_state.clicked.append((event_time, event["article_id"]))
        elif event_type == "search_query":
            session_state.searches.append((event_time, event.get("query_text", "")))
        elif event_type == "add_to_cart":
            session_state.cart_adds.append(event_time)
        elif event_type == "wishlist_add":
            session_state.wishlist_adds.append(event_time)

    if event_type in {"purchase", "add_to_cart", "wishlist_add"}:
        customer_state = state["customers"][event["customer_id"]]
        if event_type == "purchase":
            customer_state.purchases.append(event_time)
        elif event_type == "add_to_cart":
            customer_state.cart_adds.append(event_time)
        elif event_type == "wishlist_add":
            customer_state.wishlist_adds.append(event_time)

    if event_type in {"purchase", "inventory_update", "price_change", "product_metadata_update"}:
        article_state = state["articles"][event["article_id"]]
        if event_type == "purchase":
            article_state.purchases.append((event_time, event.get("price", "")))
        if event_type == "inventory_update":
            inventory_level = event.get("inventory_level", "")
            article_state.inventory_level = int(inventory_level) if inventory_level else 0
            article_state.last_catalog_update = event_time
        if event_type == "price_change":
            new_price = event.get("new_price", "")
            article_state.current_price = float(new_price) if new_price else article_state.current_price
            article_state.last_catalog_update = event_time
        if event_type == "product_metadata_update":
            article_state.last_catalog_update = event_time


def _build_session_features(sessions: dict[str, object]) -> dict[str, dict]:
    output: dict[str, dict] = {}
    for key, session in sessions.items():
        if session.last_event_time is None:
            continue
        viewed = trim_event_pairs(session.viewed, session.last_event_time, days=7)
        clicked = trim_event_pairs(session.clicked, session.last_event_time, days=7)
        searches = trim_event_pairs(session.searches, session.last_event_time, days=7)
        cart_adds = trim_times(session.cart_adds, session.last_event_time, minutes=30)
        wishlist_adds = trim_times(session.wishlist_adds, session.last_event_time, days=7)
        output[key] = {
            "recent_viewed_article_ids": [article_id for _, article_id in viewed[-5:]],
            "recent_clicked_article_ids": [article_id for _, article_id in clicked[-5:]],
            "recent_search_terms": [query for _, query in searches[-5:] if query],
            "cart_add_count_30m": len(cart_adds),
            "wishlist_add_count_7d": len(wishlist_adds),
            "last_event_time": session.last_event_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    return output


def _build_customer_features(customers: dict[str, object]) -> dict[str, dict]:
    output: dict[str, dict] = {}
    for customer_id, customer in customers.items():
        reference_time = _latest_time(customer.purchases + customer.cart_adds + customer.wishlist_adds)
        if reference_time is None:
            continue
        purchases_30d = trim_times(customer.purchases, reference_time, days=30)
        purchases_7d = trim_times(customer.purchases, reference_time, days=7)
        cart_adds_7d = trim_times(customer.cart_adds, reference_time, days=7)
        wishlist_adds_30d = trim_times(customer.wishlist_adds, reference_time, days=30)
        last_purchase = customer.purchases[-1] if customer.purchases else None
        output[customer_id] = {
            "purchase_count_30d_rt": len(purchases_30d),
            "purchase_count_7d_rt": len(purchases_7d),
            "days_since_last_purchase_rt": (
                (reference_time - last_purchase).days if last_purchase else -1
            ),
            "cart_add_count_7d_rt": len(cart_adds_7d),
            "wishlist_add_count_30d_rt": len(wishlist_adds_30d),
        }
    return output


def _build_article_features(articles: dict[str, object]) -> dict[str, dict]:
    output: dict[str, dict] = {}
    for article_id, article in articles.items():
        purchase_times = [event_time for event_time, _ in article.purchases]
        purchase_reference = _latest_time(purchase_times)
        catalog_reference = article.last_catalog_update
        reference_time = _latest_time([time for time in [purchase_reference, catalog_reference] if time])
        if reference_time is None:
            continue
        purchase_count_1d = len(trim_times(purchase_times, reference_time, days=1))
        purchase_count_7d = len(trim_times(purchase_times, reference_time, days=7))
        output[article_id] = {
            "purchase_count_1d_rt": purchase_count_1d,
            "purchase_count_7d_rt": purchase_count_7d,
            "inventory_level_rt": article.inventory_level,
            "is_in_stock_rt": article.inventory_level > 0,
            "current_price_rt": article.current_price,
            "minutes_since_last_catalog_update": (
                int((reference_time - article.last_catalog_update).total_seconds() / 60)
                if article.last_catalog_update
                else -1
            ),
        }
    return output


def _parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def _event_sort_key(event: dict) -> tuple[str, str]:
    return event["event_time"], event["event_id"]


def _session_key(customer_id: str, session_id: str) -> str:
    return f"{customer_id}::{session_id}"


def _latest_time(times: list[datetime]) -> datetime | None:
    return max(times) if times else None
