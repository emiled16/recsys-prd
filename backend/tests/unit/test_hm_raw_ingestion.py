from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from recsys_prd.ingestion.hm_raw import ingest_hm_raw
from recsys_prd.paths import RAW_HM_ROOT


class HmRawIngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.source_root = Path(self.tmp_dir.name) / "hm_source"
        self.source_root.mkdir(parents=True)
        self._write_fixture_dataset(self.source_root)
        if RAW_HM_ROOT.exists():
            shutil.rmtree(RAW_HM_ROOT)

    def tearDown(self) -> None:
        if RAW_HM_ROOT.exists():
            shutil.rmtree(RAW_HM_ROOT)
        self.tmp_dir.cleanup()

    def test_ingests_from_directory(self) -> None:
        result = ingest_hm_raw(self.source_root)

        self.assertTrue(result.customers_path.exists())
        self.assertTrue(result.articles_path.exists())
        self.assertTrue(result.transactions_path.exists())
        self.assertTrue(result.images_root.exists())
        self.assertEqual(result.image_count, 2)

        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_kind"], "directory")
        self.assertEqual(manifest["image_count"], 2)

    def test_ingests_from_zip_archive(self) -> None:
        zip_path = Path(self.tmp_dir.name) / "hm.zip"
        with ZipFile(zip_path, "w") as archive:
            for path in self.source_root.rglob("*"):
                archive.write(path, arcname=path.relative_to(self.source_root))

        result = ingest_hm_raw(zip_path)

        self.assertTrue(result.manifest_path.exists())
        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_kind"], "zip")
        self.assertEqual(manifest["image_count"], 2)

    def _write_fixture_dataset(self, root: Path) -> None:
        (root / "articles.csv").write_text("article_id,prod_name\n1,Dress\n", encoding="utf-8")
        (root / "customers.csv").write_text("customer_id,age\nc1,30\n", encoding="utf-8")
        (root / "transactions_train.csv").write_text(
            "t_dat,customer_id,article_id,price,sales_channel_id\n2020-01-01,c1,1,9.99,1\n",
            encoding="utf-8",
        )
        images_dir = root / "images" / "01"
        images_dir.mkdir(parents=True)
        (images_dir / "1.jpg").write_text("jpg-data", encoding="utf-8")
        (images_dir / "2.jpg").write_text("jpg-data", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
