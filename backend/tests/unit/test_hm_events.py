from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from recsys_prd.events.replay import publish_local_replay
from recsys_prd.events.validation import validate_local_replay
from recsys_prd.normalization.pipeline import run_hm_normalization


class HmEventsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.raw_root = Path(self.tmp_dir.name) / "raw" / "hm"
        self.normalized_root = Path(self.tmp_dir.name) / "normalized"
        self.events_root = Path(self.tmp_dir.name) / "events"
        self.reports_root = Path(self.tmp_dir.name) / "reports"
        self._write_raw_fixture()
        run_hm_normalization(raw_root=self.raw_root, normalized_root=self.normalized_root)

    def tearDown(self) -> None:
        shutil.rmtree(Path(self.tmp_dir.name), ignore_errors=True)
        self.tmp_dir.cleanup()

    def test_generates_replay_batches(self) -> None:
        outputs = publish_local_replay(
            normalized_root=self.normalized_root,
            events_root=self.events_root,
        )

        self.assertTrue(outputs["interaction_events"].exists())
        self.assertTrue(outputs["catalog_events"].exists())
        self.assertTrue(outputs["manifest"].exists())

    def test_validates_generated_batches(self) -> None:
        publish_local_replay(normalized_root=self.normalized_root, events_root=self.events_root)
        result = validate_local_replay(events_root=self.events_root, reports_root=self.reports_root)
        self.assertTrue(result["ok"])

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
                }
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
        (images_dir / "108775015.jpg").write_text("jpg-data", encoding="utf-8")

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
