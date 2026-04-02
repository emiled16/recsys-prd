from __future__ import annotations

import unittest

from recsys_prd.features.registry import feature_entities, feature_views


class FeatureRegistryTests(unittest.TestCase):
    def test_feature_entities_are_defined(self) -> None:
        entities = {entity.name: entity for entity in feature_entities()}
        self.assertEqual(set(entities.keys()), {"customer", "article", "customer_article"})
        self.assertEqual(entities["customer"].join_keys, ("customer_id",))
        self.assertEqual(entities["customer_article"].join_keys, ("customer_id", "article_id"))

    def test_feature_views_cover_static_and_time_aware_sets(self) -> None:
        views = {view.name: view for view in feature_views()}
        self.assertIn("customer_profile_features", views)
        self.assertIn("article_catalog_features", views)
        self.assertIn("customer_activity_features", views)
        self.assertEqual(views["customer_profile_features"].timestamp_field, None)
        self.assertEqual(views["customer_activity_features"].timestamp_field, "event_time")


if __name__ == "__main__":
    unittest.main()
