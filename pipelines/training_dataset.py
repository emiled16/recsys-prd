from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TypeAlias

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.features.pit_state import (
    ArticleStats,
    CustomerArticleStats,
    CustomerStats,
    HistoricalState,
    build_article_stats,
    build_customer_article_stats,
    build_customer_stats,
)
from recsys_prd.features.static_lookups import (
    load_customer_profiles,
    load_image_presence,
    load_product_catalog,
)
from recsys_prd.io.json_ops import write_json
from recsys_prd.io.tabular_ops import read_tabular_rows
from pipelines.normalization.writer import write_dataset_bundle

StaticLookupMap: TypeAlias = dict[str, dict[str, str]]
ImagePresenceMap: TypeAlias = dict[str, bool]
HistoryMap: TypeAlias = dict[str, HistoricalState]
PairHistoryMap: TypeAlias = dict[tuple[str, str], HistoricalState]

TRAINING_FEATURE_FIELDS = [
    "customer_age",
    "customer_club_member_status",
    "customer_fashion_news_frequency",
    "customer_has_fn_flag",
    "customer_has_active_flag",
    "article_product_type_name",
    "article_product_group_name",
    "article_colour_group_name",
    "article_department_name",
    "article_index_group_name",
    "article_has_detail_desc",
    "article_has_image",
    "customer_purchase_count_30d",
    "customer_purchase_count_all_time",
    "customer_days_since_last_purchase",
    "customer_distinct_articles_purchased_30d",
    "customer_avg_purchase_price_30d",
    "article_purchase_count_7d",
    "article_purchase_count_30d",
    "article_unique_customers_30d",
    "article_avg_article_price_30d",
    "article_days_since_last_article_purchase",
    "customer_article_historical_purchase_count",
    "customer_article_days_since_last_purchase",
    "customer_article_has_purchased_before",
    "customer_article_last_purchase_price",
]

TRAINING_FIELDS = [
    "label_event_id",
    "label_timestamp",
    "customer_id",
    "article_id",
    "label_purchase",
    *TRAINING_FEATURE_FIELDS,
]


def build_point_in_time_training_dataset(
    *,
    normalized_root: Path | None = None,
    features_root: Path | None = None,
    settings: AppSettings | None = None,
) -> Path:
    """Build a leakage-safe point-in-time training dataset from normalized inputs."""
    settings = settings or get_app_settings()
    normalized_root = normalized_root or settings.paths.normalized_root
    features_root = features_root or settings.paths.features_offline_root
    customers, products, image_presence, ordered_transactions = load_training_inputs(
        normalized_root
    )

    rows: list[dict[str, str]] = []
    customer_history: HistoryMap = {}
    article_history: HistoryMap = {}
    customer_article_history: PairHistoryMap = {}

    for transaction in ordered_transactions:
        rows.append(
            build_point_in_time_feature_row(
                transaction=transaction,
                candidate_article_id=transaction["article_id"],
                customers=customers,
                products=products,
                image_presence=image_presence,
                customer_history=customer_history,
                article_history=article_history,
                customer_article_history=customer_article_history,
            )
        )
        record_transaction_history(
            transaction=transaction,
            customer_history=customer_history,
            article_history=article_history,
            customer_article_history=customer_article_history,
        )

    dataset_path = write_dataset_bundle(
        dataset_dir=features_root / "training_dataset",
        dataset_filename="point_in_time_training_dataset.parquet",
        fieldnames=TRAINING_FIELDS,
        rows=rows,
        primary_key="label_event_id",
    )
    write_json(
        features_root / "training_dataset" / "join_manifest.json",
        {
            "label_source": "transactions_normalized",
            "ordering": "event_time,event_id",
            "history_rule": "strictly_before_label_time",
            "row_count": len(rows),
        },
    )
    return dataset_path


def load_training_inputs(
    normalized_root: Path,
) -> tuple[StaticLookupMap, StaticLookupMap, ImagePresenceMap, list[dict[str, str]]]:
    """Load the normalized lookups and transaction labels needed for PIT dataset builders."""
    customers = load_customer_profiles(normalized_root)
    products = load_product_catalog(normalized_root)
    image_presence = load_image_presence(normalized_root)
    transactions = read_tabular_rows(
        normalized_root / "transactions" / "transactions_normalized.parquet"
    )
    ordered_transactions = sorted(
        transactions,
        key=lambda row: (row["event_time"], row["event_id"]),
    )
    return customers, products, image_presence, ordered_transactions


