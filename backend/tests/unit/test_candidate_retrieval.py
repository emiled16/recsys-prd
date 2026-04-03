from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from pipelines.normalization import run_hm_normalization
from simulator import publish_local_replay

from recsys_prd.features.online_service import OnlineFeatureService
from recsys_prd.features.streaming_features import compute_online_feature_store
from recsys_prd.retrieval.candidate_retrieval import CandidateRetriever
from recsys_prd.retrieval.contracts import RetrievalRequest
from recsys_prd.retrieval.embedding_pipeline import build_embedding_artifacts
from recsys_prd.retrieval.vector_index import build_vector_indexes


class FakeSearchPoint:
    def __init__(self, article_id: str, score: float, department_name: str) -> None:
        self.score = score
        self.payload = {
            "article_id": article_id,
            "structured_metadata": {"department_name": department_name},
            "modality_availability": {"text": True, "image": article_id == "108775015"},
        }


class FakeQdrantClient:
    def search(
        self,
        *,
        collection_name: str,
        query_vector: list[float],
        limit: int,
        with_payload: bool,
    ) -> list[FakeSearchPoint]:
        del collection_name, query_vector, with_payload
        return [
            FakeSearchPoint("108775015", 0.99, "Ladies Dresses"),
            FakeSearchPoint("108775016", 0.88, "Ladies Dresses"),
            FakeSearchPoint("208775015", 0.21, "Ladies Tops"),
        ][:limit]


class FakeFeastOnlineFeatureService:
    def get_session_intent_features(self, *, customer_id: str, session_id: str) -> dict[str, str]:
        del customer_id, session_id
        return {"recent_search_terms": "linen dress"}

    def get_customer_realtime_features(self, *, customer_id: str) -> dict[str, int]:
        del customer_id
        return {"purchase_count_7d_rt": 3}


class CandidateRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.raw_root = self.root / "raw" / "hm"
        self.normalized_root = self.root / "normalized"
        self.events_root = self.root / "events"
        self.store_root = self.root / "features" / "online_bootstrap"
        self.embeddings_root = self.root / "embeddings"
        self.indexes_root = self.root / "indexes"
        self._write_raw_fixture()
        run_hm_normalization(raw_root=self.raw_root, normalized_root=self.normalized_root)
        publish_local_replay(normalized_root=self.normalized_root, events_root=self.events_root)
        compute_online_feature_store(events_root=self.events_root, store_root=self.store_root)
        build_embedding_artifacts(
            normalized_root=self.normalized_root,
            embeddings_root=self.embeddings_root,
        )
        build_vector_indexes(
            embeddings_root=self.embeddings_root,
            indexes_root=self.indexes_root,
        )
        self.retriever = CandidateRetriever(
            indexes_root=self.indexes_root,
            online_feature_service=OnlineFeatureService(self.store_root),
            feast_online_feature_service=FakeFeastOnlineFeatureService(),
            client=FakeQdrantClient(),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        self.tmp_dir.cleanup()

    def test_retrieves_ranked_candidates_from_query_and_online_context(self) -> None:
        result = self.retriever.retrieve(
            RetrievalRequest(
                query_text="dress beige cotton",
                customer_id="0001",
                session_id="0001-2020-09-20",
                limit=2,
                index_name="fused",
            )
        )

        self.assertEqual(len(result.candidates), 2)
        self.assertEqual(result.candidates[0].article_id, "108775015")
        self.assertTrue(any(token.startswith("session:") for token in result.context_tokens))
        self.assertTrue(any(token.startswith("customer:") for token in result.context_tokens))
        self.assertIn("session:recent_search_terms=linen dress", result.context_tokens)
        self.assertIn("customer:purchase_count_7d_rt=3", result.context_tokens)

    def test_excludes_seed_articles_from_results(self) -> None:
        result = self.retriever.retrieve(
            RetrievalRequest(
                query_text="dress",
                seed_article_ids=("108775015",),
                limit=2,
                index_name="fused",
            )
        )

        article_ids = [candidate.article_id for candidate in result.candidates]
        self.assertNotIn("108775015", article_ids)
        self.assertEqual(article_ids[0], "108775016")

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
