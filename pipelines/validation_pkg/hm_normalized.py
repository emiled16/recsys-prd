from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings


def validate_hm_normalized(
    *,
    normalized_root: Path | None = None,
    reports_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict:
    """Placeholder entrypoint for pipeline-owned normalized dataset validation."""
    raise NotImplementedError("Validation migration to pipelines.validation_pkg is pending.")
