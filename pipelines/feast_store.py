from __future__ import annotations

import importlib
import os
from datetime import datetime, timezone

from feast import FeatureStore

from recsys_prd.config import AppSettings, get_app_settings


def _reload_feast_repo_modules(settings: AppSettings):
    os.environ["RECSYS_PRD_PROJECT_ROOT"] = str(settings.paths.project_root)
    os.environ["RECSYS_PRD_BACKEND_ROOT"] = str(settings.paths.backend_root)
    os.environ["RECSYS_PRD_DATA_ROOT"] = str(settings.paths.data_root)
    os.environ["RECSYS_PRD_NORMALIZED_ROOT"] = str(settings.paths.normalized_root)
    os.environ["RECSYS_PRD_FEATURES_ROOT"] = str(settings.paths.features_root)
    os.environ["RECSYS_PRD_FEATURES_OFFLINE_ROOT"] = str(settings.paths.features_offline_root)
    os.environ["RECSYS_PRD_FEAST_REPO_ROOT"] = str(settings.paths.feast_repo_root)
    get_app_settings.cache_clear()

    from feast_repo import entities, offline_views, online_views, sources

    importlib.reload(sources)
    importlib.reload(entities)
    importlib.reload(offline_views)
    importlib.reload(online_views)
    return entities, sources, offline_views, online_views


def offline_feast_repo_objects(*, settings: AppSettings | None = None) -> list:
    """Return the offline Feast objects in dependency-safe apply order."""
    settings = settings or get_app_settings()
    _reload_feast_repo_modules(settings)
    from feast_repo.registry import offline_objects

    return offline_objects()


def online_feast_repo_objects(*, settings: AppSettings | None = None) -> list:
    """Return the online Feast objects in dependency-safe apply order."""
    settings = settings or get_app_settings()
    _reload_feast_repo_modules(settings)
    from feast_repo.registry import online_objects

    return online_objects()


def feast_repo_objects(
    *,
    include_online: bool = True,
    settings: AppSettings | None = None,
) -> list:
    """Return all Feast repo objects, optionally including online serving definitions."""
    objects = offline_feast_repo_objects(settings=settings)
    if include_online:
        objects.extend(online_feast_repo_objects(settings=settings))
    return objects


def apply_feast_repo(
    *,
    settings: AppSettings | None = None,
    materialize_incremental: bool = False,
    end_date: datetime | None = None,
    store: FeatureStore | None = None,
) -> dict[str, object]:
    """Apply Feast definitions and optionally materialize them incrementally."""
    settings = settings or get_app_settings()
    repo_path = settings.paths.feast_repo_root
    feast_store = store or FeatureStore(repo_path=str(repo_path))
    objects = feast_repo_objects(settings=settings)
    feast_store.apply(objects=objects, partial=False)

    materialize_end_date = end_date
    if materialize_incremental:
        materialize_end_date = materialize_end_date or datetime.now(timezone.utc)
        feast_store.materialize_incremental(materialize_end_date)

    return {
        "repo_path": str(repo_path),
        "applied_object_count": len(objects),
        "materialized_incremental": materialize_incremental,
        "materialize_end_date": (
            materialize_end_date.isoformat() if materialize_end_date is not None else None
        ),
    }


def parse_feast_end_date(value: str) -> datetime:
    """Parse an ISO timestamp for Feast materialization requests."""
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
