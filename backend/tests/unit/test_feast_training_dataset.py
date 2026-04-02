from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from recsys_prd.features.feast_training_dataset import FeastPointInTimeDatasetBuilder
from recsys_prd.io.tabular_ops import read_tabular_rows
from recsys_prd.normalization.pipeline import run_hm_normalization


class FakeRetrievalJob:
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self.rows = rows

    def to_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)


class FakeFeastStore:
    def __init__(self, rows: list[dict[str, str]]) -> None:
        self.rows = rows
        self.request = None

    def get_historical_features(self, *, entity_df, features, full_feature_names):
        entity_frame = entity_df.compute() if hasattr(entity_df, "compute") else entity_df.copy()
        self.request = {
            "entity_df": entity_frame,
            "features": list(features),
            "full_feature_names": full_feature_names,
        }
        return FakeRetrievalJob(self.rows)


class FeastTrainingDatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.raw_root = Path(self.tmp_dir.name) / "raw" / "hm"
        self.normalized_root = Path(self.tmp_dir.name) / "normalized"
        self.features_root = Path(self.tmp_dir.name) / "features" / "offline"
        self._write_raw_fixture()
        run_hm_normalization(raw_root=self.raw_root, normalized_root=self.normalized_root)

    def tearDown(self) -> None:
        shutil.rmtree(Path(self.tmp_dir.name), ignore_errors=True)
        self.tmp_dir.cleanup()

    def test_builds_training_dataset_from_feast_historical_retrieval(self) -> None:
        store = FakeFeastStore(
            [
                {
                    "customer_profile_features__age": "34",
                    "customer_profile_features__club_member_status": "Active",
                    "customer_profile_features__fashion_news_frequency": "Regularly",
                    "customer_profile_features__has_fn_flag": "1",
                    "customer_profile_features__has_active_flag": "1",
                    "article_catalog_features__product_type_name": "Dress",
                    "article_catalog_features__product_group_name": "Garment Upper Body",
                    "article_catalog_features__colour_group_name": "Light Beige",
                    "article_catalog_features__department_name": "Ladies Dresses",
                    "article_catalog_features__index_group_name": "Ladieswear",
                    "article_catalog_features__has_detail_desc": "1",
                    "article_catalog_features__has_image": "1",
                    "customer_activity_features__purchase_count_30d": "0",
                    "customer_activity_features__purchase_count_all_time": "0",
                    "customer_activity_features__days_since_last_purchase": "-1",
                    "customer_activity_features__distinct_articles_purchased_30d": "0",
                    "customer_activity_features__avg_purchase_price_30d": "0.00",
                    "article_demand_features__purchase_count_7d": "0",
                    "article_demand_features__purchase_count_30d": "0",
                    "article_demand_features__unique_customers_30d": "0",
                    "article_demand_features__avg_article_price_30d": "0.00",
                    "article_demand_features__days_since_last_article_purchase": "-1",
                    "customer_article_affinity_features__historical_purchase_count": "0",
                    "customer_article_affinity_features__days_since_last_purchase": "-1",
                    "customer_article_affinity_features__has_purchased_before": "0",
                    "customer_article_affinity_features__last_purchase_price": "0.00",
                },
                {
                    "customer_profile_features__age": "34",
                    "customer_profile_features__club_member_status": "Active",
                    "customer_profile_features__fashion_news_frequency": "Regularly",
                    "customer_profile_features__has_fn_flag": "1",
                    "customer_profile_features__has_active_flag": "1",
                    "article_catalog_features__product_type_name": "Dress",
                    "article_catalog_features__product_group_name": "Garment Upper Body",
                    "article_catalog_features__colour_group_name": "Light Beige",
                    "article_catalog_features__department_name": "Ladies Dresses",
                    "article_catalog_features__index_group_name": "Ladieswear",
                    "article_catalog_features__has_detail_desc": "1",
                    "article_catalog_features__has_image": "1",
                    "customer_activity_features__purchase_count_30d": "1",
                    "customer_activity_features__purchase_count_all_time": "1",
                    "customer_activity_features__days_since_last_purchase": "5",
                    "customer_activity_features__distinct_articles_purchased_30d": "1",
                    "customer_activity_features__avg_purchase_price_30d": "29.99",
                    "article_demand_features__purchase_count_7d": "1",
                    "article_demand_features__purchase_count_30d": "1",
                    "article_demand_features__unique_customers_30d": "1",
                    "article_demand_features__avg_article_price_30d": "29.99",
                    "article_demand_features__days_since_last_article_purchase": "5",
                    "customer_article_affinity_features__historical_purchase_count": "1",
                    "customer_article_affinity_features__days_since_last_purchase": "5",
                    "customer_article_affinity_features__has_purchased_before": "1",
                    "customer_article_affinity_features__last_purchase_price": "29.99",
                },
            ]
        )
        builder = FeastPointInTimeDatasetBuilder(store=store)

        dataset_path = builder.build(
            normalized_root=self.normalized_root,
            features_root=self.features_root,
        )

        rows = read_tabular_rows(dataset_path)
        manifest = json.loads(
            (self.features_root / "training_dataset" / "join_manifest.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["customer_purchase_count_all_time"], "1")
        self.assertEqual(rows[1]["customer_article_historical_purchase_count"], "1")
        self.assertEqual(manifest["join_engine"], "feast_historical_retrieval")
        self.assertTrue(store.request["full_feature_names"])

    def _write_raw_fixture(self) -> None:
        articles_dir = self.raw_root / "articles"
        customers_dir = self.raw_root / "customers"
        transactions_dir = self.raw_root / "transactions"
        images_dir = self.raw_root / "images" / "108"
        for directory in [articles_dir, customers_dir, transactions_dir, images_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        self._write_csv(
            articles_dir / "articles.csv",
            [
                "article_id",
                "product_code",
                "prod_name",
                "product_type_name",
                "product_group_name",
                "graphical_appearance_name",
                "colour_group_name",
                "perceived_colour_value_name",
                "perceived_colour_master_name",
                "department_name",
                "index_name",
                "index_group_name",
                "section_name",
                "garment_group_name",
                "detail_desc",
            ],
            [
                {
                    "article_id": "108775015",
                    "product_code": "108775",
                    "prod_name": "Summer Dress",
                    "product_type_name": "dress",
                    "product_group_name": "garment upper body",
                    "graphical_appearance_name": "solid",
                    "colour_group_name": "light beige",
                    "perceived_colour_value_name": "light",
                    "perceived_colour_master_name": "beige",
                    "department_name": "ladies dresses",
                    "index_name": "ladieswear",
                    "index_group_name": "ladieswear",
                    "section_name": "womens everyday collection",
                    "garment_group_name": "dresses",
                    "detail_desc": "airy cotton dress",
                }
            ],
        )
        self._write_csv(
            customers_dir / "customers.csv",
            [
                "customer_id",
                "FN",
                "Active",
                "club_member_status",
                "fashion_news_frequency",
                "age",
                "postal_code",
            ],
            [
                {
                    "customer_id": "0001",
                    "FN": "1",
                    "Active": "1",
                    "club_member_status": "active",
                    "fashion_news_frequency": "regularly",
                    "age": "34",
                    "postal_code": "12345",
                }
            ],
        )
        self._write_csv(
            transactions_dir / "transactions_train.csv",
            ["t_dat", "customer_id", "article_id", "price", "sales_channel_id"],
            [
                {
                    "t_dat": "2020-09-20",
                    "customer_id": "0001",
                    "article_id": "108775015",
                    "price": "29.99",
                    "sales_channel_id": "2",
                },
                {
                    "t_dat": "2020-09-25",
                    "customer_id": "0001",
                    "article_id": "108775015",
                    "price": "31.99",
                    "sales_channel_id": "2",
                },
            ],
        )
        (images_dir / "108775015.jpg").write_text("jpg-data", encoding="utf-8")

    def _write_csv(
        self,
        path: Path,
        fieldnames: list[str],
        rows: list[dict[str, str]],
    ) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
