from __future__ import annotations

import shutil
from pathlib import Path


def copy_file(source: Path, destination: Path, *, replace: bool) -> None:
    """Copy one file into the target layout."""
    if destination.exists() and not replace:
        raise FileExistsError(
            f"Destination already exists: {destination}. Pass replace=True to overwrite."
        )
    shutil.copy2(source, destination)


def copy_tree(source: Path, destination: Path, *, replace: bool) -> None:
    """Copy a directory tree into the target layout."""
    if destination.exists():
        if not replace:
            raise FileExistsError(
                f"Destination already exists: {destination}. Pass replace=True to overwrite."
            )
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
