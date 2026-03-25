"""Tests for infrastructure.rendering._pdf_markdown_combine."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._pdf_markdown_combine import combine_manuscript_markdown_sections


def test_combine_single_file(tmp_path: Path) -> None:
    f = tmp_path / "a.md"
    f.write_text("# Hi\n", encoding="utf-8")
    out = combine_manuscript_markdown_sections([f])
    assert "# Hi" in out


def test_combine_empty_sources_raises() -> None:
    with pytest.raises(RenderingError, match="empty"):
        combine_manuscript_markdown_sections([])


def test_combine_strips_bom(tmp_path: Path) -> None:
    f = tmp_path / "b.md"
    f.write_bytes(b"\xef\xbb\xbf# Title\n")
    out = combine_manuscript_markdown_sections([f])
    assert out.startswith("# Title")
