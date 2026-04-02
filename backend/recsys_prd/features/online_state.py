from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class SessionState:
    viewed: list[tuple[datetime, str]] = field(default_factory=list)
    clicked: list[tuple[datetime, str]] = field(default_factory=list)
    searches: list[tuple[datetime, str]] = field(default_factory=list)
    cart_adds: list[datetime] = field(default_factory=list)
    wishlist_adds: list[datetime] = field(default_factory=list)
    last_event_time: datetime | None = None


@dataclass
class CustomerRealtimeState:
    purchases: list[datetime] = field(default_factory=list)
    cart_adds: list[datetime] = field(default_factory=list)
    wishlist_adds: list[datetime] = field(default_factory=list)


@dataclass
class ArticleRealtimeState:
    purchases: list[tuple[datetime, str]] = field(default_factory=list)
    inventory_level: int = 0
    current_price: float = 0.0
    last_catalog_update: datetime | None = None


def empty_online_state() -> dict[str, dict]:
    """Return mutable containers for online feature computation."""
    return {
        "sessions": defaultdict(SessionState),
        "customers": defaultdict(CustomerRealtimeState),
        "articles": defaultdict(ArticleRealtimeState),
    }


def trim_times(times: list[datetime], reference_time: datetime, *, days: int = 0, minutes: int = 0) -> list[datetime]:
    """Keep only timestamps within the trailing window."""
    lower_bound = reference_time - timedelta(days=days, minutes=minutes)
    return [value for value in times if value >= lower_bound]


def trim_event_pairs(
    pairs: list[tuple[datetime, str]],
    reference_time: datetime,
    *,
    days: int = 0,
    minutes: int = 0,
) -> list[tuple[datetime, str]]:
    """Keep only timestamped values within the trailing window."""
    lower_bound = reference_time - timedelta(days=days, minutes=minutes)
    return [pair for pair in pairs if pair[0] >= lower_bound]
