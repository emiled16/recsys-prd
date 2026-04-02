from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from recsys_prd.events.io import read_jsonl
from recsys_prd.normalization.pipeline import run_hm_normalization
from recsys_prd.retrieval.embedding_pipeline import (
    EMBEDDING_DIMENSION,
    build_embedding_artifacts,
)


class EmbeddingPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.raw_root = self.root / "raw" / "hm"
        self.normalized_root = self.root / "normalized"
        self.embeddings_root = self.root / "embeddings"
        self._write_raw_fixture()
        run_hm_normalization(raw_root=self.raw_root, normalized_root=self.normalized_root)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        self.tmp_dir.cleanup()

    def test_builds_text_image_and_fused_embedding_artifacts(self) -> None:
        outputs = build_embedding_artifacts(
            normalized_root=self.normalized_root,
            embeddings_root=self.embeddings_root,
        )

        text_records = read_jsonl(outputs["text_embeddings"])
        image_records = read_jsonl(outputs["image_embeddings"])
        fused_records = read_jsonl(outputs["fused_embeddings"])
        manifest = json.loads(outputs["manifest"].read_text(encoding="utf-8"))

        self.assertEqual(len(text_records), 2)
        self.assertEqual(len(image_records), 1)
        self.assertEqual(len(fused_records), 2)
        self.assertEqual(manifest["dimension"], EMBEDDING_DIMENSION)
        self.assertEqual(manifest["artifacts"]["image"]["row_count"], 1)

        text_by_article = {record["article_id"]: record for record in text_records}
        fused_by_article = {record["article_id"]: record for record in fused_records}

        image_backed_fused = fused_by_article["108775015"]
        self.assertTrue(image_backed_fused["modality_availability"]["image"])
        self.assertEqual(
            len(image_backed_fused["vector"]),
            EMBEDDING_DIMENSION,
        )
        self.assertNotEqual(
            image_backed_fused["vector"],
            text_by_article["108775015"]["vector"],
        )

        text_only_fused = fused_by_article["208775015"]
        self.assertFalse(text_only_fused["modality_availability"]["image"])
        self.assertEqual(
            text_only_fused["vector"],
            text_by_article["208775015"]["vector"],
        )
        self.assertEqual(
            text_only_fused["structured_metadata"]["department_name"],
            "Ladies Tops",
        )

    def _write_raw_fixture(self) -> None:
        articles_dir = self.raw_root / "articles"
        customers_dir = self.raw_root / "customers"
        transactions_dir = self.raw_root / "transactions"
        image_dir = self.raw_root / "images" / "108"
        for directory in [articles_dir, customers_dir, transactions_dir, image_dir]:
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
                    "article_id": "208775015",
                    "product_code": "208775",
                    "prod_name": "Relaxed Tee",
                    "product_type_name": "t-shirt",
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
                    "detail_desc": "soft jersey tee",
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
                }
            ],
        )
        (image_dir / "108775015.jpg").write_text("jpg-data", encoding="utf-8")

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
