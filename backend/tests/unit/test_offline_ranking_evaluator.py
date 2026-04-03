from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from pipelines.normalization import run_hm_normalization

from recsys_prd.ranking.offline_evaluator import OfflineRankingEvaluator
from recsys_prd.ranking.registry import register_candidate_ranking_model
from recsys_prd.ranking.training import train_local_ranking_model
from recsys_prd.retrieval.embedding_pipeline import build_embedding_artifacts
from recsys_prd.retrieval.vector_index import build_vector_indexes
from recsys_prd.services.mlflow_store import MLflowModelRegistrar, MLflowRunLogger


class FakeRunInfo:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class FakeRun:
    def __init__(self, run_id: str) -> None:
        self.info = FakeRunInfo(run_id)


class FakeModelVersion:
    def __init__(self, version: str) -> None:
        self.version = version


class FakeMlflowClient:
    def create_run(self, experiment_id: str, tags: dict[str, str]) -> FakeRun:
        del experiment_id, tags
        return FakeRun("run-123")

    def log_param(self, run_id: str, key: str, value: object) -> None:
        del run_id, key, value

    def log_metric(self, run_id: str, key: str, value: float) -> None:
        del run_id, key, value

    def log_artifact(self, run_id: str, path: str) -> None:
        del run_id, path

    def create_registered_model(self, name: str) -> None:
        del name

    def create_model_version(self, name: str, source: str, run_id: str) -> FakeModelVersion:
        del name, source, run_id
        return FakeModelVersion("2")

    def set_model_version_tag(self, name: str, version: str, key: str, value: str) -> None:
        del name, version, key, value


class OfflineRankingEvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)
        self.raw_root = self.root / "raw" / "hm"
        self.normalized_root = self.root / "normalized"
        self.embeddings_root = self.root / "embeddings"
        self.indexes_root = self.root / "indexes"
        self.models_root = self.root / "models"
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
        mlflow_client = FakeMlflowClient()
        train_local_ranking_model(
            normalized_root=self.normalized_root,
            indexes_root=self.indexes_root,
            models_root=self.models_root,
            mlflow_logger=MLflowRunLogger(client=mlflow_client),
        )
        register_candidate_ranking_model(
            models_root=self.models_root,
            normalized_root=self.normalized_root,
            indexes_root=self.indexes_root,
            mlflow_registrar=MLflowModelRegistrar(client=mlflow_client),
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        self.tmp_dir.cleanup()

    def test_evaluates_precision_map_and_ndcg(self) -> None:
        outputs = OfflineRankingEvaluator().evaluate(models_root=self.models_root, k=2)

        payload = json.loads(Path(outputs["report"]).read_text(encoding="utf-8"))
        self.assertGreaterEqual(payload["metrics"]["precision_at_k"], 0.5)
        self.assertGreaterEqual(payload["metrics"]["map_at_k"], 0.5)
        self.assertGreaterEqual(payload["metrics"]["ndcg_at_k"], 0.5)
        self.assertGreaterEqual(payload["metrics"]["pairwise_quality"], 0.66)

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
                    "article_id": "108775016",
                    "price": "49.99",
                    "sales_channel_id": "2",
                },
                {
                    "t_dat": "2020-10-01",
                    "customer_id": "0001",
                    "article_id": "108775018",
                    "price": "39.99",
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


if __name__ == "__main__":
    unittest.main()
