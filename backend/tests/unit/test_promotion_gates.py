from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from recsys_prd.ranking.promotion import evaluate_promotion_gate


class PromotionGateTests(unittest.TestCase):
    def test_combines_retrieval_ranking_smoke_and_online_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            retrieval_report = root / "retrieval.json"
            ranking_report = root / "ranking.json"
            api_smoke_report = root / "api_smoke.json"
            online_report = root / "online.json"
            output_path = root / "gate.json"

            retrieval_report.write_text(
                json.dumps({"readiness": {"ready_for_promotion": True}}),
                encoding="utf-8",
            )
            ranking_report.write_text(
                json.dumps(
                    {
                        "metrics": {
                            "precision_at_k": 0.7,
                            "map_at_k": 0.7,
                            "ndcg_at_k": 0.7,
                            "pairwise_quality": 0.8,
                        }
                    }
                ),
                encoding="utf-8",
            )
            api_smoke_report.write_text(json.dumps({"blockers": []}), encoding="utf-8")
            online_report.write_text(
                json.dumps({"rollback_recommended": False}),
                encoding="utf-8",
            )

            outputs = evaluate_promotion_gate(
                retrieval_report_path=retrieval_report,
                ranking_evaluation_path=ranking_report,
                api_smoke_report_path=api_smoke_report,
                online_evaluation_report_path=online_report,
                output_path=output_path,
                ranking_thresholds={
                    "precision_at_k": 0.6,
                    "map_at_k": 0.6,
                    "ndcg_at_k": 0.6,
                    "pairwise_quality": 0.7,
                },
            )

            payload = json.loads(Path(outputs["report"]).read_text(encoding="utf-8"))
            self.assertTrue(payload["ready_for_promotion"])
            self.assertFalse(payload["blockers"])


if __name__ == "__main__":
    unittest.main()
