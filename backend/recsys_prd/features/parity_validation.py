from __future__ import annotations

import json
from pathlib import Path

from recsys_prd.config import AppSettings, get_app_settings
from recsys_prd.features.online_requirements import online_feature_requirements
from recsys_prd.features.online_service import OnlineFeatureService
from recsys_prd.io.json_ops import write_json
from recsys_prd.io.tabular_ops import read_tabular_rows

OFFLINE_ONLINE_MAPPINGS = {
    "customer_realtime_features": [
        ("purchase_count_30d_rt", "customer_purchase_count_30d", "count_gte"),
        ("days_since_last_purchase_rt", "customer_days_since_last_purchase", "days_lte"),
    ],
    "article_realtime_features": [
        ("purchase_count_7d_rt", "article_purchase_count_7d", "count_gte"),
    ],
}


def validate_feature_parity_and_freshness(
    *,
    features_root: Path | None = None,
    reports_root: Path | None = None,
    settings: AppSettings | None = None,
    online_feature_service: OnlineFeatureService | None = None,
) -> dict:
    """Validate online freshness targets and offline-online feature parity mappings."""
    settings = settings or get_app_settings()
    features_root = features_root or settings.paths.features_root
    reports_root = reports_root or settings.paths.reports_root
    training_dataset_path = (
        features_root / "offline" / "training_dataset" / "point_in_time_training_dataset.parquet"
    )
    training_dataset_rows = read_tabular_rows(training_dataset_path)
    online_store_root = features_root / "online_bootstrap"
    if online_feature_service is None:
        if online_store_root.exists():
            online_feature_service = OnlineFeatureService(store_root=online_store_root)
        else:
            online_feature_service = OnlineFeatureService(settings=settings)

    freshness_checks = _validate_freshness(online_store_root)
    parity_checks = _validate_parity(
        training_dataset_rows,
        online_store_root,
        online_feature_service,
    )

    result = {
        "ok": all(check["ok"] for check in freshness_checks.values())
        and all(check["ok"] for check in parity_checks.values()),
        "freshness_checks": freshness_checks,
        "parity_checks": parity_checks,
    }
    write_json(reports_root / "data_quality" / "feature_parity_and_freshness.json", result)
    return result


def _validate_freshness(online_store_root: Path) -> dict[str, dict]:
    checks: dict[str, dict] = {}
    for requirement in online_feature_requirements():
        filename = f"{requirement.name}.json"
        path = online_store_root / filename
        payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        checks[requirement.name] = {
            "ok": len(payload) > 0,
            "freshness_target_seconds": requirement.freshness_target_seconds,
            "row_count": len(payload),
        }
    return checks


def _validate_parity(
    training_dataset_rows: list[dict[str, str]],
    online_store_root: Path,
    online_feature_service: OnlineFeatureService,
) -> dict[str, dict]:
    if not training_dataset_rows:
        return {
            "customer_realtime_features": {"ok": False, "reason": "missing_training_dataset"},
            "article_realtime_features": {"ok": False, "reason": "missing_training_dataset"},
        }

    latest_row = training_dataset_rows[-1]
    return {
        "customer_realtime_features": _compare_feature_pairs(
            store_payload=online_feature_service.get_customer_realtime_features(
                customer_id=latest_row["customer_id"]
            )
            or _read_json_payload(online_store_root / "customer_realtime_features.json").get(
                latest_row["customer_id"],
                {},
            ),
            training_row=latest_row,
            mappings=OFFLINE_ONLINE_MAPPINGS["customer_realtime_features"],
        ),
        "article_realtime_features": _compare_feature_pairs(
            store_payload=online_feature_service.get_article_realtime_features(
                article_id=latest_row["article_id"]
            )
            or _read_json_payload(online_store_root / "article_realtime_features.json").get(
                latest_row["article_id"],
                {},
            ),
            training_row=latest_row,
            mappings=OFFLINE_ONLINE_MAPPINGS["article_realtime_features"],
        ),
    }


def _compare_feature_pairs(
    *,
    store_payload: dict,
    training_row: dict[str, str],
    mappings: list[tuple[str, str, str]],
) -> dict:
    comparisons = []
    for online_name, offline_name, comparator in mappings:
        online_value = str(store_payload.get(online_name, ""))
        offline_value = str(training_row.get(offline_name, ""))
        comparisons.append(
            {
                "online_feature": online_name,
                "offline_feature": offline_name,
                "online_value": online_value,
                "offline_value": offline_value,
                "comparator": comparator,
                "matches": _compare_values(online_value, offline_value, comparator),
            }
        )
    return {
        "ok": all(item["matches"] for item in comparisons),
        "comparisons": comparisons,
    }


def _compare_values(online_value: str, offline_value: str, comparator: str) -> bool:
    if comparator == "count_gte":
        return int(float(online_value or 0)) >= int(float(offline_value or 0))
    if comparator == "days_lte":
        offline_days = int(float(offline_value or -1))
        online_days = int(float(online_value or -1))
        if offline_days < 0:
            return online_days >= -1
        return online_days <= offline_days
    return online_value == offline_value


def _read_json_payload(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
