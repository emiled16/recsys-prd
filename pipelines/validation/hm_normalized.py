from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings
from recsys_prd.validation.hm_normalized import validate_hm_normalized as backend_validate_hm_normalized


def validate_hm_normalized(
    *,
    normalized_root: Path | None = None,
    reports_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict:
    """Temporary compatibility wrapper for backend-owned normalized dataset validation."""
    return backend_validate_hm_normalized(
        normalized_root=normalized_root,
        reports_root=reports_root,
        settings=settings,
    )
