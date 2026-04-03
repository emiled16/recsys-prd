from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings


def run_hm_normalization(
    *,
    raw_root: Path | None = None,
    normalized_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path]:
    """Placeholder entrypoint for the pipeline-owned normalization job."""
    raise NotImplementedError("Normalization migration to pipelines.normalization_pkg is pending.")
