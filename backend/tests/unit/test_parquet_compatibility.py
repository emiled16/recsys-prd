from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pipelines.normalization.writer import write_dataset_bundle

from recsys_prd.io.tabular_ops import read_tabular_rows


class ParquetCompatibilityTests(unittest.TestCase):
    def test_dataset_bundle_writes_parquet_and_csv_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dataset_dir = Path(tmp_dir) / "dataset"
            dataset_path = write_dataset_bundle(
                dataset_dir=dataset_dir,
                dataset_filename="rows.parquet",
                fieldnames=["id", "value"],
                rows=[{"id": "1", "value": "a"}],
                primary_key="id",
            )

            self.assertEqual(dataset_path.suffix, ".parquet")
            self.assertTrue((dataset_dir / "rows.csv").exists())
            self.assertEqual(read_tabular_rows(dataset_dir / "rows.csv")[0]["value"], "a")
