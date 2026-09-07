"""Accessible Beamer regressions for atomic code-frame geometry."""

from __future__ import annotations

from typing import Any

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    compose_accessible_pandoc_document,
)
from infrastructure.rendering._slides_beamer import transform_beamer_latex
from infrastructure.rendering.config import RenderingConfig


def _header(title: str) -> dict[str, Any]:
    return {
        "t": "Header",
        "c": [2, ["", [], []], [{"t": "Str", "c": word} for word in title.split()]],
    }


def _code(source: str, language: str) -> dict[str, Any]:
    return {"t": "CodeBlock", "c": [["", [language], []], source]}


def _document(*blocks: dict[str, Any]) -> dict[str, Any]:
    return {"pandoc-api-version": [1, 23, 1], "meta": {}, "blocks": list(blocks)}


def _inline_text(value: object) -> str:
    if isinstance(value, list):
        return "".join(_inline_text(item) for item in value)
    if not isinstance(value, dict):
        return ""
    tag = value.get("t")
    content = value.get("c")
    if tag == "Space":
        return " "
    if tag == "LineBreak":
        return "\n"
    if tag == "Code" and isinstance(content, list) and len(content) == 2:
        return str(content[1])
    return _inline_text(content)


def test_long_shell_commands_reflow_at_whitespace_with_complete_tokens() -> None:
    source = "uv run --extra dev python scripts/check_coverage.py\n    uv run python scripts/make_variables.py"

    composition = compose_accessible_pandoc_document(
        _document(_header("Coverage evidence"), _code(source, "bash")),
        policy=AccessibleSlidePolicy(),
        source="manuscript/reproducibility.md",
    )

    assert not any(block.get("t") == "CodeBlock" for block in composition.document["blocks"])
    paragraph = next(block for block in composition.document["blocks"] if block.get("t") == "Para")
    assert _inline_text(paragraph["c"]) == source
    assert all(
        inline.get("c", [None, []])[0][1] == ["accessible-shell-token"]
        for inline in paragraph["c"]
        if inline.get("t") == "Code"
    )


def test_short_code_block_retains_pandoc_highlighting_environment() -> None:
    code = _code("result = aggregate(request)", "python")

    composition = compose_accessible_pandoc_document(
        _document(_header("Code"), code),
        policy=AccessibleSlidePolicy(),
        source="manuscript/methods.md",
    )

    assert code in composition.document["blocks"]


def test_overwide_whitespace_sensitive_code_fails_with_stable_diagnostic() -> None:
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-code-line\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(_header("Python"), _code("value = " + "x" * 60, "python")),
            policy=AccessibleSlidePolicy(),
            source="manuscript/methods.md",
        )

    assert exc_info.value.context == {
        "source": "manuscript/methods.md",
        "heading": "Python",
        "diagnostic_code": "slides.density.indivisible-code-line",
        "language": "python",
        "line_number": 1,
        "observed_characters": 68,
        "maximum_characters": 34,
    }


def test_atomic_shell_block_that_is_too_tall_fails_before_pandoc() -> None:
    source = "\n".join("uv run pytest tests/unit.py" for _ in range(8))

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-code\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(_header("Commands"), _code(source, "bash")),
            policy=AccessibleSlidePolicy(),
            source="manuscript/reproducibility.md",
        )

    assert exc_info.value.context["source_line_count"] == 8
    assert exc_info.value.context["estimated_lines"] == 8
    assert exc_info.value.context["maximum_lines"] == 7


def test_beamer_transform_remaps_projection_unsupported_glyphs_outside_code() -> None:
    """Beamer text faces get math-font fallbacks; protected code stays intact."""
    tex = "Frame text with β ≤ 0.05 while q → p.\\n\\\\begin{verbatim}\\nβ ≤ raw\\n\\\\end{verbatim}\\n"

    transformed = transform_beamer_latex(tex, RenderingConfig(), require_seqsplit=lambda: None)

    assert r"\texorpdfstring{\ensuremath{\beta}}{beta}" in transformed
    assert r"\texorpdfstring{\ensuremath{\leq}}{<=}" in transformed
    assert r"\texorpdfstring{\ensuremath{\to}}{->}" in transformed
    assert "β ≤ raw" in transformed
    assert "β ≤ 0.05" not in transformed


def test_beamer_transform_preserves_established_ge_remap() -> None:
    tex = "count ≥ 3"

    transformed = transform_beamer_latex(tex, RenderingConfig(), require_seqsplit=lambda: None)

    assert r"\texorpdfstring{\ensuremath{\ge}}{>=}" in transformed
    assert "≥" not in transformed


def test_beamer_transform_leaves_nested_and_plain_tables_untouched_by_glyph_rule() -> None:
    tex = "α level\\n\\\\begin{Highlighting}[]\\nα ≤ code\\n\\\\end{Highlighting}\\n"

    transformed = transform_beamer_latex(tex, RenderingConfig(), require_seqsplit=lambda: None)

    assert "α ≤ code" in transformed
    assert r"\texorpdfstring{\ensuremath{\alpha}}{alpha}" in transformed


def test_beamer_transform_leaves_graphics_filename_arguments_untouched() -> None:
    """A Unicode figure filename must survive the glyph remap verbatim."""
    tex = "\\includegraphics[width=50%]{β-panel.png} while β ≤ 1"

    transformed = transform_beamer_latex(tex, RenderingConfig(), require_seqsplit=lambda: None)

    assert "\\includegraphics[width=50%]{β-panel.png}" in transformed
    assert r"\texorpdfstring{\ensuremath{\beta}}{beta}.png" not in transformed
    assert r"\texorpdfstring{\ensuremath{\beta}}{beta} \texorpdfstring{\ensuremath{\leq}}{<=} 1" in transformed
