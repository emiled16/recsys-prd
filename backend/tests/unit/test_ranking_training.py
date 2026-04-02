from __future__ import annotations

import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from recsys_prd.events.io import read_jsonl
from recsys_prd.io.tabular_ops import read_tabular_rows
from recsys_prd.normalization.pipeline import run_hm_normalization
from recsys_prd.ranking.dataset import build_ranking_dataset
from recsys_prd.ranking.model import RankingTrainingConfig
from recsys_prd.ranking.trainers import XGBoostRankerTrainer
from recsys_prd.ranking.training import load_ranking_model, train_local_ranking_model
from recsys_prd.retrieval.embedding_pipeline import build_embedding_artifacts
from recsys_prd.retrieval.vector_index import build_vector_indexes
from recsys_prd.services.mlflow_store import MLflowRunLogger


class FakeRunInfo:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class FakeRun:
    def __init__(self, run_id: str) -> None:
        self.info = FakeRunInfo(run_id)


class FakeMlflowClient:
    def __init__(self) -> None:
        self.params: dict[str, object] = {}
        self.metrics: dict[str, float] = {}
        self.artifacts: list[str] = []

    def create_run(self, experiment_id: str, tags: dict[str, str]) -> FakeRun:
        del experiment_id, tags
        return FakeRun("run-123")

    def log_param(self, run_id: str, key: str, value: object) -> None:
        del run_id
        self.params[key] = value

    def log_metric(self, run_id: str, key: str, value: float) -> None:
        del run_id
        self.metrics[key] = value

    def log_artifact(self, run_id: str, path: str) -> None:
        del run_id
        self.artifacts.append(path)


class FakeRankerBackend:
    def __init__(self) -> None:
        self.fit_calls: list[dict[str, object]] = []

    def fit(
        self,
        feature_matrix: list[list[float]],
        labels: list[int],
        *,
        group: list[int],
    ) -> None:
        self.fit_calls.append(
            {
                "row_count": len(feature_matrix),
                "label_count": len(labels),
                "group_sizes": group,
            }
        )

    def predict(self, feature_matrix: list[list[float]]) -> list[float]:
        del feature_matrix
        return [0.9]

    def serialize_model(self) -> bytes:
        return b"fake-xgboost-model"


class RankingTrainingTests(unittest.TestCase):
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
        self.dataset_path = build_ranking_dataset(
            normalized_root=self.normalized_root,
            indexes_root=self.indexes_root,
            models_root=self.models_root / "training_sets",
            negative_sample_count=2,
            max_seed_articles=2,
        )
        self.mlflow_client = FakeMlflowClient()
        self.mlflow_logger = MLflowRunLogger(client=self.mlflow_client)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        self.tmp_dir.cleanup()

    def test_trains_reproducible_baseline_and_tracks_runs(self) -> None:
        outputs = train_local_ranking_model(
            normalized_root=self.normalized_root,
            indexes_root=self.indexes_root,
            models_root=self.models_root,
            mlflow_logger=self.mlflow_logger,
        )

        model = load_ranking_model(outputs["model"])
        metrics = json.loads(outputs["metrics"].read_text(encoding="utf-8"))
        manifest = json.loads(outputs["manifest"].read_text(encoding="utf-8"))
        run_log = read_jsonl(outputs["run_log"])
        rows = read_tabular_rows(self.dataset_path)

        self.assertEqual(manifest["dataset"]["path"], str(self.dataset_path))
        self.assertEqual(manifest["mlflow_run_id"], "run-123")
        self.assertEqual(len(run_log), 1)
        self.assertEqual(run_log[0]["run_id"], manifest["run_id"])
        self.assertEqual(run_log[0]["mlflow_run_id"], "run-123")
        self.assertEqual(metrics["row_count"], float(len(rows)))
        self.assertGreater(metrics["mean_positive_score"], metrics["mean_negative_score"])
        self.assertGreaterEqual(metrics["pairwise_accuracy"], 0.66)
        self.assertIn("training_config.epochs", self.mlflow_client.params)
        self.assertIn(str(outputs["model"]), self.mlflow_client.artifacts)

        positive_row = next(
            row
            for row in rows
            if row["label_timestamp"] == "2020-09-25T00:00:00Z" and row["label_purchase"] == "1"
        )
        negative_row = next(
            row
            for row in rows
            if row["label_timestamp"] == "2020-09-25T00:00:00Z" and row["label_purchase"] == "0"
        )
        self.assertGreater(
            model.predict_probability(positive_row),
            model.predict_probability(negative_row),
        )

    def test_xgboost_ranker_trainer_builds_grouped_fit_inputs(self) -> None:
        rows = read_tabular_rows(self.dataset_path)
        backend = FakeRankerBackend()
        trainer = XGBoostRankerTrainer(
            backend_factory=lambda config, objective: backend,
        )

        trainer.train(
            rows,
            config=RankingTrainingConfig(epochs=5),
            model_name="ranking_xgboost_baseline",
            model_version="v1",
        )

        self.assertEqual(len(backend.fit_calls), 1)
        self.assertEqual(backend.fit_calls[0]["row_count"], len(rows))
        self.assertEqual(sum(backend.fit_calls[0]["group_sizes"]), len(rows))

    def test_xgboost_ranker_training_persists_trainer_specific_artifact(self) -> None:
        backend = FakeRankerBackend()
        outputs = train_local_ranking_model(
            normalized_root=self.normalized_root,
            indexes_root=self.indexes_root,
            models_root=self.models_root,
            trainer=XGBoostRankerTrainer(
                backend_factory=lambda config, objective: backend,
            ),
            mlflow_logger=self.mlflow_logger,
        )

        model_payload = json.loads(outputs["model"].read_text(encoding="utf-8"))
        manifest = json.loads(outputs["manifest"].read_text(encoding="utf-8"))

        self.assertEqual(model_payload["model_name"], "ranking_xgboost_ranker")
        self.assertEqual(model_payload["model_family"], "xgboost_ranker")
        self.assertIsNone(model_payload["weights"])
        self.assertTrue(model_payload["backend_payload"])
        self.assertEqual(manifest["trainer"], "xgboost_ranker")

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


if __name__ == "__main__":
    unittest.main()
