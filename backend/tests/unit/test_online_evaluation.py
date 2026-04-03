from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from recsys_prd.serving.online_evaluation import build_online_experiment_report


class OnlineEvaluationTests(unittest.TestCase):
    def test_builds_guardrail_metrics_from_exposures_and_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            exposures_path = root / "exposures.jsonl"
            events_path = root / "events.jsonl"
            report_path = root / "report.json"
            exposures_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "response_id": "r1",
                                "response": {
                                    "fallback_used": False,
                                    "recommendations": [{"article_id": "a1"}],
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "response_id": "r2",
                                "response": {"fallback_used": True, "recommendations": []},
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            events_path.write_text(
                "\n".join(
                    [
                        json.dumps({"event_type": "recommendation_click", "response_id": "r1"}),
                        json.dumps({"event_type": "recommendation_feedback", "response_id": "r2"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            outputs = build_online_experiment_report(
                exposures_path=exposures_path,
                events_path=events_path,
                report_path=report_path,
                fallback_rate_threshold=0.4,
                null_result_rate_threshold=0.4,
            )

            payload = json.loads(Path(outputs["report"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["exposure_count"], 2)
            self.assertEqual(payload["click_count"], 1)
            self.assertEqual(payload["feedback_count"], 1)
            self.assertEqual(payload["ctr"], 0.5)
            self.assertEqual(payload["fallback_rate"], 0.5)
            self.assertTrue(payload["rollback_recommended"])


if __name__ == "__main__":
    unittest.main()
