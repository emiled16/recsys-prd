from __future__ import annotations

from feast import FileSource
from feast.data_format import ParquetFormat

from recsys_prd.config import get_app_settings


def _file_uri(path: str) -> str:
    return f"file://{path}"


settings = get_app_settings()
paths = settings.paths

customers_normalized_source = FileSource(
    name="customers_normalized_source",
    path=_file_uri(str(paths.normalized_root / "customers" / "customers_normalized.parquet")),
    file_format=ParquetFormat(),
)

products_normalized_source = FileSource(
    name="products_normalized_source",
    path=_file_uri(str(paths.normalized_root / "products" / "products_normalized.parquet")),
    file_format=ParquetFormat(),
)

product_images_manifest_source = FileSource(
    name="product_images_manifest_source",
    path=_file_uri(str(paths.normalized_root / "images" / "product_images_manifest.parquet")),
    file_format=ParquetFormat(),
)

transactions_normalized_source = FileSource(
    name="transactions_normalized_source",
    path=_file_uri(str(paths.normalized_root / "transactions" / "transactions_normalized.parquet")),
    file_format=ParquetFormat(),
    timestamp_field="event_time",
)

point_in_time_training_dataset_source = FileSource(
    name="point_in_time_training_dataset_source",
    path=_file_uri(
        str(
            paths.features_offline_root
            / "training_dataset"
            / "point_in_time_training_dataset.parquet"
        )
    ),
    file_format=ParquetFormat(),
    timestamp_field="label_timestamp",
)

session_intent_snapshot_source = FileSource(
    name="session_intent_snapshot_source",
    path=_file_uri(
        str(paths.features_root / "online_snapshots" / "session_intent_features.parquet")
    ),
    file_format=ParquetFormat(),
    timestamp_field="last_event_time",
)

customer_realtime_snapshot_source = FileSource(
    name="customer_realtime_snapshot_source",
    path=_file_uri(
        str(paths.features_root / "online_snapshots" / "customer_realtime_features.parquet")
    ),
    file_format=ParquetFormat(),
    timestamp_field="event_timestamp",
)

article_realtime_snapshot_source = FileSource(
    name="article_realtime_snapshot_source",
    path=_file_uri(
        str(paths.features_root / "online_snapshots" / "article_realtime_features.parquet")
    ),
    file_format=ParquetFormat(),
    timestamp_field="event_timestamp",
)
