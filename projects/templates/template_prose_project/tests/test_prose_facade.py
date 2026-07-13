"""Tests for src.prose_facade — protocols, helpers, and parse_bib_keys.

These are the negative-control and edge-case tests for the project's
protocol layer. The facade intentionally imports no infrastructure;
every test here is pure-Python with no subprocess calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from src.prose_facade import HeadingView, parse_bib_keys, render_outline


# ---------------------------------------------------------------------------
# HeadingView
# ---------------------------------------------------------------------------


class TestHeadingView:
    def test_basic_construction(self):
        h = HeadingView(level=1, title="Introduction")
        assert h.level == 1
        assert h.title == "Introduction"

    def test_frozen_immutable(self):
        h = HeadingView(level=2, title="Methods")
        with pytest.raises((AttributeError, TypeError)):
            h.level = 3  # type: ignore[misc]  # frozen dataclass — assignment must raise

    def test_equality(self):
        assert HeadingView(level=1, title="A") == HeadingView(level=1, title="A")
        assert HeadingView(level=1, title="A") != HeadingView(level=2, title="A")

    def test_repr_roundtrip(self):
        h = HeadingView(level=3, title="Deep")
        # repr must contain both fields for debuggability
        r = repr(h)
        assert "3" in r
        assert "Deep" in r


# ---------------------------------------------------------------------------
# render_outline — happy path and fallback paths
# ---------------------------------------------------------------------------


@dataclass
class _FakeStructure:
    """Minimal stand-in for StructureReportLike.

    Carries all attributes required by the StructureReportLike protocol so
    render_outline can be called without infrastructure imports.
    """

    headings: list[object]
    has_skipped_level: bool = False
    has_h1: bool = True


@dataclass
class _HeadingWithTitle:
    level: int
    title: str


@dataclass
class _HeadingNoTitle:
    """Heading that deliberately has no `title` attribute.

    render_outline uses getattr(heading, 'title', heading) so the heading
    object itself becomes the title string. This tests the fallback branch
    on prose_facade.py line 71.
    """

    level: int


class TestRenderOutline:
    def test_contiguous_levels(self):
        structure = _FakeStructure(
            headings=[
                _HeadingWithTitle(level=1, title="Intro"),
                _HeadingWithTitle(level=2, title="Background"),
                _HeadingWithTitle(level=3, title="Prior Work"),
            ]
        )
        out = render_outline(structure)
        assert out == "- Intro\n  - Background\n    - Prior Work"

    def test_single_heading(self):
        structure = _FakeStructure(headings=[_HeadingWithTitle(level=1, title="Only")])
        out = render_outline(structure)
        assert out == "- Only"

    def test_empty_headings(self):
        structure = _FakeStructure(headings=[])
        out = render_outline(structure)
        assert out == ""

    def test_heading_without_title_attribute_uses_str_of_object(self):
        """Fallback: getattr(heading, 'title', heading) → str(heading).

        This covers the branch on prose_facade.py line 71 that was
        previously uncovered (heading has no title attribute).
        """
        heading = _HeadingNoTitle(level=1)
        structure = _FakeStructure(headings=[heading])
        out = render_outline(structure)
        # The fallback converts the heading object to its string repr.
        # We just verify it produces a bullet line without raising.
        assert out.startswith("- ")

    def test_indent_scales_with_level(self):
        structure = _FakeStructure(
            headings=[
                _HeadingWithTitle(level=1, title="L1"),
                _HeadingWithTitle(level=4, title="L4"),
            ]
        )
        lines = render_outline(structure).splitlines()
        assert lines[0] == "- L1"
        assert lines[1] == "      - L4"  # 6 spaces = 3 * 2 (level-1=3)


# ---------------------------------------------------------------------------
# parse_bib_keys — negative controls
# ---------------------------------------------------------------------------


class TestParseBibKeys:
    def test_absent_path_returns_empty_set(self, tmp_path: Path):
        """Non-existent file → empty set (covers prose_facade.py line 83)."""
        missing = tmp_path / "nonexistent.bib"
        assert not missing.exists()
        result = parse_bib_keys(missing)
        assert result == set()

    def test_directory_not_a_file(self, tmp_path: Path):
        """Directory path (not a file) → empty set."""
        result = parse_bib_keys(tmp_path)
        assert result == set()

    def test_typical_bib_file(self, tmp_path: Path):
        bib = tmp_path / "refs.bib"
        bib.write_text(
            "@article{smith2020paper, title={T}, author={S}, year={2020}}\n"
            "@book{jones2021book, title={B}, author={J}, year={2021}}\n",
            encoding="utf-8",
        )
        keys = parse_bib_keys(bib)
        assert "smith2020paper" in keys
        assert "jones2021book" in keys
        assert len(keys) == 2

    def test_comment_block_not_extracted_as_key(self, tmp_path: Path):
        """@comment{} blocks must NOT produce citation keys.

        The updated regex uses a negative lookahead ``(?!comment\\b)`` to
        skip @comment entries. This prevents preamble comments like
        ``@comment{This is a preamble}`` from polluting the key set with
        ``This`` as a spurious citation key.
        """
        bib = tmp_path / "refs.bib"
        bib.write_text(
            "@comment{This is a preamble comment, not a key}\n@article{real_key, title={T}, author={A}, year={2020}}\n",
            encoding="utf-8",
        )
        keys = parse_bib_keys(bib)
        # "real_key" must always be present
        assert "real_key" in keys
        # "This" must NOT appear — it is part of the comment body, not a bib key
        assert "This" not in keys

    def test_empty_bib_file(self, tmp_path: Path):
        bib = tmp_path / "empty.bib"
        bib.write_text("", encoding="utf-8")
        result = parse_bib_keys(bib)
        assert result == set()

    def test_only_comments(self, tmp_path: Path):
        """A bib that contains only % line-comments → empty set of keys."""
        bib = tmp_path / "comments.bib"
        bib.write_text(
            "% This is a comment line\n% Another comment\n",
            encoding="utf-8",
        )
        result = parse_bib_keys(bib)
        assert result == set()

    def test_returns_set_type(self, tmp_path: Path):
        bib = tmp_path / "refs.bib"
        bib.write_text("@article{k1, title={T}}\n", encoding="utf-8")
        result = parse_bib_keys(bib)
        assert isinstance(result, set)
