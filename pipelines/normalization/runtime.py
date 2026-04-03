from __future__ import annotations

from pathlib import Path

from recsys_prd.config import AppSettings


def run_hm_normalization(
    *,
    raw_root: Path | None = None,
    normalized_root: Path | None = None,
    settings: AppSettings | None = None,
) -> dict[str, Path]:
    """Temporary placeholder for the pipeline-owned normalization runtime."""
    del raw_root, normalized_root, settings
    raise NotImplementedError("Pipeline-owned normalization runtime has not been implemented yet.")
