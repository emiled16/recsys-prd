from __future__ import annotations

import unittest

from recsys_prd.features.online_requirements import online_feature_requirements


class OnlineFeatureRequirementsTests(unittest.TestCase):
    def test_online_requirements_cover_expected_sets(self) -> None:
        requirements = {item.name: item for item in online_feature_requirements()}
        self.assertEqual(
            set(requirements.keys()),
            {
                "session_intent_features",
                "customer_realtime_features",
                "article_realtime_features",
            },
        )

    def test_freshness_targets_are_ordered_by_serving_need(self) -> None:
        requirements = {item.name: item for item in online_feature_requirements()}
        self.assertLess(
            requirements["session_intent_features"].freshness_target_seconds,
            requirements["customer_realtime_features"].freshness_target_seconds,
        )
        self.assertLessEqual(
            requirements["article_realtime_features"].freshness_target_seconds,
            requirements["customer_realtime_features"].freshness_target_seconds,
        )


if __name__ == "__main__":
    unittest.main()
