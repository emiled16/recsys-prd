from __future__ import annotations

from recsys_prd.config import get_app_settings


def resolved_paths():
    settings = get_app_settings()
    return settings.paths
