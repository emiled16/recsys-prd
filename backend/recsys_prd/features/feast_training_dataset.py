from __future__ import annotations

from pathlib import Path

import pandas as pd
from feast import FeatureStore

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.features.feast_store import feast_repo_objects
from recsys_prd.features.training_dataset import TRAINING_FIELDS, load_training_inputs
from recsys_prd.io.json_ops import write_json
from recsys_prd.normalization.writer import write_dataset_bundle

FEAST_FEATURE_REFS = [
    "customer_profile_features:age",
    "customer_profile_features:club_member_status",
    "customer_profile_features:fashion_news_frequency",
    "customer_profile_features:has_fn_flag",
    "customer_profile_features:has_active_flag",
    "article_catalog_features:product_type_name",
    "article_catalog_features:product_group_name",
    "article_catalog_features:colour_group_name",
    "article_catalog_features:department_name",
    "article_catalog_features:index_group_name",
    "article_catalog_features:has_detail_desc",
    "article_catalog_features:has_image",
    "customer_activity_features:purchase_count_30d",
    "customer_activity_features:purchase_count_all_time",
    "customer_activity_features:days_since_last_purchase",
    "customer_activity_features:distinct_articles_purchased_30d",
    "customer_activity_features:avg_purchase_price_30d",
    "article_demand_features:purchase_count_7d",
    "article_demand_features:purchase_count_30d",
    "article_demand_features:unique_customers_30d",
    "article_demand_features:avg_article_price_30d",
    "article_demand_features:days_since_last_article_purchase",
    "customer_article_affinity_features:historical_purchase_count",
    "customer_article_affinity_features:days_since_last_purchase",
    "customer_article_affinity_features:has_purchased_before",
    "customer_article_affinity_features:last_purchase_price",
]

FEAST_TO_TRAINING_FIELD = {
    "customer_profile_features__age": "customer_age",
    "customer_profile_features__club_member_status": "customer_club_member_status",
    "customer_profile_features__fashion_news_frequency": "customer_fashion_news_frequency",
    "customer_profile_features__has_fn_flag": "customer_has_fn_flag",
    "customer_profile_features__has_active_flag": "customer_has_active_flag",
    "article_catalog_features__product_type_name": "article_product_type_name",
    "article_catalog_features__product_group_name": "article_product_group_name",
    "article_catalog_features__colour_group_name": "article_colour_group_name",
    "article_catalog_features__department_name": "article_department_name",
    "article_catalog_features__index_group_name": "article_index_group_name",
    "article_catalog_features__has_detail_desc": "article_has_detail_desc",
    "article_catalog_features__has_image": "article_has_image",
    "customer_activity_features__purchase_count_30d": "customer_purchase_count_30d",
    "customer_activity_features__purchase_count_all_time": "customer_purchase_count_all_time",
    "customer_activity_features__days_since_last_purchase": "customer_days_since_last_purchase",
    "customer_activity_features__distinct_articles_purchased_30d": (
        "customer_distinct_articles_purchased_30d"
    ),
    "customer_activity_features__avg_purchase_price_30d": "customer_avg_purchase_price_30d",
    "article_demand_features__purchase_count_7d": "article_purchase_count_7d",
    "article_demand_features__purchase_count_30d": "article_purchase_count_30d",
    "article_demand_features__unique_customers_30d": "article_unique_customers_30d",
    "article_demand_features__avg_article_price_30d": "article_avg_article_price_30d",
    "article_demand_features__days_since_last_article_purchase": (
        "article_days_since_last_article_purchase"
    ),
    "customer_article_affinity_features__historical_purchase_count": (
        "customer_article_historical_purchase_count"
    ),
    "customer_article_affinity_features__days_since_last_purchase": (
        "customer_article_days_since_last_purchase"
    ),
    "customer_article_affinity_features__has_purchased_before": (
        "customer_article_has_purchased_before"
    ),
    "customer_article_affinity_features__last_purchase_price": (
        "customer_article_last_purchase_price"
    ),
}


class FeastPointInTimeDatasetBuilder:
    """Build PIT training rows through Feast historical retrieval."""

    def __init__(
        self,
        *,
        settings: AppSettings | None = None,
        store: FeatureStore | None = None,
    ) -> None:
        self.settings = settings or get_app_settings()
        self.store = store

    def build(
        self,
        *,
        normalized_root: Path | None = None,
        features_root: Path | None = None,
    ) -> Path:
        normalized_root = normalized_root or self.settings.paths.normalized_root
        features_root = features_root or self.settings.paths.features_offline_root
        _, _, _, ordered_transactions = load_training_inputs(normalized_root)

        entity_df = pd.DataFrame(
            [
                {
                    "event_timestamp": transaction["event_time"],
                    "customer_id": transaction["customer_id"],
                    "article_id": transaction["article_id"],
                }
                for transaction in ordered_transactions
            ]
        )
        store = self._feature_store()
        retrieval_job = store.get_historical_features(
            entity_df=entity_df,
            features=FEAST_FEATURE_REFS,
            full_feature_names=True,
        )
        retrieved_rows = retrieval_job.to_df().fillna("").to_dict(orient="records")
        if len(retrieved_rows) != len(ordered_transactions):
            raise ValueError("Feast historical retrieval row count does not match label rows.")

        rows = [
            self._build_training_row(transaction=transaction, feast_row=feast_row)
            for transaction, feast_row in zip(ordered_transactions, retrieved_rows, strict=True)
        ]

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
                "join_engine": "feast_historical_retrieval",
                "feature_refs": FEAST_FEATURE_REFS,
                "row_count": len(rows),
            },
        )
        return dataset_path

    def _feature_store(self) -> FeatureStore:
        if self.store is not None:
            return self.store
        store = FeatureStore(repo_path=str(self.settings.paths.feast_repo_root))
        store.apply(objects=feast_repo_objects(), partial=False)
        return store

    def _build_training_row(
        self,
        *,
        transaction: dict[str, str],
        feast_row: dict[str, object],
    ) -> dict[str, str]:
        feature_values = {
            training_field: self._stringify(feast_row.get(feast_field, ""))
            for feast_field, training_field in FEAST_TO_TRAINING_FIELD.items()
        }
        return {
            "label_event_id": transaction["event_id"],
            "label_timestamp": transaction["event_time"],
            "customer_id": transaction["customer_id"],
            "article_id": transaction["article_id"],
            "label_purchase": "1",
            **feature_values,
        }

    @staticmethod
    def _stringify(value: object) -> str:
        return "" if value is None else str(value)
