from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from recsys_prd.api.app import create_app
from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.io.json_ops import write_json
from recsys_prd.schemas.artifacts import ApiSmokeReport


def build_api_smoke_report(
    *,
    report_path: Path | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path | dict[str, object]]:
    """Exercise the public API contracts in-process and persist a smoke report."""
    settings = settings or get_app_settings()
    report_path = report_path or settings.paths.reports_root / "serving" / "api_smoke_report.json"

    blockers: list[str] = []
    client = TestClient(create_app())
    health_response = client.get("/healthz")
    ready_response = client.get("/readyz")
    diagnostics_response = client.get("/diagnostics")

    health_ok = health_response.status_code == 200 and health_response.json().get("status") == "ok"
    ready_ok = ready_response.status_code == 200 and bool(ready_response.json().get("ready", False))
    diagnostics_ok = diagnostics_response.status_code == 200 and "/recommendations" in (
        diagnostics_response.json().get("supported_endpoints", [])
    )

    if not health_ok:
        blockers.append("healthz_failed")
    if not ready_ok:
        blockers.append("readyz_failed")
    if not diagnostics_ok:
        blockers.append("diagnostics_failed")

    report = ApiSmokeReport(
        checked_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        health_ok=health_ok,
        ready_ok=ready_ok,
        diagnostics_ok=diagnostics_ok,
        blockers=blockers,
    )
    payload = report.model_dump()
    payload["responses"] = {
        "healthz": health_response.json(),
        "readyz": ready_response.json(),
        "diagnostics": diagnostics_response.json(),
    }
    write_json(report_path, payload)
    return {"report": report_path, "status": payload}
