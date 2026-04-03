from __future__ import annotations

from feast import FileSource
from feast.data_format import ParquetFormat

from feast_repo.source_defs.config import resolved_paths

paths = resolved_paths()

session_intent_snapshot_source = FileSource(
    name="session_intent_snapshot_source",
    path=str(paths.features_root / "online_snapshots" / "session_intent_features.parquet"),
    file_format=ParquetFormat(),
    timestamp_field="last_event_time",
)

customer_realtime_snapshot_source = FileSource(
    name="customer_realtime_snapshot_source",
    path=str(paths.features_root / "online_snapshots" / "customer_realtime_features.parquet"),
    file_format=ParquetFormat(),
    timestamp_field="event_timestamp",
)

article_realtime_snapshot_source = FileSource(
    name="article_realtime_snapshot_source",
    path=str(paths.features_root / "online_snapshots" / "article_realtime_features.parquet"),
    file_format=ParquetFormat(),
    timestamp_field="event_timestamp",
)
