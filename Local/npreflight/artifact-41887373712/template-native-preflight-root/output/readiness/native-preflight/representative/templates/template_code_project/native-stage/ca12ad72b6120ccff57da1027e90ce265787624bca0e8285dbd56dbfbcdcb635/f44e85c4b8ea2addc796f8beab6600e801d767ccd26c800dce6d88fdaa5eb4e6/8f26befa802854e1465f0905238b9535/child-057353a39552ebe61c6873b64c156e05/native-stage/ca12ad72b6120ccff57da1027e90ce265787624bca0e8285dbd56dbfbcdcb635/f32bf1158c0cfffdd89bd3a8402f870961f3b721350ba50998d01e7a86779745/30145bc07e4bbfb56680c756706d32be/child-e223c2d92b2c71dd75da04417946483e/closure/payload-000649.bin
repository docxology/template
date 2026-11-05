"""Deterministic local publication of the unchanged Source web font cohort."""

from __future__ import annotations

from pathlib import Path

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.rendering._web_font_assets import source_web_font_javascript

SOURCE_WEB_FONT_ASSET = "assets/source-web-fonts.js"
_MAX_ASSET_BYTES = 8 * 1024 * 1024


def shared_web_font_script(output_directory: Path) -> str:
    """Publish one exact cohort per directory and return its relative script tag.

    The directory is a physical output owner, never a resolved symlink. The
    classic script also works for plain-file readers; no fetch or remote font
    fallback is introduced. Export the directory and its assets together.
    """
    root = output_directory.absolute()
    target = root / SOURCE_WEB_FONT_ASSET
    content = source_web_font_javascript().encode("utf-8")
    if len(content) > _MAX_ASSET_BYTES:
        raise ValueError("Source web font asset exceeds its finite publication budget")
    try:
        previous = read_bytes_confined(root, target, max_bytes=_MAX_ASSET_BYTES)
    except FileNotFoundError:
        previous = None
    except OSError as exc:
        raise ValueError("Source web font asset is not a confined regular file") from exc
    if previous != content:
        atomic_write_bytes_confined(root, target, content)
    return '<script data-template-source-font-loader src="' + SOURCE_WEB_FONT_ASSET + '"></script>\n'
