"""Tests for the shared defensive markdown reader.

Zero-mocks: every case writes real files (valid + deliberately invalid UTF-8)
to ``tmp_path`` and exercises the real linters that route through the shared
``read_markdown`` helper. A corrupt fixture must be skipped identically (no
crash, no spurious findings) across every refactored linter.
"""

from __future__ import annotations

from pathlib import Path

from infrastructure.validation.docs._io import read_markdown
from infrastructure.validation.docs.cross_link_lint import find_broken_links
from infrastructure.validation.docs.mermaid_lint import find_mermaid_blocks
from infrastructure.validation.docs.public_audit import collect_public_markdown

# A byte sequence that is valid Latin-1 but invalid UTF-8 (lone 0xFF / 0xFE).
_INVALID_UTF8 = b"# heading\n\xff\xfe not valid utf-8\n"


def test_read_markdown_returns_text_for_valid_file(tmp_path: Path) -> None:
    md = tmp_path / "ok.md"
    md.write_text("# hello\n", encoding="utf-8")
    assert read_markdown(md) == "# hello\n"


def test_read_markdown_returns_none_on_invalid_utf8(tmp_path: Path) -> None:
    md = tmp_path / "bad.md"
    md.write_bytes(_INVALID_UTF8)
    assert read_markdown(md) is None


def test_read_markdown_returns_none_on_missing_file(tmp_path: Path) -> None:
    assert read_markdown(tmp_path / "nope.md") is None


def test_consistency_shared_reexports_read_markdown() -> None:
    """Back-compat: consistency/_shared must still expose the same callable."""
    from infrastructure.validation.docs.consistency import _shared

    assert _shared.read_markdown is read_markdown


def test_corrupt_fixture_skipped_by_cross_link_lint(tmp_path: Path) -> None:
    """A bad-UTF-8 file is skipped; a valid sibling is still linted."""
    (tmp_path / "bad.md").write_bytes(_INVALID_UTF8)
    valid = tmp_path / "index.md"
    valid.write_text("[broken](missing.md)\n", encoding="utf-8")

    broken = find_broken_links([tmp_path])

    # No crash; the corrupt file contributes nothing and the valid one is linted.
    assert [b.file for b in broken] == [valid]
    assert all(b.file != tmp_path / "bad.md" for b in broken)


def test_corrupt_fixture_skipped_by_mermaid_lint(tmp_path: Path) -> None:
    """A bad-UTF-8 file is skipped; mermaid blocks in a valid sibling are found."""
    (tmp_path / "bad.md").write_bytes(_INVALID_UTF8)
    valid = tmp_path / "diagram.md"
    valid.write_text("```mermaid\nflowchart TD\n  A --> B\n```\n", encoding="utf-8")

    blocks = find_mermaid_blocks([tmp_path])

    # No crash; exactly one block from the valid file, none from the corrupt one.
    assert len(blocks) == 1
    assert blocks[0].file == valid


def test_corrupt_fixture_skipped_by_public_audit(tmp_path: Path) -> None:
    """collect_public_markdown skips the corrupt file and records the valid one."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "bad.md").write_bytes(_INVALID_UTF8)
    (docs / "good.md").write_text("# good\n[link](x.md)\n", encoding="utf-8")

    records = collect_public_markdown(tmp_path)

    paths = {str(r.path) for r in records}
    assert "docs/good.md" in paths
    assert "docs/bad.md" not in paths
