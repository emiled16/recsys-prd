from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings


def validate_hm_normalized(
    *,
    normalized_root: Path | None = None,
    reports_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict:
    """Temporary placeholder for pipeline-owned normalized dataset validation."""
    del normalized_root, reports_root, settings
    raise NotImplementedError(
        "Pipeline-owned normalized dataset validation has not been implemented yet."
    )
