from __future__ import annotations

import argparse
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from recsys_prd.cli import main, run_feature_command
from recsys_prd.config import PathSettings


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

    def test_main_routes_to_retrieval_handler(self) -> None:
        with patch("recsys_prd.cli.run_retrieval_command", return_value=0) as mock_handler:
            status = main(["build-vector-index"], settings=object())

        self.assertEqual(status, 0)
        mock_handler.assert_called_once()
