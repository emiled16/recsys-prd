from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from recsys_prd.normalization.pipeline import run_hm_normalization
from recsys_prd.retrieval.contracts import CandidateRecord, RetrievalResult
from recsys_prd.retrieval.embedding_pipeline import build_embedding_artifacts
from recsys_prd.retrieval.evaluation import OfflineRetrievalEvaluator
from recsys_prd.retrieval.vector_index import build_vector_indexes


class FakeRetriever:
    def retrieve(self, request) -> RetrievalResult:
        if "summer dress" in request.query_text.lower():
            article_ids = ("1001", "1002", "1003")
        else:
            article_ids = ("1003", "1004", "1002")
        return RetrievalResult(
            candidates=tuple(
                CandidateRecord(
                    article_id=article_id,
                    score=1.0 / index,
                    structured_metadata={},
                    modality_availability={"text": True},
                )
                for index, article_id in enumerate(article_ids, start=1)
            ),
            index_name="fused",
            context_tokens=(),
        )


class RetrievalEvaluationTests(unittest.TestCase):
    def test_evaluates_recall_mrr_and_ndcg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            raw_root = root / "raw" / "hm"
            normalized_root = root / "normalized"
            embeddings_root = root / "embeddings"
            indexes_root = root / "indexes"
            self._write_raw_fixture(raw_root)
            run_hm_normalization(raw_root=raw_root, normalized_root=normalized_root)
            build_embedding_artifacts(
                normalized_root=normalized_root,
                embeddings_root=embeddings_root,
            )
            build_vector_indexes(
                embeddings_root=embeddings_root,
                indexes_root=indexes_root,
            )

            outputs = OfflineRetrievalEvaluator(retriever=FakeRetriever()).evaluate(
                normalized_root=normalized_root,
                report_path=Path(tmp_dir) / "retrieval.json",
                indexes_root=indexes_root,
                embeddings_root=embeddings_root,
                k=3,
            )

            payload = json.loads(Path(outputs["report"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["metrics"]["recall_at_k"], 1.0)
            self.assertEqual(payload["metrics"]["mrr"], 0.75)
            self.assertGreater(payload["metrics"]["ndcg_at_k"], 0.8)
            self.assertIn("target_has_image=True", payload["slices"])
            self.assertTrue(payload["freshness"]["index_manifest_available"])
            self.assertTrue(payload["readiness"]["ready_for_promotion"])

    def _write_csv(
        self,
        path: Path,
        fieldnames: list[str],
        rows: list[dict[str, str]],
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _write_raw_fixture(self, raw_root: Path) -> None:
        articles_dir = raw_root / "articles"
        customers_dir = raw_root / "customers"
        transactions_dir = raw_root / "transactions"
        images_dir = raw_root / "images" / "100"
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
                    "article_id": "1001",
                    "product_code": "1001",
                    "prod_name": "Summer Dress",
                    "product_type_name": "dress",
                    "product_group_name": "garment upper body",
                    "graphical_appearance_name": "solid",
                    "colour_group_name": "beige",
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
                    "article_id": "1004",
                    "product_code": "1004",
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
                    "customer_id": "c1",
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
                    "customer_id": "c1",
                    "article_id": "1001",
                    "price": "29.99",
                    "sales_channel_id": "2",
                },
                {
                    "t_dat": "2020-09-21",
                    "customer_id": "c1",
                    "article_id": "1004",
                    "price": "39.99",
                    "sales_channel_id": "2",
                },
            ],
        )
        (images_dir / "1001.jpg").write_text("jpg-data", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
