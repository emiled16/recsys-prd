from __future__ import annotations

import unittest
from pathlib import Path

from recsys_prd.config import PathSettings


class FeastRepoTests(unittest.TestCase):
    def test_feature_store_yaml_exists_with_local_provider(self) -> None:
        repo_root = Path(__file__).resolve().parents[2] / "feast_repo"
        yaml_text = (repo_root / "feature_store.yaml").read_text(encoding="utf-8")

        self.assertIn("project: recsys_prd", yaml_text)
        self.assertIn("provider: local", yaml_text)
        self.assertIn("type: redis", yaml_text)

    def test_sources_point_to_expected_parquet_artifacts(self) -> None:
        from feast_repo import sources

        path_settings = PathSettings()
        customers_path = (
            path_settings.normalized_root / "customers" / "customers_normalized.parquet"
        )
        training_dataset_path = (
            path_settings.features_offline_root
            / "training_dataset"
            / "point_in_time_training_dataset.parquet"
        )

        self.assertEqual(
            sources.customers_normalized_source.path,
            f"file://{customers_path}",
        )
        self.assertEqual(
            sources.transactions_normalized_source.timestamp_field,
            "event_time",
        )
        self.assertEqual(
            sources.point_in_time_training_dataset_source.path,
            f"file://{training_dataset_path}",
        )

    def test_entities_cover_customer_article_and_session_keys(self) -> None:
        from feast_repo import entities

        self.assertEqual(entities.customer.join_key, "customer_id")
        self.assertEqual(entities.article.join_key, "article_id")
        self.assertEqual(entities.customer_session.join_key, "customer_session_id")

    def test_offline_views_cover_current_feature_registry_names(self) -> None:
        from feast_repo.offline_views import offline_feature_views

        views = {view.name: view for view in offline_feature_views()}

        self.assertEqual(
            set(views.keys()),
            {
                "customer_profile_features",
                "article_catalog_features",
                "customer_activity_features",
                "article_demand_features",
                "customer_article_affinity_features",
            },
        )
        self.assertEqual(
            {field.name for field in views["customer_profile_features"].schema},
            {
                "age",
                "club_member_status",
                "fashion_news_frequency",
                "has_fn_flag",
                "has_active_flag",
            },
        )
        self.assertEqual(
            {field.name for field in views["article_catalog_features"].schema},
            {
                "product_type_name",
                "product_group_name",
                "colour_group_name",
                "department_name",
                "index_group_name",
                "has_detail_desc",
                "has_image",
            },
        )

    def test_online_views_cover_current_online_requirements(self) -> None:
        from feast_repo.online_views import online_feature_views

        views = {view.name: view for view in online_feature_views()}

        self.assertEqual(
            set(views.keys()),
            {
                "session_intent_features",
                "customer_realtime_features",
                "article_realtime_features",
            },
        )
        self.assertTrue(all(view.online for view in views.values()))
        self.assertEqual(
            views["session_intent_features"].stream_source.name,
            "session_intent_push_source",
        )
        self.assertEqual(
            views["session_intent_features"].source.name,
            "session_intent_snapshot_source",
        )
        self.assertEqual(
            views["customer_realtime_features"].tags["freshness_target_seconds"],
            "300",
        )
        self.assertEqual(
            {field.name for field in views["article_realtime_features"].schema},
            {
                "purchase_count_1d_rt",
                "purchase_count_7d_rt",
                "inventory_level_rt",
                "is_in_stock_rt",
                "current_price_rt",
                "minutes_since_last_catalog_update",
            },
        )


if __name__ == "__main__":
    unittest.main()
