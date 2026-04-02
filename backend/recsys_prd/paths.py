from __future__ import annotations

from pathlib import Path

from recsys_prd.config import get_app_settings

_SETTINGS = get_app_settings()

BACKEND_ROOT = Path(_SETTINGS.paths.backend_root)
PROJECT_ROOT = Path(_SETTINGS.paths.project_root)
DATA_ROOT = Path(_SETTINGS.paths.data_root)
RAW_HM_ROOT = Path(_SETTINGS.paths.raw_hm_root)
NORMALIZED_ROOT = Path(_SETTINGS.paths.normalized_root)
REPORTS_ROOT = Path(_SETTINGS.paths.reports_root)
