from __future__ import annotations

from feast import FileSource
from feast.data_format import ParquetFormat

from feast_repo.source_defs.config import resolved_paths

paths = resolved_paths()

point_in_time_training_dataset_source = FileSource(
    name="point_in_time_training_dataset_source",
    path=str(
        paths.features_offline_root
        / "training_dataset"
        / "point_in_time_training_dataset.parquet"
    ),
    file_format=ParquetFormat(),
    timestamp_field="label_timestamp",
)
