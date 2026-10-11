"""Exact source-helper byte binding for copied standalone browser drivers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import atomic_write_bytes_confined
from infrastructure.reporting.native_format_html_source_metadata import remaining_seconds
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader


def bind_html_font_driver(root: Path, directory: Path, reader: SnapshotReader, *, deadline: float) -> dict[str, Any]:
    remaining_seconds(deadline)
    sdk_root = Path(__file__).absolute().parents[2]
    sdk_reader = SnapshotReader(sdk_root, native_producer_operation=current_native_producer_operation())
    source = sdk_reader.read("infrastructure/reporting/native_format_html_platform_font_dom.py")
    target = directory / "native_format_html_platform_font_dom.py"
    atomic_write_bytes_confined(root, target, source.content, mode=0o600)
    consumed = reader.read(target.relative_to(root).as_posix())
    if consumed.content != source.content or not sdk_reader.unchanged():
        raise ValueError("native glyph font observer SDK copy changed")
    result = {
        "source": {"path": source.relative, "sha256": source.sha256},
        "consumed": {"path": consumed.relative, "sha256": consumed.sha256},
    }
    remaining_seconds(deadline)
    return result


def replay_html_font_driver(
    root: Path,
    directory: Path,
    reader: SnapshotReader,
    binding: dict[str, Any],
    driver: dict[str, Any],
    *,
    deadline: float,
) -> None:
    remaining_seconds(deadline)
    sdk_root = Path(__file__).absolute().parents[2]
    sdk_reader = SnapshotReader(sdk_root, native_producer_operation=current_native_producer_operation())
    source = sdk_reader.read("infrastructure/reporting/native_format_html_platform_font_dom.py")
    consumed = reader.read((directory / "native_format_html_platform_font_dom.py").relative_to(root).as_posix())
    expected = {
        "source": {"path": source.relative, "sha256": source.sha256},
        "consumed": {"path": consumed.relative, "sha256": consumed.sha256},
    }
    if (
        binding != expected
        or source.content != consumed.content
        or driver.get("platform_font_observer_sha256") != source.sha256
        or not sdk_reader.unchanged()
    ):
        raise ValueError("native glyph font observer actual source/copy/result binding changed")
    remaining_seconds(deadline)
