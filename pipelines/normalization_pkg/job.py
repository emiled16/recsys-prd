from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings

from pipelines.normalization.runtime import run_hm_normalization as shimmed_run_hm_normalization


def run_hm_normalization(
    *,
    raw_root: Path | None = None,
    normalized_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path]:
    """Temporary compatibility wrapper for pipeline-owned normalization imports."""
    return shimmed_run_hm_normalization(
        raw_root=raw_root,
        normalized_root=normalized_root,
        settings=settings,
    )
