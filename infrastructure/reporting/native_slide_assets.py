"""Exact source-owned Beamer figure resolution and private reference inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def source_slide_images(root: Path, plan: Any, contract: Any, reader: SnapshotReader) -> dict[str, bytes]:
    """Reproduce current SDK's declared figures-directory filename resolution.

    fix_slides_figure_paths maps current generated images to ../figures/name.
    The admitted current pipeline's own figures directory is the sole native
    Beamer asset authority; unrelated manuscript files are never fallback data.
    """
    images = {}
    for row in contract.occurrences:
        if row.kind != "image":
            continue
        url = urlsplit(row.target)
        if url.scheme or url.netloc or url.query or url.fragment or "\\" in url.path:
            raise ValueError("source slide image is not one exact declared local figure")
        filename = Path(url.path).name
        if not filename or filename in {".", ".."}:
            raise ValueError("source slide figure has no original lexical filename")
        figure = plan.figures_directory / filename
        if not figure.is_relative_to(root):
            raise ValueError("source slide figures directory escapes its admitted source DATA")
        images[row.target] = reader.read(figure.relative_to(root).as_posix()).content
    if not reader.unchanged():
        raise ValueError("source-owned slide figure bytes changed during admission")
    return images


def freeze_source_slide_figures(root: Path, directory: Path, images: dict[str, bytes]) -> None:
    """Keep current SDK ../figures paths inside the fresh reference directory."""
    from infrastructure.reporting.native_format_acceptance_contracts import create_private_native_directory

    if not images:
        return
    create_private_native_directory(root, directory)
    selected: dict[str, bytes] = {}
    for target, content in images.items():
        name = Path(urlsplit(target).path).name
        if name in selected and selected[name] != content:
            raise ValueError("source slide figures collapse two different original pixel identities")
        selected[name] = content
    for name, content in selected.items():
        atomic_write_bytes_confined(root, directory / name, content, mode=0o600)
