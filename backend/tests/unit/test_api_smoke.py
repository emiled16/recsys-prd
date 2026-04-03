from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from recsys_prd.api.smoke import build_api_smoke_report


class ApiSmokeTests(unittest.TestCase):
    def test_builds_in_process_api_smoke_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "api_smoke.json"

            outputs = build_api_smoke_report(report_path=report_path)

            payload = json.loads(Path(outputs["report"]).read_text(encoding="utf-8"))
            self.assertTrue(payload["health_ok"])
            self.assertIn(
                "/recommendations",
                payload["responses"]["diagnostics"]["supported_endpoints"],
            )


if __name__ == "__main__":
    unittest.main()
