from __future__ import annotations

from datetime import datetime
from pathlib import Path

from recsys_prd.features.pit_state import (
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
from recsys_prd.io.csv_ops import read_csv_rows
from recsys_prd.io.json_ops import write_json
from recsys_prd.normalization.writer import write_dataset_bundle
from recsys_prd.paths import DATA_ROOT, NORMALIZED_ROOT


TRAINING_FIELDS = [
    "label_event_id",
    "label_timestamp",
    "customer_id",
    "article_id",
    "label_purchase",
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


def build_point_in_time_training_dataset(
    *,
    normalized_root: Path = NORMALIZED_ROOT,
    features_root: Path = DATA_ROOT / "features" / "offline",
) -> Path:
    """Build a leakage-safe point-in-time training dataset from normalized inputs."""
    customers = load_customer_profiles(normalized_root)
    products = load_product_catalog(normalized_root)
    image_presence = load_image_presence(normalized_root)
    transactions = read_csv_rows(normalized_root / "transactions" / "transactions_normalized.csv")
    ordered_transactions = sorted(transactions, key=lambda row: (row["event_time"], row["event_id"]))

    rows: list[dict[str, str]] = []
    customer_history: dict[str, HistoricalState] = {}
    article_history: dict[str, HistoricalState] = {}
    customer_article_history: dict[tuple[str, str], HistoricalState] = {}

    for transaction in ordered_transactions:
        label_time = datetime.strptime(transaction["event_time"], "%Y-%m-%dT%H:%M:%SZ")
        customer_id = transaction["customer_id"]
        article_id = transaction["article_id"]

        customer_events = customer_history.setdefault(customer_id, HistoricalState()).customer_events
        article_events = article_history.setdefault(article_id, HistoricalState()).article_events
        pair_key = (customer_id, article_id)
        pair_events = customer_article_history.setdefault(pair_key, HistoricalState()).customer_article_events

        customer_stats = build_customer_stats(customer_events, label_time)
        article_stats = build_article_stats(article_events, label_time)
        pair_stats = build_customer_article_stats(pair_events, label_time)

        customer = customers.get(customer_id, {})
        product = products.get(article_id, {})
        rows.append(
            _build_training_row(
                transaction=transaction,
                customer=customer,
                product=product,
                has_image=image_presence.get(article_id, False),
                customer_stats=customer_stats,
                article_stats=article_stats,
                pair_stats=pair_stats,
            )
        )

        event_record = {
            "event_time": label_time,
            "customer_id": customer_id,
            "article_id": article_id,
            "price": float(transaction["price"]) if transaction["price"] else 0.0,
        }
        customer_events.append(event_record)
        article_events.append(event_record)
        pair_events.append(event_record)

    dataset_path = write_dataset_bundle(
        dataset_dir=features_root / "training_dataset",
        dataset_filename="point_in_time_training_dataset.csv",
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


def _build_training_row(
    *,
    transaction: dict[str, str],
    customer: dict[str, str],
    product: dict[str, str],
    has_image: bool,
    customer_stats,
    article_stats,
    pair_stats,
) -> dict[str, str]:
    return {
        "label_event_id": transaction["event_id"],
        "label_timestamp": transaction["event_time"],
        "customer_id": transaction["customer_id"],
        "article_id": transaction["article_id"],
        "label_purchase": "1",
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
