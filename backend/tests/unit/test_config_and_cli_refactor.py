from __future__ import annotations

import argparse
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from recsys_prd.cli import build_parser, main, run_feature_command, run_retrieval_command
from recsys_prd.config import BrokerSettings, PathSettings


class ConfigAndCliRefactorTests(unittest.TestCase):
    def test_path_settings_from_env_uses_configured_roots(self) -> None:
        with patch.dict(
            os.environ,
            {
                "RECSYS_PRD_PROJECT_ROOT": "/tmp/project",
                "RECSYS_PRD_DATA_ROOT": "/tmp/project/custom-data",
            },
            clear=False,
        ):
            settings = PathSettings.from_env()

        self.assertEqual(settings.project_root, Path("/tmp/project").resolve())
        self.assertEqual(settings.data_root, Path("/tmp/project/custom-data").resolve())
        self.assertEqual(
            settings.online_feature_store_root,
            Path("/tmp/project/custom-data/features/online_bootstrap").resolve(),
        )

    def test_feature_command_routes_to_pit_builder(self) -> None:
        args = argparse.Namespace(command="build-pit-training-set")
        with patch("recsys_prd.cli.build_point_in_time_training_dataset") as mock_builder:
            mock_builder.return_value = Path("/tmp/point_in_time_training_dataset.parquet")
            status = run_feature_command(args, settings=object())

        self.assertEqual(status, 0)
        mock_builder.assert_called_once()

    def test_feature_command_routes_to_feast_apply(self) -> None:
        args = argparse.Namespace(
            command="apply-feast-repo",
            materialize_incremental=True,
            end_date="2026-04-02T00:00:00Z",
        )
        with patch("recsys_prd.cli.apply_feast_repo") as mock_apply:
            mock_apply.return_value = {"repo_path": "/tmp/feast_repo"}
            status = run_feature_command(args, settings=object())

        self.assertEqual(status, 0)
        mock_apply.assert_called_once()

    def test_main_routes_to_retrieval_handler(self) -> None:
        with patch("recsys_prd.cli.run_retrieval_command", return_value=0) as mock_handler:
            status = main(["build-vector-index"], settings=object())

        self.assertEqual(status, 0)
        mock_handler.assert_called_once()

    def test_backend_cli_does_not_expose_runtime_bootstrap_command(self) -> None:
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["bootstrap-redpanda-topics"])

    def test_broker_defaults_target_external_local_redpanda_listener(self) -> None:
        self.assertEqual(BrokerSettings().bootstrap_servers, "127.0.0.1:9092")

    def test_retrieval_command_routes_to_qdrant_loader(self) -> None:
        args = argparse.Namespace(command="build-qdrant-index")
        with patch("recsys_prd.cli.load_qdrant_indexes") as mock_loader:
            mock_loader.return_value = {"text_count": 2, "fused_count": 2}
            status = run_retrieval_command(args, settings=object())

        self.assertEqual(status, 0)
        mock_loader.assert_called_once()

    def test_retrieval_command_routes_to_offline_evaluator(self) -> None:
        with patch("recsys_prd.cli.OfflineRetrievalEvaluator") as mock_evaluator:
            mock_evaluator.return_value.evaluate.return_value = {"report": "/tmp/retrieval.json"}
            status = main(["evaluate-retrieval"], settings=object())

        self.assertEqual(status, 0)
        mock_evaluator.return_value.evaluate.assert_called_once()

    def test_ranking_command_routes_to_registered_model_evaluation(self) -> None:
        with patch("recsys_prd.cli.evaluate_registered_ranking_model") as mock_evaluate:
            mock_evaluate.return_value = {"evaluation": "/tmp/evaluation.json"}
            status = main(["evaluate-ranking-model"], settings=object())

        self.assertEqual(status, 0)
        mock_evaluate.assert_called_once()

    def test_ranking_command_routes_to_offline_quality_evaluator(self) -> None:
        with patch("recsys_prd.cli.OfflineRankingEvaluator") as mock_evaluator:
            mock_evaluator.return_value.evaluate.return_value = {"report": "/tmp/ranking.json"}
            status = main(["evaluate-ranking-quality"], settings=object())

        self.assertEqual(status, 0)
        mock_evaluator.return_value.evaluate.assert_called_once()
