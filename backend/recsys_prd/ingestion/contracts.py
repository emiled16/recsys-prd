from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REQUIRED_FILES = {
    "articles.csv": ("articles", "articles.csv"),
    "customers.csv": ("customers", "customers.csv"),
    "transactions_train.csv": ("transactions", "transactions_train.csv"),
}


@dataclass(frozen=True)
class IngestionResult:
    source: str
    target_root: Path
    customers_path: Path
    articles_path: Path
    transactions_path: Path
    images_root: Path
    image_count: int
    manifest_path: Path
