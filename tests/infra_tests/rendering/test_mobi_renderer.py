"""Tests for MOBI renderer helper functions and error paths (no external binaries needed)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.mobi_renderer import (
    _process_output_text,
    _truncate_error_context,
    render_mobi,
)


# ── _truncate_error_context ───────────────────────────────────────────────


def test_truncate_error_context_empty_returns_placeholder() -> None:
    """Empty string input returns 'no stderr captured'."""
    assert _truncate_error_context("") == "no stderr captured"


def test_truncate_error_context_whitespace_only_returns_placeholder() -> None:
    """Whitespace-only string is stripped to empty and returns placeholder."""
    assert _truncate_error_context("   \n\t  ") == "no stderr captured"


def test_truncate_error_context_short_string_returns_unchanged() -> None:
    """Short string is returned as-is."""
    assert _truncate_error_context("short") == "short"


def test_truncate_error_context_long_string_truncated_to_500() -> None:
    """A 1000-char string is truncated to the first 500 characters."""
    long_text = "x" * 1000
    result = _truncate_error_context(long_text)
    assert len(result) == 500
    assert result == "x" * 500


def test_truncate_error_context_strips_leading_trailing_whitespace() -> None:
    """Leading/trailing whitespace is stripped before truncation."""
    result = _truncate_error_context("  hello  ")
    assert result == "hello"


# ── _process_output_text ──────────────────────────────────────────────────


def test_process_output_text_none_returns_empty_string() -> None:
    """None input returns empty string."""
    assert _process_output_text(None) == ""


def test_process_output_text_str_returns_str() -> None:
    """String input is returned as-is."""
    assert _process_output_text("text") == "text"


def test_process_output_text_bytes_returns_decoded_str() -> None:
    """Bytes input is decoded to string."""
    assert _process_output_text(b"bytes") == "bytes"


def test_process_output_text_bytes_with_invalid_utf8_uses_replace() -> None:
    """Invalid UTF-8 bytes are decoded with errors='replace'."""
    # \xff is invalid UTF-8
    result = _process_output_text(b"\xff\xfe")
    assert isinstance(result, str)
    assert len(result) > 0


# ── render_mobi error paths ───────────────────────────────────────────────


def test_render_mobi_raises_file_not_found_for_missing_combined_md(tmp_path: Path) -> None:
    """render_mobi raises FileNotFoundError when combined_md does not exist."""
    missing_md = tmp_path / "nonexistent.md"
    output = tmp_path / "out.mobi"
    with pytest.raises(FileNotFoundError):
        render_mobi(missing_md, output)


def test_render_mobi_raises_rendering_error_when_pandoc_missing(tmp_path: Path) -> None:
    """render_mobi raises RenderingError when pandoc binary is not found."""
    src = tmp_path / "combined.md"
    src.write_text("# Title\n\nSome content.\n", encoding="utf-8")
    output = tmp_path / "out.mobi"
    with pytest.raises(RenderingError, match="pandoc binary not found"):
        render_mobi(src, output, pandoc_path="nonexistent-pandoc")


def test_render_mobi_raises_rendering_error_when_calibre_missing(tmp_path: Path) -> None:
    """render_mobi raises RenderingError when calibre binary is not found.

    Uses a real pandoc path if available, otherwise uses 'true' (which exists
    on PATH as a no-op binary that shutil.which will find).
    """
    src = tmp_path / "combined.md"
    src.write_text("# Title\n\nSome content.\n", encoding="utf-8")
    output = tmp_path / "out.mobi"

    # Use 'true' as a guaranteed-present binary that satisfies shutil.which
    # but is NOT pandoc. This tests the calibre-missing path without needing
    # real pandoc installed.
    pandoc_substitute = "true" if shutil.which("true") else "pandoc"
    if not shutil.which(pandoc_substitute):
        pytest.skip("No suitable pandoc substitute binary found on PATH")

    with pytest.raises(RenderingError, match="calibre ebook-convert binary not found"):
        render_mobi(
            src,
            output,
            pandoc_path=pandoc_substitute,
            calibre_path="nonexistent-calibre",
        )


def test_render_mobi_raises_file_not_found_for_missing_bibliography(tmp_path: Path) -> None:
    """render_mobi raises FileNotFoundError when bibliography file does not exist."""
    src = tmp_path / "combined.md"
    src.write_text("# Title\n\nSome content.\n", encoding="utf-8")
    output = tmp_path / "out.mobi"
    missing_bib = tmp_path / "nonexistent.bib"
    with pytest.raises(FileNotFoundError):
        render_mobi(src, output, bibliography=missing_bib)


def test_render_mobi_raises_file_not_found_for_missing_cover(tmp_path: Path) -> None:
    """render_mobi raises FileNotFoundError when cover image does not exist."""
    src = tmp_path / "combined.md"
    src.write_text("# Title\n\nSome content.\n", encoding="utf-8")
    output = tmp_path / "out.mobi"
    missing_cover = tmp_path / "nonexistent.png"
    with pytest.raises(FileNotFoundError):
        render_mobi(src, output, cover_image=missing_cover)
