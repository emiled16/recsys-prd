from __future__ import annotations

from pathlib import Path

from recsys_prd.ingestion.contracts import REQUIRED_FILES


def find_required_files(search_root: Path) -> dict[str, Path]:
    """Locate the required H&M CSV assets under a source tree."""
    matches: dict[str, Path] = {}
    for filename in REQUIRED_FILES:
        candidates = [path for path in search_root.rglob(filename) if path.is_file()]
        if not candidates:
            raise FileNotFoundError(f"Missing required dataset file: {filename}")
        if len(candidates) > 1:
            candidate_list = ", ".join(str(path) for path in candidates)
            raise ValueError(f"Multiple matches found for {filename}: {candidate_list}")
        matches[filename] = candidates[0]
    return matches


def find_images_directory(search_root: Path) -> Path:
    """Locate the single image directory that contains product assets."""
    exact_matches = [
        path
        for path in search_root.rglob("*")
        if path.is_dir() and path.name.lower() == "images"
    ]
    image_dirs = [path for path in exact_matches if count_files(path) > 0]
    if not image_dirs:
        raise FileNotFoundError("Missing required images directory.")
    if len(image_dirs) > 1:
        candidate_list = ", ".join(str(path) for path in image_dirs)
        raise ValueError(f"Multiple image directories found: {candidate_list}")
    return image_dirs[0]


def count_files(root: Path) -> int:
    """Count files recursively under a directory."""
    return sum(1 for path in root.rglob("*") if path.is_file())
