from __future__ import annotations

import tempfile
from pathlib import Path
from zipfile import ZipFile, is_zipfile

from recsys_prd.ingestion.contracts import IngestionResult, REQUIRED_FILES
from recsys_prd.ingestion.copy_ops import copy_file, copy_tree
from recsys_prd.ingestion.discovery import count_files, find_images_directory, find_required_files
from recsys_prd.ingestion.manifest import write_manifest
from recsys_prd.paths import RAW_HM_ROOT


def ingest_hm_raw(source: Path, replace: bool = False) -> IngestionResult:
    """Ingest raw H&M dataset assets into the local `data/raw/hm` layout."""
    source = source.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Source path does not exist: {source}")

    if is_zipfile(source):
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_root = Path(temp_dir) / "extracted"
            with ZipFile(source) as archive:
                archive.extractall(extract_root)
            return _ingest_from_directory(extract_root, source, replace=replace, source_kind="zip")

    if source.is_dir():
        return _ingest_from_directory(source, source, replace=replace, source_kind="directory")

    raise ValueError("Source must be a directory or a zip archive.")


def _ingest_from_directory(
    search_root: Path,
    source_reference: Path,
    *,
    replace: bool,
    source_kind: str,
) -> IngestionResult:
    matches = find_required_files(search_root)
    images_dir = find_images_directory(search_root)

    RAW_HM_ROOT.mkdir(parents=True, exist_ok=True)
    copied_paths = _copy_tabular_assets(matches, replace=replace)
    images_root = _copy_images(images_dir, replace=replace)
    manifest_path = _write_ingestion_manifest(
        source_kind=source_kind,
        source_reference=source_reference,
        copied_paths=copied_paths,
        images_root=images_root,
    )

    return IngestionResult(
        source=str(source_reference),
        target_root=RAW_HM_ROOT,
        customers_path=copied_paths["customers.csv"],
        articles_path=copied_paths["articles.csv"],
        transactions_path=copied_paths["transactions_train.csv"],
        images_root=images_root,
        image_count=count_files(images_root),
        manifest_path=manifest_path,
    )


def _copy_tabular_assets(matches: dict[str, Path], *, replace: bool) -> dict[str, Path]:
    copied_paths: dict[str, Path] = {}
    for filename, (subdir, target_name) in REQUIRED_FILES.items():
        destination_dir = RAW_HM_ROOT / subdir
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination_path = destination_dir / target_name
        copy_file(matches[filename], destination_path, replace=replace)
        copied_paths[filename] = destination_path
    return copied_paths


def _copy_images(images_dir: Path, *, replace: bool) -> Path:
    images_root = RAW_HM_ROOT / "images"
    copy_tree(images_dir, images_root, replace=replace)
    return images_root


def _write_ingestion_manifest(
    *,
    source_kind: str,
    source_reference: Path,
    copied_paths: dict[str, Path],
    images_root: Path,
) -> Path:
    manifest_dir = RAW_HM_ROOT / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / "ingestion_manifest.json"
    write_manifest(
        manifest_path=manifest_path,
        source_kind=source_kind,
        source_path=source_reference,
        target_root=RAW_HM_ROOT,
        customers_path=copied_paths["customers.csv"],
        articles_path=copied_paths["articles.csv"],
        transactions_path=copied_paths["transactions_train.csv"],
        images_root=images_root,
        image_count=count_files(images_root),
    )
    return manifest_path