def build_point_in_time_feature_row(
    *,
    transaction: dict[str, str],
    candidate_article_id: str,
    customers: StaticLookupMap,
    products: StaticLookupMap,
    image_presence: ImagePresenceMap,
    customer_history: HistoryMap,
    article_history: HistoryMap,
    customer_article_history: PairHistoryMap,
) -> dict[str, str]:
    """Build one leakage-safe feature row for a customer/article pair at the label time."""
    label_time = parse_event_time(transaction["event_time"])
    customer_id = transaction["customer_id"]
    customer_events = customer_history.setdefault(customer_id, HistoricalState()).customer_events
    article_events = article_history.setdefault(
        candidate_article_id,
        HistoricalState(),
    ).article_events
    pair_key = (customer_id, candidate_article_id)
    pair_events = customer_article_history.setdefault(
        pair_key,
        HistoricalState(),
    ).customer_article_events

    customer_stats = build_customer_stats(customer_events, label_time)
    article_stats = build_article_stats(article_events, label_time)
    pair_stats = build_customer_article_stats(pair_events, label_time)
    customer = customers.get(customer_id, {})
    product = products.get(candidate_article_id, {})

    return {
        "label_event_id": transaction["event_id"],
        "label_timestamp": transaction["event_time"],
        "customer_id": customer_id,
        "article_id": candidate_article_id,
        "label_purchase": "1" if transaction["article_id"] == candidate_article_id else "0",
        **serialize_feature_values(
            customer=customer,
            product=product,
            has_image=image_presence.get(candidate_article_id, False),
            customer_stats=customer_stats,
            article_stats=article_stats,
            pair_stats=pair_stats,
        ),
    }


def serialize_feature_values(
    *,
    customer: dict[str, str],
    product: dict[str, str],
    has_image: bool,
    customer_stats: CustomerStats,
    article_stats: ArticleStats,
    pair_stats: CustomerArticleStats,
) -> dict[str, str]:
    """Serialize static and historical feature values into the shared training schema."""
    return {
        "customer_age": customer.get("age", ""),
        "customer_club_member_status": customer.get("club_member_status", ""),
        "customer_fashion_news_frequency": customer.get("fashion_news_frequency", ""),
        "customer_has_fn_flag": "1" if customer.get("fn_flag", "") else "0",
        "customer_has_active_flag": "1" if customer.get("active_flag", "") else "0",
        "article_product_type_name": product.get("product_type_name", ""),
        "article_product_group_name": product.get("product_group_name", ""),
        "article_colour_group_name": product.get("colour_group_name", ""),
        "article_department_name": product.get("department_name", ""),
        "article_index_group_name": product.get("index_group_name", ""),
        "article_has_detail_desc": "1" if product.get("detail_desc", "") else "0",
        "article_has_image": "1" if has_image else "0",
        "customer_purchase_count_30d": str(customer_stats.purchase_count_30d),
        "customer_purchase_count_all_time": str(customer_stats.purchase_count_all_time),
        "customer_days_since_last_purchase": str(customer_stats.days_since_last_purchase),
        "customer_distinct_articles_purchased_30d": str(customer_stats.distinct_articles_30d),
        "customer_avg_purchase_price_30d": f"{customer_stats.avg_purchase_price_30d:.2f}",
        "article_purchase_count_7d": str(article_stats.purchase_count_7d),
        "article_purchase_count_30d": str(article_stats.purchase_count_30d),
        "article_unique_customers_30d": str(article_stats.unique_customers_30d),
        "article_avg_article_price_30d": f"{article_stats.avg_article_price_30d:.2f}",
        "article_days_since_last_article_purchase": str(
            article_stats.days_since_last_article_purchase
        ),
        "customer_article_historical_purchase_count": str(pair_stats.historical_purchase_count),
        "customer_article_days_since_last_purchase": str(pair_stats.days_since_last_purchase),
        "customer_article_has_purchased_before": str(pair_stats.has_purchased_before),
        "customer_article_last_purchase_price": f"{pair_stats.last_purchase_price:.2f}",
    }


def record_transaction_history(
    *,
    transaction: dict[str, str],
    customer_history: HistoryMap,
    article_history: HistoryMap,
    customer_article_history: PairHistoryMap,
) -> None:
    """Append one normalized transaction into the PIT state stores."""
    label_time = parse_event_time(transaction["event_time"])
    customer_id = transaction["customer_id"]
    article_id = transaction["article_id"]
    event_record = {
        "event_time": label_time,
        "customer_id": customer_id,
        "article_id": article_id,
        "price": float(transaction["price"]) if transaction["price"] else 0.0,
    }
    customer_history.setdefault(customer_id, HistoricalState()).customer_events.append(event_record)
    article_history.setdefault(article_id, HistoricalState()).article_events.append(event_record)
    customer_article_history.setdefault(
        (customer_id, article_id),
        HistoricalState(),
    ).customer_article_events.append(event_record)


def recent_seed_article_ids(
    customer_history: HistoryMap,
    *,
    customer_id: str,
    limit: int,
) -> tuple[str, ...]:
    """Return the most recent distinct article IDs seen for the customer before the label time."""
    customer_events = customer_history.get(customer_id, HistoricalState()).customer_events
    seed_article_ids: list[str] = []
    seen_article_ids: set[str] = set()
    for event in reversed(customer_events):
        article_id = event["article_id"]
        if article_id in seen_article_ids:
            continue
        seed_article_ids.append(article_id)
        seen_article_ids.add(article_id)
        if len(seed_article_ids) >= limit:
            break
    return tuple(seed_article_ids)


def parse_event_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
