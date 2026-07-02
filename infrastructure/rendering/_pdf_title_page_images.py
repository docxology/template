"""Cover-image resolution and LaTeX includegraphics blocks for the title page."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from infrastructure.core.logging.utils import get_logger

__all__ = [
    "_configured_image_path",
    "_cover_image_block",
    "_cover_image_path",
    "_has_available_paper_cover",
    "_image_block",
    "_image_latex_path",
    "_section_cover_image_path",
]

logger = get_logger(__name__)


def _cover_image_path(config: dict[str, Any], config_file: Path) -> Path | None:
    """Resolve the configured book or paper cover image path, if any."""
    for section_name in ("book", "paper"):
        image_path = _section_cover_image_path(config, config_file, section_name)
        if image_path is not None:
            return image_path
    return None


def _section_cover_image_path(config: dict[str, Any], config_file: Path, section_name: str) -> Path | None:
    """Resolve a cover image from one metadata section only."""
    cover: dict[str, Any] | None = None
    section = config.get(section_name, {}) or {}
    if not isinstance(section, dict):
        return None
    candidate = section.get("cover", {}) or {}
    if isinstance(candidate, dict) and candidate.get("image"):
        cover = candidate
    if cover is None:
        return None
    raw_image = cover.get("image")
    if not raw_image:
        return None
    return _configured_image_path(raw_image, config_file)


def _configured_image_path(raw_image: object, config_file: Path) -> Path | None:
    """Resolve a config-declared image path near the manuscript/output tree."""
    image_path = Path(str(raw_image))
    if not str(image_path):
        return None
    if image_path.is_absolute():
        return image_path
    candidates = [config_file.parent / image_path]
    project_roots = [config_file.parent.parent]
    if config_file.parent.name == "manuscript" and config_file.parent.parent.name == "output":
        project_roots.append(config_file.parent.parent.parent)
    for root in project_roots:
        candidates.extend(
            [
                root / image_path,
                root / "manuscript" / image_path,
                root / "output" / image_path,
            ]
        )
    for parent in config_file.parents:
        candidates.append(parent / "manuscript" / image_path)
    unique_candidates: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        unique_candidates.append(candidate)
    for candidate in unique_candidates:
        if candidate.is_file():
            return candidate
    return unique_candidates[0]


def _image_latex_path(image_path: Path, config_file: Path) -> str:
    """Return a LaTeX-safe image path without embedding local absolute paths."""
    manuscript_dir = config_file.parent
    parent = manuscript_dir.parent
    if manuscript_dir.name == "manuscript":
        output_root = parent if parent.name == "output" else parent / "output"
        latex_dir = output_root / "pdf"
    else:
        latex_dir = manuscript_dir
    try:
        return Path(os.path.relpath(image_path.resolve(), latex_dir.resolve())).as_posix()
    except OSError:
        return image_path.as_posix() if not image_path.is_absolute() else image_path.name


def _image_block(
    image_path: Path | None,
    config_file: Path,
    *,
    height: str,
    width: str = r"0.98\textwidth",
) -> str:
    """Return a LaTeX includegraphics block for a configured image."""
    if image_path is None:
        return ""
    if not image_path.is_file():
        logger.warning("Configured image does not exist: %s", image_path)
        return ""
    latex_image = _image_latex_path(image_path, config_file)
    return (
        r"\includegraphics[width="
        + width
        + r",height="
        + height
        + r",keepaspectratio]{"
        + r"\detokenize{"
        + latex_image
        + r"}}"
    )


def _cover_image_block(
    config: dict[str, Any],
    config_file: Path,
    *,
    height: str,
    section_name: str | None = None,
) -> str:
    """Return a LaTeX includegraphics block for the configured cover image."""
    image_path = (
        _section_cover_image_path(config, config_file, section_name)
        if section_name is not None
        else _cover_image_path(config, config_file)
    )
    return _image_block(image_path, config_file, height=height)


def _has_available_paper_cover(config: dict[str, Any], config_file: Path | None) -> bool:
    """Return true when a paper cover image is configured and present."""
    if config_file is None:
        return False
    paper = config.get("paper", {}) or {}
    if not isinstance(paper, dict):
        return False
    cover = paper.get("cover", {}) or {}
    if not isinstance(cover, dict) or not cover.get("image"):
        return False
    cover_image = _section_cover_image_path(config, config_file, "paper")
    return cover_image is not None and cover_image.is_file()
