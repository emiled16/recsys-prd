from __future__ import annotations

from feast import FileSource
from feast.data_format import ParquetFormat

from feast_repo.source_defs.config import resolved_paths

paths = resolved_paths()

customers_normalized_source = FileSource(
    name="customers_normalized_source",
    path=str(paths.normalized_root / "customers" / "customers_normalized.parquet"),
    file_format=ParquetFormat(),
)

products_normalized_source = FileSource(
    name="products_normalized_source",
    path=str(paths.normalized_root / "products" / "products_normalized.parquet"),
    file_format=ParquetFormat(),
)

product_images_manifest_source = FileSource(
    name="product_images_manifest_source",
    path=str(paths.normalized_root / "images" / "product_images_manifest.parquet"),
    file_format=ParquetFormat(),
)

transactions_normalized_source = FileSource(
    name="transactions_normalized_source",
    path=str(paths.normalized_root / "transactions" / "transactions_normalized.parquet"),
    file_format=ParquetFormat(),
    timestamp_field="event_time",
)
