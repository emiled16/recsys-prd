from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from recsys_prd.normalization.pipeline import run_hm_normalization
from recsys_prd.ranking.dataset import build_ranking_dataset
from recsys_prd.retrieval.embedding_pipeline import build_embedding_artifacts
from recsys_prd.retrieval.vector_index import build_vector_indexes


class RankingDatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.raw_root = self.root / "raw" / "hm"
        self.normalized_root = self.root / "normalized"
        self.embeddings_root = self.root / "embeddings"
        self.indexes_root = self.root / "indexes"
        self.models_root = self.root / "models" / "training_sets"
        self._write_raw_fixture()
        run_hm_normalization(raw_root=self.raw_root, normalized_root=self.normalized_root)
        build_embedding_artifacts(
            normalized_root=self.normalized_root,
            embeddings_root=self.embeddings_root,
        )
        build_vector_indexes(
            embeddings_root=self.embeddings_root,
            indexes_root=self.indexes_root,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        self.tmp_dir.cleanup()

    def test_builds_ranking_rows_with_positive_labels_and_retrieved_negatives(self) -> None:
        dataset_path = build_ranking_dataset(
            normalized_root=self.normalized_root,
            indexes_root=self.indexes_root,
            models_root=self.models_root,
            negative_sample_count=2,
            max_seed_articles=2,
        )

        rows = self._read_csv(dataset_path)
        manifest = json.loads(
            (self.models_root / "ranking_dataset" / "manifest.json").read_text(encoding="utf-8")
        )

        self.assertEqual(manifest["positive_row_count"], 3)
        self.assertEqual(manifest["negative_sample_count"], 2)
        self.assertEqual(len(rows), manifest["row_count"])

        positive_rows = [row for row in rows if row["candidate_source"] == "observed_positive"]
        negative_rows = [row for row in rows if row["candidate_source"] == "retrieval_negative"]

        self.assertEqual(len(positive_rows), 3)
        self.assertGreaterEqual(len(negative_rows), 3)
        self.assertTrue(all(row["label_purchase"] == "1" for row in positive_rows))
        self.assertTrue(all(row["label_purchase"] == "0" for row in negative_rows))

        second_positive = next(
            row
            for row in positive_rows
            if row["label_timestamp"] == "2020-09-25T00:00:00Z"
        )
        self.assertEqual(second_positive["candidate_article_id"], "108775015")
        self.assertEqual(second_positive["retrieval_seed_article_ids"], "108775015")
        self.assertEqual(second_positive["customer_purchase_count_all_time"], "1")
        self.assertEqual(second_positive["customer_article_historical_purchase_count"], "1")

        second_event_negatives = [
            row
            for row in negative_rows
            if row["label_timestamp"] == "2020-09-25T00:00:00Z"
        ]
        self.assertEqual(len(second_event_negatives), 2)
        self.assertTrue(
            all(row["candidate_article_id"] != second_positive["target_article_id"] for row in second_event_negatives)
        )
        self.assertTrue(all(row["candidate_rank"] in {"1", "2"} for row in second_event_negatives))
        self.assertTrue(all(row["customer_purchase_count_all_time"] == "1" for row in second_event_negatives))
        self.assertTrue(
            all(row["customer_article_historical_purchase_count"] == "0" for row in second_event_negatives)
        )

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
                },
                {
                    "article_id": "108775016",
                    "product_code": "108776",
                    "prod_name": "Evening Dress",
                    "product_type_name": "dress",
                    "product_group_name": "garment upper body",
                    "graphical_appearance_name": "solid",
                    "colour_group_name": "black",
                    "perceived_colour_value_name": "dark",
                    "perceived_colour_master_name": "black",
                    "department_name": "ladies dresses",
                    "index_name": "ladieswear",
                    "index_group_name": "ladieswear",
                    "section_name": "party edit",
                    "garment_group_name": "dresses",
                    "detail_desc": "elegant evening dress",
                },
                {
                    "article_id": "108775017",
                    "product_code": "108777",
                    "prod_name": "Cotton Shirt",
                    "product_type_name": "shirt",
                    "product_group_name": "garment upper body",
                    "graphical_appearance_name": "solid",
                    "colour_group_name": "white",
                    "perceived_colour_value_name": "light",
                    "perceived_colour_master_name": "white",
                    "department_name": "ladies tops",
                    "index_name": "ladieswear",
                    "index_group_name": "ladieswear",
                    "section_name": "casual basics",
                    "garment_group_name": "tops",
                    "detail_desc": "soft cotton shirt",
                },
                {
                    "article_id": "108775018",
                    "product_code": "108778",
                    "prod_name": "Denim Skirt",
                    "product_type_name": "skirt",
                    "product_group_name": "garment lower body",
                    "graphical_appearance_name": "solid",
                    "colour_group_name": "blue",
                    "perceived_colour_value_name": "medium",
                    "perceived_colour_master_name": "blue",
                    "department_name": "ladies bottoms",
                    "index_name": "ladieswear",
                    "index_group_name": "ladieswear",
                    "section_name": "denim shop",
                    "garment_group_name": "skirts",
                    "detail_desc": "classic denim skirt",
                },
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
                {
                    "t_dat": "2020-10-10",
                    "customer_id": "0001",
                    "article_id": "108775017",
                    "price": "24.99",
                    "sales_channel_id": "1",
                },
            ],
        )
        (images_dir / "108775015.jpg").write_text("jpg-data", encoding="utf-8")
        (images_dir / "108775016.jpg").write_text("jpg-data", encoding="utf-8")

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

    def _read_csv(self, path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))


if __name__ == "__main__":
    unittest.main()
