from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

from recsys_prd.io.event_ids import build_event_id
from recsys_prd.io.tabular_ops import read_tabular_rows


def generate_interaction_events(normalized_root: Path) -> list[dict]:
    """Generate deterministic interaction events from normalized transactions."""
    transactions = read_tabular_rows(
        normalized_root / "transactions" / "transactions_normalized.parquet"
    )
    products = read_tabular_rows(normalized_root / "products" / "products_normalized.parquet")
    product_lookup = {row["article_id"]: row for row in products}

    events: list[dict] = []
    for index, transaction in enumerate(transactions, start=1):
        base_time = datetime.strptime(transaction["event_time"], "%Y-%m-%dT%H:%M:%SZ")
        customer_id = transaction["customer_id"]
        article_id = transaction["article_id"]
        product = product_lookup.get(article_id, {})
        session_id = f"{customer_id}-{transaction['event_time'][:10]}"
        query_text = _build_query_text(product)

        events.extend(
            [
                _interaction_event(
                    event_type="product_view",
                    event_time=base_time - timedelta(minutes=15),
                    customer_id=customer_id,
                    session_id=session_id,
                    article_id=article_id,
                    source="synthetic_transaction_replay",
                    ordinal=f"{index}-view",
                ),
                _interaction_event(
                    event_type="product_click",
                    event_time=base_time - timedelta(minutes=10),
                    customer_id=customer_id,
                    session_id=session_id,
                    article_id=article_id,
                    source="synthetic_transaction_replay",
                    ordinal=f"{index}-click",
                ),
                _interaction_event(
                    event_type="add_to_cart",
                    event_time=base_time - timedelta(minutes=5),
                    customer_id=customer_id,
                    session_id=session_id,
                    article_id=article_id,
                    source="synthetic_transaction_replay",
                    ordinal=f"{index}-cart",
                ),
                _interaction_event(
                    event_type="purchase",
                    event_time=base_time,
                    customer_id=customer_id,
                    session_id=session_id,
                    article_id=article_id,
                    source="historical_transaction",
                    ordinal=f"{index}-purchase",
                    price=transaction["price"],
                ),
                _interaction_event(
                    event_type="search_query",
                    event_time=base_time - timedelta(minutes=20),
                    customer_id=customer_id,
                    session_id=session_id,
                    article_id="",
                    source="synthetic_query_inference",
                    ordinal=f"{index}-search",
                    query_text=query_text,
                ),
            ]
        )

    return sorted(events, key=lambda event: (event["event_time"], event["event_id"]))


def _interaction_event(
    *,
    event_type: str,
    event_time: datetime,
    customer_id: str,
    session_id: str,
    article_id: str,
    source: str,
    ordinal: str,
    price: str = "",
    query_text: str = "",
) -> dict:
    event_time_str = event_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "event_id": build_event_id(event_type, customer_id, session_id, article_id, ordinal),
        "event_type": event_type,
        "event_time": event_time_str,
        "customer_id": customer_id,
        "session_id": session_id,
        "article_id": article_id,
        "price": price,
        "query_text": query_text,
        "source": source,
    }


def _build_query_text(product: dict[str, str]) -> str:
    tokens = [product.get("product_type_name", ""), product.get("colour_group_name", "")]
    return " ".join(token for token in tokens if token).strip()
