from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings

from pipelines.validation.hm_normalized import validate_hm_normalized as shimmed_validate_hm_normalized


def validate_hm_normalized(
    *,
    normalized_root: Path | None = None,
    reports_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict:
    """Temporary compatibility wrapper for pipeline-owned validation imports."""
    return shimmed_validate_hm_normalized(
        normalized_root=normalized_root,
        reports_root=reports_root,
        settings=settings,
    )
