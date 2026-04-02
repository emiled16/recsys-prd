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


if __name__ == "__main__":
    unittest.main()
