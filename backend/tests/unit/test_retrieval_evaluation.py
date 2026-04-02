from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from recsys_prd.retrieval.contracts import CandidateRecord, RetrievalResult
from recsys_prd.retrieval.evaluation import OfflineRetrievalEvaluator


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
            normalized_root = Path(tmp_dir) / "normalized"
            self._write_csv(
                normalized_root / "products" / "products_normalized.csv",
                [
                    "article_id",
                    "prod_name",
                    "product_type_name",
                    "product_group_name",
                    "colour_group_name",
                    "department_name",
                    "section_name",
                    "detail_desc",
                ],
                [
                    {
                        "article_id": "1001",
                        "prod_name": "Summer Dress",
                        "product_type_name": "dress",
                        "product_group_name": "garment upper body",
                        "colour_group_name": "beige",
                        "department_name": "ladies dresses",
                        "section_name": "womens everyday collection",
                        "detail_desc": "airy cotton dress",
                    },
                    {
                        "article_id": "1004",
                        "prod_name": "Denim Skirt",
                        "product_type_name": "skirt",
                        "product_group_name": "garment lower body",
                        "colour_group_name": "blue",
                        "department_name": "ladies bottoms",
                        "section_name": "denim shop",
                        "detail_desc": "classic denim skirt",
                    },
                ],
            )
            self._write_csv(
                normalized_root / "customers" / "customers_normalized.csv",
                ["customer_id"],
                [{"customer_id": "c1"}],
            )
            self._write_csv(
                normalized_root / "images" / "product_images_manifest.csv",
                ["article_id"],
                [{"article_id": "1001"}, {"article_id": "1004"}],
            )
            self._write_csv(
                normalized_root / "transactions" / "transactions_normalized.csv",
                [
                    "event_id",
                    "event_time",
                    "customer_id",
                    "article_id",
                    "price",
                    "sales_channel_id",
                ],
                [
                    {
                        "event_id": "evt-1",
                        "event_time": "2020-09-20T00:00:00Z",
                        "customer_id": "c1",
                        "article_id": "1001",
                        "price": "29.99",
                        "sales_channel_id": "2",
                    },
                    {
                        "event_id": "evt-2",
                        "event_time": "2020-09-21T00:00:00Z",
                        "customer_id": "c1",
                        "article_id": "1004",
                        "price": "39.99",
                        "sales_channel_id": "2",
                    },
                ],
            )

            outputs = OfflineRetrievalEvaluator(retriever=FakeRetriever()).evaluate(
                normalized_root=normalized_root,
                report_path=Path(tmp_dir) / "retrieval.json",
                k=3,
            )

            payload = json.loads(Path(outputs["report"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["metrics"]["recall_at_k"], 1.0)
            self.assertEqual(payload["metrics"]["mrr"], 0.75)
            self.assertGreater(payload["metrics"]["ndcg_at_k"], 0.8)

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


if __name__ == "__main__":
    unittest.main()
