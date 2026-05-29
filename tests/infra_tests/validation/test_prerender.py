"""Tests for pre-render validation leaf and markdown strip helpers."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.validation.content.markdown_strip import (
    strip_code_and_math,
    strip_fences,
    strip_inline_code,
    strip_math,
)
from infrastructure.validation.content.prerender import prevalidate_for_render


def test_strip_fences_removes_code_blocks() -> None:
    text = "before\n```python\nx = 1\n```\nafter"
    assert "x = 1" not in strip_fences(text)
    assert "before" in strip_fences(text)


def test_strip_inline_code_removes_backticks() -> None:
    assert "`code`" not in strip_inline_code("use `code` here")


def test_strip_math_removes_dollar_math() -> None:
    assert "$x$" not in strip_math("value $x$ end")


def test_strip_code_and_math_composes_helpers() -> None:
    text = dedent(
        """
        prose |pipe|
        ```py
        |ignored|
        ```
        $a$
        """
    ).strip()
    stripped = strip_code_and_math(text)
    assert "|ignored|" not in stripped
    assert "$a$" not in stripped
    assert "|pipe|" in stripped


def test_prevalidate_for_render_passes_clean_manuscript(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "01_intro.md").write_text("Hello world.\n", encoding="utf-8")
    (manuscript / "references.bib").write_text("@article{a, title={A}}\n", encoding="utf-8")

    prevalidate_for_render(manuscript, repo_root=tmp_path)


def test_prevalidate_for_render_raises_on_undefined_citation(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    (manuscript / "01_intro.md").write_text("See [@missing].\n", encoding="utf-8")
    (manuscript / "references.bib").write_text("@article{a, title={A}}\n", encoding="utf-8")

    with pytest.raises(RenderingError, match="blocker"):
        prevalidate_for_render(manuscript, repo_root=tmp_path)
