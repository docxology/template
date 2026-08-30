"""Accessible Beamer regressions for atomic code-frame geometry."""

from __future__ import annotations

from typing import Any

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    compose_accessible_pandoc_document,
)


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


def test_long_shell_commands_reflow_as_complete_breakable_inline_code() -> None:
    source = (
        "uv run --extra dev python scripts/validate_test_coverage.py\n"
        "    uv run  python scripts/z_generate_manuscript_variables.py"
    )

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
    source = "\n".join("uv run pytest tests/unit.py" for _ in range(9))

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-code\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(_header("Commands"), _code(source, "bash")),
            policy=AccessibleSlidePolicy(),
            source="manuscript/reproducibility.md",
        )

    assert exc_info.value.context["source_line_count"] == 9
    assert exc_info.value.context["estimated_lines"] == 9
    assert exc_info.value.context["maximum_lines"] == 8
