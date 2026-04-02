from __future__ import annotations

from datetime import datetime, timezone

from feast import FeatureStore

from recsys_prd.config import AppSettings, get_app_settings


def feast_repo_objects() -> list:
    """Return the Feast repo objects in dependency-safe apply order."""
    from feast_repo import entities, offline_views, online_views, sources

    return [
        entities.customer,
        entities.article,
        entities.customer_session,
        sources.customers_normalized_source,
        sources.products_normalized_source,
        sources.product_images_manifest_source,
        sources.transactions_normalized_source,
        sources.point_in_time_training_dataset_source,
        sources.session_intent_snapshot_source,
        sources.customer_realtime_snapshot_source,
        sources.article_realtime_snapshot_source,
        offline_views.customer_profile_base,
        offline_views.product_catalog_base,
        offline_views.product_image_manifest_base,
        offline_views.customer_activity_base,
        offline_views.article_demand_base,
        offline_views.customer_article_affinity_base,
        offline_views.customer_profile_features,
        offline_views.article_catalog_features,
        offline_views.customer_activity_features,
        offline_views.article_demand_features,
        offline_views.customer_article_affinity_features,
        online_views.session_intent_push_source,
        online_views.customer_realtime_push_source,
        online_views.article_realtime_push_source,
        online_views.session_intent_features,
        online_views.customer_realtime_features,
        online_views.article_realtime_features,
    ]


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
    objects = feast_repo_objects()
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
