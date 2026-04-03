from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings
from recsys_prd.normalization.pipeline import run_hm_normalization as backend_run_hm_normalization


def run_hm_normalization(
    *,
    raw_root: Path | None = None,
    normalized_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path]:
    """Temporary compatibility wrapper for the backend-owned normalization runtime."""
    return backend_run_hm_normalization(
        raw_root=raw_root,
        normalized_root=normalized_root,
        settings=settings,
    )
