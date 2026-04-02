from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CustomerStats:
    purchase_count_all_time: int = 0
    purchase_count_30d: int = 0
    distinct_articles_30d: int = 0
    avg_purchase_price_30d: float = 0.0
    days_since_last_purchase: int = -1


@dataclass
class ArticleStats:
    purchase_count_7d: int = 0
    purchase_count_30d: int = 0
    unique_customers_30d: int = 0
    avg_article_price_30d: float = 0.0
    days_since_last_article_purchase: int = -1


@dataclass
class CustomerArticleStats:
    historical_purchase_count: int = 0
    days_since_last_purchase: int = -1
    has_purchased_before: int = 0
    last_purchase_price: float = 0.0


@dataclass
class HistoricalState:
    customer_events: list[dict] = field(default_factory=list)
    article_events: list[dict] = field(default_factory=list)
    customer_article_events: list[dict] = field(default_factory=list)


def build_customer_stats(events: list[dict], label_time: datetime) -> CustomerStats:
    """Build customer aggregates using history strictly before the label time."""
    if not events:
        return CustomerStats()
    trailing_30d = _filter_window(events, label_time, days=30)
    last_event = events[-1]
    prices = [event["price"] for event in trailing_30d]
    distinct_articles = {event["article_id"] for event in trailing_30d}
    return CustomerStats(
        purchase_count_all_time=len(events),
        purchase_count_30d=len(trailing_30d),
        distinct_articles_30d=len(distinct_articles),
        avg_purchase_price_30d=(sum(prices) / len(prices) if prices else 0.0),
        days_since_last_purchase=(label_time - last_event["event_time"]).days,
    )


def build_article_stats(events: list[dict], label_time: datetime) -> ArticleStats:
    """Build article demand aggregates using history strictly before the label time."""
    if not events:
        return ArticleStats()
    trailing_7d = _filter_window(events, label_time, days=7)
    trailing_30d = _filter_window(events, label_time, days=30)
    prices = [event["price"] for event in trailing_30d]
    unique_customers = {event["customer_id"] for event in trailing_30d}
    last_event = events[-1]
    return ArticleStats(
        purchase_count_7d=len(trailing_7d),
        purchase_count_30d=len(trailing_30d),
        unique_customers_30d=len(unique_customers),
        avg_article_price_30d=(sum(prices) / len(prices) if prices else 0.0),
        days_since_last_article_purchase=(label_time - last_event["event_time"]).days,
    )


def build_customer_article_stats(events: list[dict], label_time: datetime) -> CustomerArticleStats:
    """Build customer-article affinity aggregates using history before the label time."""
    if not events:
        return CustomerArticleStats()
    last_event = events[-1]
    return CustomerArticleStats(
        historical_purchase_count=len(events),
        days_since_last_purchase=(label_time - last_event["event_time"]).days,
        has_purchased_before=1,
        last_purchase_price=last_event["price"],
    )


def _filter_window(events: list[dict], label_time: datetime, *, days: int) -> list[dict]:
    lower_bound = label_time.timestamp() - (days * 24 * 60 * 60)
    return [
        event
        for event in events
        if event["event_time"].timestamp() >= lower_bound
    ]
