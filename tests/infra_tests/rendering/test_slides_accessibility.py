"""Contracts for the opt-in accessible presentation profile.

The archive profile remains the default.  These tests exercise the semantic
Pandoc-AST boundary directly and retain real Pandoc/Beamer smoke coverage for
the two accessible presentation derivatives.
"""

from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._bibliography import BibliographyConflictError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    _estimated_visible_characters,
    accessible_reveal_output_issues,
    compose_accessible_pandoc_document,
    enhance_accessible_reveal,
)
from infrastructure.rendering._slides_accessibility_tables import (
    _table_column_character_capacities,
    _table_column_minima,
)
from infrastructure.rendering._slides_accessibility_contracts import (
    proportional_text_width_units,
    tex_math_vertical_line_demand,
)
from infrastructure.rendering._slides_accessibility_text_geometry import _plain_text
from infrastructure.rendering._slides_reveal_content import (
    ACCESSIBLE_REVEAL_URL,
    activate_hardened_reveal_mathjax,
    promote_display_math_labels,
    resolve_reveal_cross_references,
    reveal_reference_and_math_issues,
)
from infrastructure.rendering._web_postprocess import (
    MATHJAX_URL,
    _MATHJAX_CONFIG_SCRIPT,
    _MATHJAX_INTEGRITY,
    harden_mathjax_script,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer, _reject_accessible_beamer_overflow


def _inlines(text: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, word in enumerate(text.split()):
        if index:
            result.append({"t": "Space"})
        result.append({"t": "Str", "c": word})
    return result


def _header(text: str, *, level: int = 2, classes: list[str] | None = None) -> dict[str, Any]:
    return {"t": "Header", "c": [level, [text.lower().replace(" ", "-"), classes or [], []], _inlines(text)]}


def _paragraph(text: str) -> dict[str, Any]:
    return {"t": "Para", "c": _inlines(text)}


def _hard_line_paragraph(line_count: int) -> dict[str, Any]:
    inlines: list[dict[str, Any]] = []
    for index in range(line_count):
        if index:
            inlines.append({"t": "LineBreak"})
        inlines.append({"t": "Str", "c": "x"})
    return {"t": "Para", "c": inlines}


def _nested_fraction_source(depth: int) -> str:
    source = "1"
    for _ in range(depth):
        source = rf"\frac{{1}}{{{source}}}"
    return source


def _citation(
    identifier: str,
    *,
    prefix: str = "",
    rendered_text: str | None = None,
    suffix: str = "",
) -> dict[str, Any]:
    return {
        "t": "Cite",
        "c": [
            [
                {
                    "citationId": identifier,
                    "citationPrefix": _inlines(prefix),
                    "citationSuffix": _inlines(suffix),
                    "citationMode": {"t": "NormalCitation"},
                    "citationNoteNum": 0,
                    "citationHash": 0,
                }
            ],
            _inlines(rendered_text) if rendered_text is not None else [{"t": "Str", "c": f"[@{identifier}]"}],
        ],
    }


def _paragraph_with_citations(text: str, identifiers: list[str]) -> dict[str, Any]:
    inlines = _inlines(text)
    citations = {f"REF{index}": _citation(identifier) for index, identifier in enumerate(identifiers)}
    return {
        "t": "Para",
        "c": [citations.get(str(inline.get("c")), inline) for inline in inlines],
    }


def _document(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    return {"pandoc-api-version": [1, 23, 1, 2], "meta": {}, "blocks": blocks}


def _visible_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(part for item in value if (part := _visible_text(item)))
    if not isinstance(value, dict):
        return ""
    if value.get("t") in {"Space", "SoftBreak", "LineBreak"}:
        return " "
    return _visible_text(value["c"] if "c" in value else list(value.values()))


def _cell(value: str) -> list[Any]:
    return [["", [], []], {"t": "AlignDefault"}, 1, 1, [{"t": "Plain", "c": _inlines(value)}]]


def _row(value: str) -> list[Any]:
    return [["", [], []], [_cell(value), _cell("value")]]


def _row_values(values: list[str]) -> list[Any]:
    return [["", [], []], [_cell(value) for value in values]]


def _table(rows: int) -> dict[str, Any]:
    return {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in range(2)],
            [["", [], []], [_row("key")]],
            [[["", [], []], 0, [], [_row(str(index)) for index in range(rows)]]],
            [["", [], []], []],
        ],
    }


def _table_values(headers: list[str], rows: list[list[str]]) -> dict[str, Any]:
    assert all(len(row) == len(headers) for row in rows)
    return {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in headers],
            [["", [], []], [_row_values(headers)]],
            [[["", [], []], 0, [], [_row_values(row) for row in rows]]],
            [["", [], []], []],
        ],
    }


def _classed_headers(document: dict[str, Any]) -> list[tuple[str, set[str]]]:
    result: list[tuple[str, set[str]]] = []
    for block in document["blocks"]:
        if block["t"] != "Header":
            continue
        text = " ".join(item.get("c", "") for item in block["c"][2] if item["t"] == "Str")
        result.append((text, set(block["c"][1][1])))
    return result


def _write_png(path: Path) -> None:
    # Valid one-pixel RGB PNG; avoids a Pillow dependency in the renderer test.
    path.write_bytes(
        base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
    )


def _image(path: str, *, width: str | None = None, alt: str = "Panel") -> dict[str, Any]:
    attributes: list[list[str]] = [] if width is None else [["width", width]]
    return {
        "t": "Image",
        "c": [["", [], attributes], _inlines(alt), [path, ""]],
    }


def _linked_image(
    thumbnail: str,
    full_size: str,
    *,
    width: str | None = None,
    sibling_text: str | None = None,
) -> dict[str, Any]:
    inlines: list[dict[str, Any]] = [_image(thumbnail, width=width)]
    if sibling_text is not None:
        inlines.extend([{"t": "Space"}, *_inlines(sibling_text)])
    return {
        "t": "Link",
        "c": [["", ["figure-full-size-link"], []], inlines, [full_size, "Open full-size figure"]],
    }


def _spanning_cell(value: str, *, row_span: int = 1, column_span: int = 1) -> list[Any]:
    return [
        ["", [], []],
        {"t": "AlignDefault"},
        row_span,
        column_span,
        [{"t": "Plain", "c": _inlines(value)}],
    ]


def _block_cell(
    blocks: list[dict[str, Any]],
    *,
    row_span: int = 1,
    column_span: int = 1,
) -> list[Any]:
    return [
        ["", [], []],
        {"t": "AlignDefault"},
        row_span,
        column_span,
        blocks,
    ]


def test_archive_profile_remains_the_default_and_accessible_defaults_are_exact() -> None:
    config = RenderingConfig()

    assert config.slides_profile == "archive"
    assert config.accessible_slide_policy() == AccessibleSlidePolicy(
        max_prose_words=80,
        max_table_rows=8,
        min_figure_area_percent=70,
        title_font_pt=28,
        body_font_pt=20,
        figure_label_font_pt=16,
        reader_href="../web/index.html",
    )


def test_accessible_profile_loads_strict_yaml_and_environment_overrides() -> None:
    project = {
        "render": {
            "slides": {
                "profile": "accessible",
                "max_prose_words": 80,
                "max_table_rows": 8,
                "min_figure_area_percent": 70,
                "title_font_pt": 28,
                "body_font_pt": 20,
                "figure_label_font_pt": 16,
                "reader_href": "reader/index.html",
            }
        }
    }

    config = RenderingConfig.from_project_config(
        project,
        env={"SLIDES_MAX_PROSE_WORDS": "72", "SLIDES_READER_HREF": "https://example.org/manuscript"},
    )

    assert config.slides_profile == "accessible"
    assert config.slides_max_prose_words == 72
    assert config.slides_reader_href == "https://example.org/manuscript"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"render": {"slides": {"body_font_pt": 19}}}, "slides_body_font_pt"),
        ({"render": {"slides": {"max_prose_words": 81}}}, "slides_max_prose_words"),
        ({"render": {"slides": {"max_table_rows": 9}}}, "slides_max_table_rows"),
        ({"render": {"slides": {"max_table_rows": True}}}, "must be an integer"),
        ({"render": {"slides": {"unexpected": 1}}}, "unknown fields"),
        ({"render": {"slides": []}}, "must be a mapping"),
    ],
)
def test_accessible_profile_rejects_weakened_or_unknown_configuration(
    payload: dict[str, Any],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        RenderingConfig.from_project_config(payload, env={})


@pytest.mark.parametrize(
    "reader_href",
    ["javascript:alert(1)", "/machine/local/index.html", r"..\web\index.html", ""],
)
def test_accessible_profile_rejects_unsafe_reader_links(reader_href: str) -> None:
    with pytest.raises(ValueError, match="slides_reader_href"):
        RenderingConfig(slides_reader_href=reader_href)


def test_semantic_composer_splits_only_between_prose_blocks() -> None:
    first = _paragraph(" ".join(f"alpha{index}" for index in range(35)))
    second = _paragraph(" ".join(f"beta{index}" for index in range(35)))

    composition = compose_accessible_pandoc_document(
        _document([_header("Bounded evidence"), first, second]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    headers = _classed_headers(composition.document)
    assert composition.frame_count == 2
    assert [classes for _title, classes in headers] == [{"prose-slide"}, {"prose-slide"}]
    assert "part 2" in headers[1][0]
    assert composition.document["blocks"][1] == first
    assert composition.document["blocks"][3] == second


def test_semantic_composer_splits_long_paragraph_only_at_written_clause_boundary() -> None:
    first_sentence = " ".join(f"alpha{index}" for index in range(35)) + "."
    second_sentence = " ".join(f"beta{index}" for index in range(35)) + "."

    composition = compose_accessible_pandoc_document(
        _document([_header("Projection geometry"), _paragraph(first_sentence + " " + second_sentence)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    prose = [block for block in composition.document["blocks"] if block["t"] == "Para"]
    assert composition.frame_count == 2
    assert len(prose) == 2
    assert " ".join(_visible_text(prose[0]).split()).endswith("alpha34.")
    assert " ".join(_visible_text(prose[1]).split()).endswith("beta34.")


def test_semantic_composer_uses_comma_only_before_clause_coordinator() -> None:
    prefix = " ".join(f"alpha{index}" for index in range(32)) + ","
    suffix = "while " + " ".join(f"beta{index}" for index in range(28)) + "."

    composition = compose_accessible_pandoc_document(
        _document([_header("Projection geometry"), _paragraph(prefix + " " + suffix)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    prose = [block for block in composition.document["blocks"] if block["t"] == "Para"]
    assert composition.frame_count == 2
    assert " ".join(_visible_text(prose[0]).split()).endswith("alpha31,")
    assert " ".join(_visible_text(prose[1]).split()).startswith("while beta0")


def test_semantic_composer_rejects_geometry_overflow_without_written_boundary() -> None:
    dense = _paragraph(" ".join(f"longword{index}" for index in range(45)))

    with pytest.raises(RenderingError, match=r"one prose sentence or strong clause cannot fit") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Projection geometry"), dense]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["maximum_lines"] == 8


def test_semantic_composer_counts_authored_hard_lines_at_the_physical_boundary() -> None:
    composition = compose_accessible_pandoc_document(
        _document([_header("Hard lines"), _hard_line_paragraph(8)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/hard-lines.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Hard lines"), _hard_line_paragraph(9)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/hard-lines.md",
        )

    assert exc_info.value.context["estimated_lines"] == 9
    assert exc_info.value.context["maximum_lines"] == 8


def test_semantic_composer_fails_closed_on_pandoc_notes() -> None:
    note = {"t": "Note", "c": [_paragraph("A projected footnote would violate the declared floor.")]}
    paragraph = {"t": "Para", "c": [*_inlines("Bounded statement"), note]}

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-note\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Note boundary"), paragraph]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/notes.md",
        )

    assert exc_info.value.context["block_type"] == "Para"


def test_semantic_composer_fails_closed_on_pandoc_notes_in_headings() -> None:
    note = {"t": "Note", "c": [_paragraph("A projected title footnote would violate the floor.")]}
    header = _header("Note boundary")
    header["c"][2].append(note)

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-note\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([header, _paragraph("Bounded statement.")]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/notes.md",
        )

    assert exc_info.value.context["block_type"] == "Header"


def test_semantic_composer_fails_closed_on_unmodeled_heading_math() -> None:
    math_source = r"\rule{50cm}{1pt}"
    header = _header("Math boundary")
    header["c"][2].append({"t": "Math", "c": [{"t": "InlineMath"}, math_source]})

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-math-geometry\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([header, _paragraph("Bounded statement.")]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/math-heading.md",
        )

    assert exc_info.value.context["unsupported_commands"] == ["rule"]


def test_semantic_composer_fails_closed_on_unmodeled_raw_heading_inline() -> None:
    header = _header("Raw boundary")
    header["c"][2].append({"t": "RawInline", "c": ["tex", r"\kern50cm"]})

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-raw-geometry\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([header, _paragraph("Bounded statement.")]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/raw-heading.md",
        )

    assert exc_info.value.context["unsupported_command"] == "kern"


@pytest.mark.parametrize("surface", ["heading", "prose", "table"])
def test_semantic_composer_fails_closed_on_unmodeled_raw_inline_across_surfaces(surface: str) -> None:
    raw_inline = {"t": "RawInline", "c": ["tex", r"\hspace*{50cm} X"]}
    header = _header("Raw inline boundary")
    body: dict[str, Any] = _paragraph("Bounded statement.")
    if surface == "heading":
        header["c"][2].append(raw_inline)
    elif surface == "prose":
        body = {"t": "Para", "c": [raw_inline]}
    else:
        body = _table_values(["Expression"], [["placeholder"]])
        body["c"][4][0][3][0][1][0][4][0]["c"] = [raw_inline]

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-raw-geometry\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([header, body]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/raw-inline.md",
        )

    assert exc_info.value.context["unsupported_command"] == "hspace"


@pytest.mark.parametrize("container", ["prose", "table"])
def test_semantic_composer_fails_closed_on_unmodeled_math_commands(container: str) -> None:
    math_source = r"\rule{50cm}{1pt}"
    math_inline = {"t": "Math", "c": [{"t": "InlineMath"}, math_source]}
    if container == "prose":
        block = {"t": "Para", "c": [math_inline]}
    else:
        block = _table_values(["Expression"], [["placeholder"]])
        block["c"][4][0][3][0][1][0][4][0]["c"] = [math_inline]

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-math-geometry\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Math contract"), block]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/math.md",
        )

    assert exc_info.value.context["math_source"] == math_source
    assert exc_info.value.context["unsupported_commands"] == ["rule"]


def test_semantic_composer_rejects_overwide_display_math_token() -> None:
    math_source = "W" * 40
    equation = {"t": "Para", "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, math_source]}]}

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-equation-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Equation width"), equation]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/equation.md",
        )

    assert exc_info.value.context["first_offending_token"] == math_source
    assert exc_info.value.context["required_width_units"] > exc_info.value.context["available_width_units"]


def test_semantic_composer_rejects_overwide_evidence_token() -> None:
    token = "W" * 23
    evidence = {"t": "BlockQuote", "c": [_paragraph(token)]}

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-evidence-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Evidence width"), evidence]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/evidence.md",
        )

    assert exc_info.value.context["first_offending_token"] == token


def test_semantic_composer_treats_nonbreaking_spaces_as_physical_token_joins() -> None:
    token = "\N{LATIN CAPITAL LETTER W}\N{LATIN CAPITAL LETTER W}\N{NO-BREAK SPACE}" * 14 + "WW"
    paragraph = {"t": "Para", "c": [{"t": "Str", "c": token}]}

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Nonbreaking width"), paragraph]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/nonbreaking.md",
        )

    assert exc_info.value.context["first_offending_token"] == token


@pytest.mark.parametrize(
    ("raw_source", "unsupported_command"),
    [
        (r"\rule{50cm}{1pt}", "rule"),
        (r"\kern50cm X", "kern"),
        (r"\hbox to 50cm{X}", "hbox"),
        (r"\begin{center}X\end{center}", "raw-block-shape"),
    ],
)
def test_semantic_composer_rejects_unmodeled_raw_tex_physical_geometry(
    raw_source: str,
    unsupported_command: str,
) -> None:
    raw = {"t": "RawBlock", "c": ["tex", raw_source]}

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-raw-geometry\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Raw geometry"), raw]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/raw.md",
        )

    assert exc_info.value.context["unsupported_command"] == unsupported_command


def test_semantic_composer_accepts_allowlisted_theorem_raw_tex() -> None:
    raw = {
        "t": "RawBlock",
        "c": [
            "tex",
            r"\begin{theorem}[Bounded claim]\label{thm:bounded} "
            r"For $\lambda>0$, \texttt{method} follows (\ref{eq:method}). "
            r"\end{theorem}",
        ],
    }

    composition = compose_accessible_pandoc_document(
        _document([_header("Formal result"), raw]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/formalism.md",
    )

    assert composition.frame_count == 1


def test_semantic_composer_accepts_allowlisted_raw_reference_inline() -> None:
    paragraph = {
        "t": "Para",
        "c": [*_inlines("See theorem"), {"t": "RawInline", "c": ["tex", r"\ref{thm:bounded}"]}],
    }

    composition = compose_accessible_pandoc_document(
        _document([_header("Formal reference"), paragraph]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/formalism.md",
    )

    assert composition.frame_count == 1


@pytest.mark.parametrize(
    "raw_source",
    [
        r"\begin{theorem}x\end{theorem}",
        r"\begin{aligned}a&=b\end{aligned}",
    ],
)
def test_semantic_composer_rejects_block_only_raw_tex_as_inline(raw_source: str) -> None:
    paragraph = {"t": "Para", "c": [{"t": "RawInline", "c": ["latex", raw_source]}]}

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-raw-geometry\]"):
        compose_accessible_pandoc_document(
            _document([_header("Raw inline"), paragraph]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/raw-inline.md",
        )


@pytest.mark.parametrize("environment", ["center", "aligned"])
def test_semantic_composer_rejects_nested_raw_tex_environments(environment: str) -> None:
    raw = {
        "t": "RawBlock",
        "c": [
            "tex",
            rf"\begin{{theorem}}Claim \begin{{{environment}}}x\end{{{environment}}}\end{{theorem}}",
        ],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-raw-geometry\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Nested raw environment"), raw]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/raw-block.md",
        )

    assert exc_info.value.context["unsupported_command"] == "nested-environment"


def test_semantic_composer_accepts_the_declared_aligned_math_environment() -> None:
    math_source = (
        r"\begin{aligned}"
        r"q(s)&=\operatorname{normalize}(p(s))\\"
        r"\log q(s)&=\log p(s)-\log Z"
        r"\end{aligned}"
    )
    equation = {"t": "Para", "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, math_source]}]}

    composition = compose_accessible_pandoc_document(
        _document([_header("Aligned math"), equation]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/aligned.md",
    )

    assert composition.frame_count == 1


def test_semantic_composer_rejects_optional_aligned_row_spacing() -> None:
    math_source = r"\begin{aligned}x&=1\\[10cm]y&=2\end{aligned}"
    equation = {"t": "Para", "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, math_source]}]}

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-math-geometry\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Aligned spacing"), equation]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/aligned-spacing.md",
        )

    assert exc_info.value.context["unsupported_commands"] == ["row-spacing"]


def test_semantic_composer_treats_aligned_row_break_as_control_symbol() -> None:
    math_source = r"\begin{aligned}x_0&=0\\x_1&=1\end{aligned}"
    equation = {"t": "Para", "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, math_source]}]}

    composition = compose_accessible_pandoc_document(
        _document([_header("Row separator"), equation]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/aligned.md",
    )

    assert composition.frame_count == 1


@pytest.mark.parametrize(
    ("kind", "passing_rows", "failing_rows", "passing_lines", "failing_lines"),
    [("aligned", 6, 7, 8, 9), ("substack", 14, 15, 8, 9)],
)
def test_semantic_composer_prices_supported_multiline_math_geometry(
    kind: str,
    passing_rows: int,
    failing_rows: int,
    passing_lines: int,
    failing_lines: int,
) -> None:
    def math_source(rows: int) -> str:
        body = r"\\ ".join("a" for _ in range(rows))
        if kind == "aligned":
            return r"\begin{aligned}" + body + r"\end{aligned}"
        return rf"x_{{\substack{{{body}}}}}=1"

    passing_source = math_source(passing_rows)
    passing_equation = {
        "t": "Para",
        "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, passing_source]}],
    }
    composition = compose_accessible_pandoc_document(
        _document([_header("Multiline pass"), passing_equation]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/math.md",
    )

    assert composition.frame_count == 1
    assert tex_math_vertical_line_demand(passing_source) == passing_lines

    failing_source = math_source(failing_rows)
    failing_equation = {
        "t": "Para",
        "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, failing_source]}],
    }
    with pytest.raises(RenderingError, match=r"\[slides\.density\.math-height\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Multiline fail"), failing_equation]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/math.md",
        )

    assert exc_info.value.context["math_source"] == failing_source
    assert exc_info.value.context["estimated_lines"] == failing_lines
    assert exc_info.value.context["maximum_lines"] == 8


def test_semantic_composer_models_display_and_table_math_height() -> None:
    passing_math = {"t": "Math", "c": [{"t": "DisplayMath"}, _nested_fraction_source(16)]}
    passing_equation = {"t": "Para", "c": [passing_math]}
    composition = compose_accessible_pandoc_document(
        _document([_header("Fraction depth"), passing_equation]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/math.md",
    )
    assert composition.frame_count == 1

    failing_source = _nested_fraction_source(17)
    failing_equation = {"t": "Para", "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, failing_source]}]}
    with pytest.raises(RenderingError, match=r"\[slides\.density\.math-height\]") as equation_error:
        compose_accessible_pandoc_document(
            _document([_header("Fraction depth"), failing_equation]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/math.md",
        )
    assert equation_error.value.context["estimated_lines"] == 9

    table = _table_values(["Expression"], [["placeholder"]])
    table["c"][4][0][3][0][1][0][4][0]["c"] = [{"t": "Math", "c": [{"t": "InlineMath"}, failing_source]}]
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table\]") as table_error:
        compose_accessible_pandoc_document(
            _document([_header("Fraction table"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/math.md",
        )
    assert table_error.value.context["first_row_lines"] == 9


def test_semantic_composer_prices_list_indent_and_nested_item_lines() -> None:
    passing_width = {"t": "BulletList", "c": [[_paragraph("a" * 40)]]}
    composition = compose_accessible_pandoc_document(
        _document([_header("List width"), passing_width]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/lists.md",
    )
    assert composition.frame_count == 1

    failing_width = {"t": "BulletList", "c": [[_paragraph("a" * 42)]]}
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose-token\]") as width_error:
        compose_accessible_pandoc_document(
            _document([_header("List width"), failing_width]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/lists.md",
        )
    assert width_error.value.context["first_offending_token"] == "a" * 42

    def nested(child_count: int) -> dict[str, Any]:
        children = {"t": "BulletList", "c": [[_paragraph(f"child {index}")] for index in range(child_count)]}
        return {"t": "BulletList", "c": [[_paragraph("parent"), children]]}

    nested_composition = compose_accessible_pandoc_document(
        _document([_header("Nested list"), nested(7)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/lists.md",
    )
    assert nested_composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-list\]") as height_error:
        compose_accessible_pandoc_document(
            _document([_header("Nested list"), nested(8)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/lists.md",
        )
    assert height_error.value.context["estimated_lines"] == 9


def test_semantic_composer_models_definition_list_entry_geometry() -> None:
    def definition_list(entry_count: int) -> dict[str, Any]:
        return {
            "t": "DefinitionList",
            "c": [[_inlines(f"term{index}"), [[_paragraph("x")]]] for index in range(entry_count)],
        }

    composition = compose_accessible_pandoc_document(
        _document([_header("Definitions"), definition_list(7)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/definitions.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-definition-list\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Definitions"), definition_list(8)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/definitions.md",
        )
    assert exc_info.value.context["estimated_lines"] == 9


def test_semantic_composer_recursively_prices_one_definition_with_many_paragraphs() -> None:
    def definition_list(paragraph_count: int) -> dict[str, Any]:
        return {
            "t": "DefinitionList",
            "c": [[_inlines("term"), [[_paragraph("x") for _ in range(paragraph_count)]]]],
        }

    composition = compose_accessible_pandoc_document(
        _document([_header("One definition"), definition_list(8)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/definitions.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-definition-list\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("One definition"), definition_list(10)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/definitions.md",
        )
    assert exc_info.value.context["estimated_lines"] == 10


def test_semantic_composer_debits_loose_list_paragraph_spacing() -> None:
    def loose_list(paragraph_count: int) -> dict[str, Any]:
        return {"t": "BulletList", "c": [[_paragraph("x") for _ in range(paragraph_count)]]}

    composition = compose_accessible_pandoc_document(
        _document([_header("Loose list"), loose_list(7)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/lists.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-list\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Loose list"), loose_list(8)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/lists.md",
        )
    assert exc_info.value.context["estimated_lines"] == 9


def test_semantic_composer_recursively_prices_evidence_block_paragraphs() -> None:
    def evidence(paragraph_count: int) -> dict[str, Any]:
        return {"t": "BlockQuote", "c": [_paragraph("x") for _ in range(paragraph_count)]}

    composition = compose_accessible_pandoc_document(
        _document([_header("Evidence"), evidence(9)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/evidence.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-evidence\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Evidence"), evidence(10)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/evidence.md",
        )
    assert exc_info.value.context["estimated_lines"] == 9


def test_semantic_composer_preserves_evidence_div_block_geometry() -> None:
    evidence = {
        "t": "Div",
        "c": [["", ["evidence"], []], [_paragraph("x") for _ in range(10)]],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-evidence\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Evidence container"), evidence]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/evidence-div.md",
        )

    assert exc_info.value.context["estimated_lines"] == 19
    assert exc_info.value.context["maximum_lines"] == 8


def test_semantic_composer_fails_on_an_indivisible_dense_block() -> None:
    dense = _paragraph(" ".join(f"word{index}" for index in range(81)))

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Too dense"), dense]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["diagnostic_code"] == "slides.density.indivisible-prose"
    assert exc_info.value.context["maximum_words"] == 80


@pytest.mark.parametrize(
    ("block", "code"),
    [
        (
            {"t": "BulletList", "c": [[_paragraph(" ".join(f"item{index}" for index in range(50)))]]},
            "slides.density.indivisible-list",
        ),
        (
            {
                "t": "RawBlock",
                "c": [
                    "tex",
                    "\\begin{definition}" + " ".join(f"condition{index}" for index in range(90)) + "\\end{definition}",
                ],
            },
            "slides.density.indivisible-raw-block",
        ),
    ],
)
def test_semantic_composer_rejects_oversized_atomic_structures(
    block: dict[str, Any],
    code: str,
) -> None:
    with pytest.raises(RenderingError, match=rf"\[{re.escape(code)}\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Atomic source structure"), block]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["diagnostic_code"] == code
    assert exc_info.value.context["estimated_lines"] > exc_info.value.context["maximum_lines"]


def test_semantic_composer_debits_inline_code_at_the_monospace_width() -> None:
    inlines: list[dict[str, Any]] = []
    for index in range(12):
        if index:
            inlines.append({"t": "Space"})
        inlines.append({"t": "Code", "c": [["", [], []], f"canonical_parameter_name_{index}"]})
    block = {"t": "Para", "c": inlines}

    with pytest.raises(RenderingError, match=r"slides\.density\.indivisible-prose"):
        compose_accessible_pandoc_document(
            _document([_header("Monospace geometry"), block]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_semantic_composer_debits_cross_reference_fallback_at_visible_label_width() -> None:
    bibliography = {"t": "Para", "c": [_citation("mildner2025fedgvi")]}
    section_reference = {"t": "Para", "c": [_citation("sec:results-hierarchical")]}

    assert _estimated_visible_characters(bibliography) == 32
    assert _estimated_visible_characters(section_reference) > _estimated_visible_characters(bibliography)


def test_semantic_composer_prices_citation_prefix_and_suffix_before_citeproc() -> None:
    citation = {
        "t": "Para",
        "c": [
            _citation(
                "bissiri2016",
                prefix="compare the detailed construction in",
                suffix="especially chapter twelve and appendix alpha",
            )
        ],
    }

    assert _estimated_visible_characters(citation) == proportional_text_width_units(
        "compare the detailed construction in " + "a" * 32 + " especially chapter twelve and appendix alpha"
    )


def test_semantic_composer_uses_resolved_citeproc_text_and_rejects_one_overwide_family_name() -> None:
    long_family = "W" * 24
    citation = _citation(
        "longfamily2026",
        rendered_text=f"({long_family} 2026)",
    )
    paragraph = {"t": "Para", "c": [*_inlines("The source is"), {"t": "Space"}, citation]}

    assert _estimated_visible_characters(paragraph) == proportional_text_width_units(
        f"The source is ({long_family} 2026)"
    )
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Resolved citation geometry"), paragraph]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/discussion.md",
        )

    assert long_family in exc_info.value.context["first_offending_token"]
    assert exc_info.value.context["required_width_units"] > exc_info.value.context["available_width_units"]


def test_resolved_mixed_citation_prices_one_cross_reference_rendition() -> None:
    cite = {
        "t": "Cite",
        "c": [
            [
                {
                    "citationId": "smith2026",
                    "citationPrefix": [{"t": "Str", "c": "see"}],
                    "citationSuffix": [],
                    "citationMode": {"t": "NormalCitation"},
                    "citationNoteNum": 1,
                    "citationHash": 0,
                },
                {
                    "citationId": "eq:model",
                    "citationPrefix": [],
                    "citationSuffix": [],
                    "citationMode": {"t": "NormalCitation"},
                    "citationNoteNum": 1,
                    "citationHash": 0,
                },
            ],
            [
                {"t": "Str", "c": "(see"},
                {"t": "Space"},
                {"t": "Str", "c": "Smith"},
                {"t": "Space"},
                {"t": "Str", "c": "2026;"},
                {"t": "Space"},
                {"t": "Strong", "c": [{"t": "Str", "c": "eq:model?"}]},
                {"t": "Str", "c": ")"},
            ],
        ],
    }

    normalized = " ".join(_plain_text(cite).split())

    assert normalized == "(see Smith 2026; eq. eq:model )"
    assert normalized.count("eq:model") == 1
    assert _estimated_visible_characters({"t": "Para", "c": [cite]}) < proportional_text_width_units(
        normalized + " eq. eq:model"
    )


@pytest.mark.parametrize(("glyph", "count"), [("W", 23), ("A", 32), ("m", 28)])
def test_semantic_composer_rejects_overwide_ordinary_prose_tokens(glyph: str, count: int) -> None:
    token = glyph * count

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Physical token"), _paragraph(token)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/discussion.md",
        )

    assert exc_info.value.context["first_offending_token"] == token
    assert exc_info.value.context["required_width_units"] > 43


def test_semantic_composer_prices_aggregate_proportional_prose_width() -> None:
    passing = _paragraph(" ".join(["WW"] * 72))
    failing = _paragraph(" ".join(["WW"] * 80))

    composition = compose_accessible_pandoc_document(
        _document([_header("Wide prose pass"), passing]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/discussion.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Wide prose fail"), failing]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/discussion.md",
        )

    assert exc_info.value.context["estimated_lines"] == 9
    assert exc_info.value.context["maximum_lines"] == 8


@pytest.mark.parametrize("literal", ["'", "[", "{"])
def test_semantic_composer_rejects_long_code_outside_exact_breaktt_contract(literal: str) -> None:
    code = "a" * 80 + literal
    paragraph = {"t": "Para", "c": [{"t": "Code", "c": [["", [], []], code]}]}

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Code token"), paragraph]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/discussion.md",
        )

    assert exc_info.value.context["first_offending_token"] == code
    assert exc_info.value.context["required_width_units"] > 43


def test_semantic_composer_splits_before_unresolved_crossrefs_overflow_beamer() -> None:
    paragraph = _paragraph_with_citations(
        "Five structural extension studies (Studies 5–9, Supplementary sections) build on the same POMDP "
        "substrate and are described there: the moving disjoint-FOV sentinel ( REF0 ), the 2-level hierarchical "
        "POMDP ( REF1 ), the N-level extension ( REF2 ), the 2-D sensitivity sweep ( REF3 ), and parameter "
        "recovery ( REF4 ).",
        [
            "sec:results-moving",
            "sec:results-hierarchical",
            "sec:results-3level",
            "sec:results-sensitivity",
            "sec:results-parameter-recovery",
        ],
    )

    composition = compose_accessible_pandoc_document(
        _document([_header("Server robustness setting"), paragraph]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/12_methods_experimental_design.md",
    )

    prose = [block for block in composition.document["blocks"] if block["t"] == "Para"]
    assert composition.frame_count == 2
    assert len(prose) == 2
    assert "sec:results-3level" in json.dumps(prose[0])
    assert "sec:results-sensitivity" not in json.dumps(prose[0])
    assert "sec:results-sensitivity" in json.dumps(prose[1])
    assert "sec:results-parameter-recovery" in json.dumps(prose[1])


def test_semantic_composer_prices_citeproc_author_year_expansion_before_split() -> None:
    paragraph = _paragraph_with_citations(
        "The first bounded synthesis relates REF0 REF1 REF2 and REF3 while preserving each source claim. "
        "The second bounded synthesis relates REF4 REF5 REF6 and REF7 while preserving each evidence class.",
        [f"long-surname-source-{index}" for index in range(8)],
    )

    composition = compose_accessible_pandoc_document(
        _document([_header("Citation-rich synthesis"), paragraph]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/discussion.md",
    )

    prose = [block for block in composition.document["blocks"] if block["t"] == "Para"]
    assert composition.frame_count == 2
    assert len(prose) == 2
    assert "long-surname-source-3" in json.dumps(prose[0])
    assert "long-surname-source-4" not in json.dumps(prose[0])
    assert "long-surname-source-4" in json.dumps(prose[1])


def test_semantic_composer_excerpts_table_without_mutating_source() -> None:
    table = _table(10)
    source = _document([_header("Exact values"), table])

    composition = compose_accessible_pandoc_document(
        source,
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered_table = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    assert composition.excerpted_table_count == 1
    # The configured eight-row value remains an absolute ceiling. Projection
    # geometry retains six compact rows after the header and table rules are
    # accounted for at 20 points. The persistent frame navigation owns the
    # canonical-reader link, so no duplicate table caption consumes a row.
    assert len(rendered_table["c"][4][0][3]) == 6
    assert len(rendered_table["c"][4][0][3]) <= AccessibleSlidePolicy().max_table_rows
    assert rendered_table["c"][1] == [None, []]
    assert len(table["c"][4][0][3]) == 10
    assert all(colspec[1]["t"] == "ColWidth" for colspec in rendered_table["c"][2])
    assert all(colspec[1]["t"] == "ColWidthDefault" for colspec in table["c"][2])


def test_semantic_composer_removes_complete_table_footer_from_projection_excerpt() -> None:
    table = _table(10)
    table["c"][5][1] = [_row("Total 10")]

    composition = compose_accessible_pandoc_document(
        _document([_header("Excerpted total"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered_table = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    assert composition.excerpted_table_count == 1
    assert len(rendered_table["c"][4][0][3]) < 10
    assert rendered_table["c"][5][1] == []
    source_footer = " ".join(_visible_text(table["c"][5]).split())
    assert "Total" in source_footer and "10" in source_footer


def test_table_excerpt_recomputes_geometry_after_dropping_a_long_footer() -> None:
    table = _table(10)
    footer = _row("complete-source total")
    footer[1][0][4] = [_hard_line_paragraph(7)]
    table["c"][5][1] = [footer]

    composition = compose_accessible_pandoc_document(
        _document([_header("Excerpted long footer"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered_table = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    assert composition.excerpted_table_count == 1
    assert len(rendered_table["c"][4][0][3]) == 6
    assert rendered_table["c"][5][1] == []
    assert len(table["c"][5][1]) == 1


def test_uniform_pandoc_table_widths_are_redistributed_by_visible_demand() -> None:
    table = _table_values(
        ["ID", "Interpretation"],
        [["A", "A substantially longer source-owned explanation"], ["B", "A second explanation"]],
    )
    table["c"][2] = [
        [{"t": "AlignDefault"}, {"t": "ColWidth", "c": 0.5}],
        [{"t": "AlignDefault"}, {"t": "ColWidth", "c": 0.5}],
    ]

    composition = compose_accessible_pandoc_document(
        _document([_header("Exact values"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    widths = [float(colspec[1]["c"]) for colspec in rendered["c"][2]]
    assert widths[1] > widths[0]
    assert sum(widths) == pytest.approx(1.0)


def test_genuinely_unequal_authored_table_widths_are_preserved() -> None:
    table = _table_values(["ID", "Interpretation"], [["A", "Explanation"]])
    table["c"][2] = [
        [{"t": "AlignDefault"}, {"t": "ColWidth", "c": 0.25}],
        [{"t": "AlignDefault"}, {"t": "ColWidth", "c": 0.75}],
    ]

    composition = compose_accessible_pandoc_document(
        _document([_header("Exact values"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    widths = [float(colspec[1]["c"]) for colspec in rendered["c"][2]]
    assert widths == pytest.approx([0.25, 0.75])


def test_table_widths_honor_prose_hyphen_and_breakable_code_minima() -> None:
    long_code = "canonical_parameter_identifier_that_becomes_breakable"
    table = _table_values(
        ["Symbol", "Meaning", "Code term"],
        [["y_t", "Observation/outcome rank-biserial-derived index", long_code]],
    )
    code_inline = {"t": "Code", "c": [["", [], []], long_code]}
    table["c"][4][0][3][0][1][2][4][0]["c"] = [code_inline]

    composition = compose_accessible_pandoc_document(
        _document([_header("Notation mapping"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/notation.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    widths = [float(colspec[1]["c"]) for colspec in rendered["c"][2]]
    minima, tokens = _table_column_minima(rendered["c"], 3)
    capacities = _table_column_character_capacities(widths, AccessibleSlidePolicy(), minima)
    assert len(rendered["c"][2]) == 3
    assert all(capacity >= minimum for capacity, minimum in zip(capacities, minima, strict=True))
    assert minima[1] == 19
    assert minima[1] > len("biserial-") + 1
    assert minima[2] < len(long_code)
    assert tokens[1] == "Observation/outcome"
    assert tokens[2] == "Code"


def test_overlapping_colspans_share_their_common_column_minimum() -> None:
    wide_token = "W" * 18
    table = {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in range(3)],
            [
                ["", [], []],
                [
                    [
                        ["", [], []],
                        [
                            _spanning_cell(wide_token, column_span=2),
                            _spanning_cell("x"),
                        ],
                    ]
                ],
            ],
            [
                [
                    ["", [], []],
                    0,
                    [],
                    [
                        [
                            ["", [], []],
                            [
                                _spanning_cell("x"),
                                _spanning_cell(wide_token, column_span=2),
                            ],
                        ]
                    ],
                ]
            ],
            [["", [], []], []],
        ],
    }

    minima, _tokens = _table_column_minima(table["c"], 3)

    # Each W span requires 36 calibrated width units. The one-unit internal
    # gutter means the column minima must contribute at least 35. A local
    # greedy split would over-allocate; the exact interval solver shares the
    # middle column and finds the feasible 37-unit allocation [2, 33, 2].
    assert minima == [2, 33, 2]
    assert sum(minima[:2]) + 1 >= 36
    assert sum(minima[1:]) + 1 >= 36
    assert sum(minima) <= 41


@pytest.mark.parametrize("token_length", [41, 42])
def test_infeasible_colspan_diagnostic_preserves_active_span_provenance(token_length: int) -> None:
    token = "a" * token_length
    table = {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in range(3)],
            [
                ["", [], []],
                [
                    [
                        ["", [], []],
                        [_spanning_cell("A"), _spanning_cell("B"), _spanning_cell("C")],
                    ]
                ],
            ],
            [
                [
                    ["", [], []],
                    0,
                    [],
                    [
                        [
                            ["", [], []],
                            [_spanning_cell(token, column_span=2), _spanning_cell("x")],
                        ]
                    ],
                ]
            ],
            [["", [], []], []],
        ],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Spanning boundary"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/spanning.md",
        )

    context = exc_info.value.context
    assert context["column_minimum_width_units"] == [2, token_length - 3, 2]
    assert context["first_offending_token"] == token
    assert context["first_offending_column_index"] == 1
    assert context["offending_span_start_column_index"] == 1
    assert context["offending_span_end_column_index"] == 2
    assert context["offending_span_required_width_units"] == token_length - 1


def test_individually_impossible_column_outranks_unrelated_span_diagnostic() -> None:
    def span_row(cells: list[list[Any]]) -> list[Any]:
        return [["", [], []], cells]

    table = {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in range(3)],
            [["", [], []], [span_row([_spanning_cell("A"), _spanning_cell("B"), _spanning_cell("C")])]],
            [
                [
                    ["", [], []],
                    0,
                    [],
                    [span_row([_spanning_cell("W" * 8, column_span=2), _spanning_cell("W" * 23)])],
                ]
            ],
            [["", [], []], []],
        ],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Mixed width failure"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/table.md",
        )

    context = exc_info.value.context
    assert context["column_minimum_width_units"] == [2, 13, 45]
    assert context["first_offending_column_index"] == 3
    assert context["first_offending_token"] == "W" * 23
    assert context["first_offending_column_minimum_width_units"] == 45
    assert context["offending_span_start_column_index"] is None
    assert context["offending_span_end_column_index"] is None
    assert context["offending_span_required_width_units"] is None


def test_table_code_block_prices_each_physical_line_as_indivisible_monospace() -> None:
    code_line = "aaaaa-" * 8
    table = _table_values(["Code"], [["placeholder"]])
    table["c"][4][0][3][0][1][0] = _block_cell([{"t": "CodeBlock", "c": [["", [], []], code_line]}])

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Verbatim boundary"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/verbatim.md",
        )

    assert exc_info.value.context["first_offending_token"] == code_line
    assert exc_info.value.context["required_width_units"] > 43


@pytest.mark.parametrize(
    ("command", "passing_count", "failing_count"),
    [(r"\sum", 14, 16), (r"\rightarrow", 19, 20)],
)
def test_table_math_controls_use_calibrated_visible_width(
    command: str,
    passing_count: int,
    failing_count: int,
) -> None:
    passing_source = command * passing_count
    passing_table = _table_values(["Expression"], [["placeholder"]])
    passing_table["c"][4][0][3][0][1][0][4][0]["c"] = [{"t": "Math", "c": [{"t": "InlineMath"}, passing_source]}]
    composition = compose_accessible_pandoc_document(
        _document([_header("Math boundary pass"), passing_table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/math.md",
    )
    assert composition.frame_count == 1

    math_source = command * failing_count
    table = _table_values(["Expression"], [["placeholder"]])
    table["c"][4][0][3][0][1][0][4][0]["c"] = [{"t": "Math", "c": [{"t": "InlineMath"}, math_source]}]

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Math boundary"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/math.md",
        )

    assert exc_info.value.context["first_offending_token"] == math_source
    assert exc_info.value.context["required_width_units"] > 43


def test_table_list_geometry_prices_indent_and_item_line_structure() -> None:
    horizontal = _table_values(["Item"], [["placeholder"]])
    horizontal["c"][4][0][3][0][1][0] = _block_cell([{"t": "BulletList", "c": [[_paragraph("a" * 42)]]}])
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as width_error:
        compose_accessible_pandoc_document(
            _document([_header("List width"), horizontal]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/list.md",
        )
    assert width_error.value.context["first_offending_token"] == "a" * 42

    vertical = _table_values(["Items"], [["placeholder"]])
    vertical["c"][4][0][3][0][1][0] = _block_cell(
        [{"t": "BulletList", "c": [[_paragraph(f"item-{index}")] for index in range(8)]}]
    )
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table\]") as height_error:
        compose_accessible_pandoc_document(
            _document([_header("List height"), vertical]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/list.md",
        )
    assert height_error.value.context["first_row_lines"] == 8


def test_table_cell_geometry_counts_authored_hard_lines() -> None:
    def table_with_lines(line_count: int) -> dict[str, Any]:
        table = _table_values(["Evidence"], [["placeholder"]])
        table["c"][4][0][3][0][1][0] = _block_cell([_hard_line_paragraph(line_count)])
        return table

    composition = compose_accessible_pandoc_document(
        _document([_header("Table hard lines"), table_with_lines(6)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/table-lines.md",
    )
    assert composition.frame_count == 1

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Table hard lines"), table_with_lines(7)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/table-lines.md",
        )
    assert exc_info.value.context["first_row_lines"] == 7


def test_unmodeled_rich_table_cell_block_fails_with_stable_diagnostic() -> None:
    table = _table_values(["Claim"], [["placeholder"]])
    table["c"][4][0][3][0][1][0] = _block_cell([{"t": "BlockQuote", "c": [_paragraph("bounded evidence")]}])

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-table-cell-block\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Rich cell"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/rich.md",
        )

    assert exc_info.value.context["block_type"] == "BlockQuote"


@pytest.mark.parametrize(
    ("glyph", "passing_count", "failing_count"),
    [("A", 30, 31), ("m", 26, 27), ("w", 30, 31), ("W", 22, 23)],
)
def test_proportional_glyph_classes_match_one_column_preflight_boundary(
    glyph: str,
    passing_count: int,
    failing_count: int,
) -> None:
    passing_token = glyph * passing_count
    failing_token = glyph * failing_count
    passing_table = _table_values(["Field"], [[passing_token]])
    failing_table = _table_values(["Field"], [[failing_token]])

    composition = compose_accessible_pandoc_document(
        _document([_header("Glyph boundary pass"), passing_table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/glyph-boundary.md",
    )
    assert composition.frame_count == 1
    assert proportional_text_width_units(passing_token) <= 43
    assert proportional_text_width_units(failing_token) > 43

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Glyph boundary fail"), failing_table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/glyph-boundary.md",
        )

    context = exc_info.value.context
    assert context["column_count"] == 1
    assert context["available_width_units"] == 43
    assert context["required_width_units"] > context["available_width_units"]
    assert context["first_offending_token"] == failing_token


def test_resolved_citeproc_family_name_sets_table_token_minimum() -> None:
    long_family = "A" * 32
    table = _table_values(["Source"], [["placeholder"]])
    table["c"][4][0][3][0][1][0][4][0]["c"] = [_citation("longfamily2026", rendered_text=f"({long_family} 2026)")]

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Resolved citation table"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert long_family in exc_info.value.context["first_offending_token"]
    assert exc_info.value.context["required_width_units"] > exc_info.value.context["available_width_units"]


def test_irreducible_eight_column_gallery_fails_before_latex_with_width_context() -> None:
    table = _table_values(
        [
            "Mechanism",
            "Evidence class",
            "Naive score",
            "Selected mean",
            "Mean difference",
            "Confidence interval",
            "Win fraction",
            "Display flag",
        ],
        [["byzantine", "directional", "0.6306", "0.6599", "0.0293", "[0.0124, 0.0462]", "0.84", "shown"]],
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Contamination gallery"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/extended-methods.md",
        )

    context = exc_info.value.context
    assert context["diagnostic_code"] == "slides.density.indivisible-table-width"
    assert context["column_count"] == 8
    assert context["body_font_pt"] == 20
    assert context["required_width_units"] > context["available_width_units"]
    assert len(context["column_minimum_width_units"]) == 8
    assert 1 <= context["first_offending_column_index"] <= 8
    assert context["first_offending_token"] != ""
    assert context["intercolumn_gutter_width_units"] == 7


def test_table_excerpt_geometry_accounts_for_cell_wrapping() -> None:
    table = _table_values(
        ["Metric", "Value"],
        [
            ["first", "short"],
            ["A source-owned explanatory cell " * 8, "long"],
            ["third", "short"],
        ],
    )

    composition = compose_accessible_pandoc_document(
        _document([_header("Exact values"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    assert len(rendered["c"][4][0][3]) == 1
    assert composition.excerpted_table_count == 1


def test_table_excerpt_geometry_accounts_for_continuation_title_lines() -> None:
    table = _table(10)
    composition = compose_accessible_pandoc_document(
        _document(
            [
                _header(
                    "A deliberately long table heading that preserves its full wording on a divider before projection"
                ),
                table,
            ]
        ),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    assert composition.section_divider_count == 1
    assert len(rendered["c"][4][0][3]) == 6


def test_table_excerpt_fails_closed_when_no_whole_row_fits() -> None:
    table = _table_values(
        ["Metric", "Condition"],
        [
            [
                "alpha beta gamma delta " * 24,
                "nested condition remains source bounded " * 24,
            ]
        ],
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Paired contrasts"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    context = exc_info.value.context
    assert context["source"] == "manuscript/results.md"
    assert context["heading"] == "Paired contrasts"
    assert context["diagnostic_code"] == "slides.density.indivisible-table"
    assert context["column_count"] == 2
    assert context["body_row_count"] == 1
    assert context["available_lines"] == 8
    assert context["fixed_lines"] == 1
    assert context["title_font_pt"] == 28
    assert context["body_font_pt"] == 20
    assert context["maximum_body_rows"] == 8
    assert context["global_header_lines"] >= 1
    assert context["footer_lines"] == 0
    assert context["first_body_header_lines"] == 0
    assert context["first_row_lines"] > context["available_lines"]
    assert len(context["resolved_widths"]) == 2
    assert len(context["column_character_capacities"]) == 2


def test_row_span_uses_physical_columns_and_cannot_be_fragmented_by_excerpt() -> None:
    table = {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}] for _ in range(2)],
            [["", [], []], [[["", [], []], [_spanning_cell("ID"), _spanning_cell("Interpretation")]]]],
            [
                [
                    ["", [], []],
                    0,
                    [],
                    [
                        [["", [], []], [_spanning_cell("A", row_span=2), _spanning_cell("short")]],
                        [
                            ["", [], []],
                            [_spanning_cell("A source-owned explanatory value requiring the second physical column")],
                        ],
                    ],
                ]
            ],
            [["", [], []], []],
        ],
    }

    composition = compose_accessible_pandoc_document(
        _document([_header("Spanning values"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )
    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Table")
    widths = [float(colspec[1]["c"]) for colspec in rendered["c"][2]]
    assert widths[1] > widths[0]
    assert len(rendered["c"][4][0][3]) == 2

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Spanning values"), table]),
            policy=AccessibleSlidePolicy(max_table_rows=1),
            source="manuscript/results.md",
        )
    assert exc_info.value.context["row_span_excerpt_blocked"] is True


def test_header_only_table_body_fails_closed_instead_of_disappearing() -> None:
    table = _table(0)
    table["c"][4][0][2] = [_row("subheader")]

    with pytest.raises(RenderingError, match=r"\[slides\.density\.header-only-table-body\]"):
        compose_accessible_pandoc_document(
            _document([_header("Header-only body"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_malformed_table_body_still_raises_renderer_error() -> None:
    table = _table(1)
    table["c"][4] = [[]]

    with pytest.raises(RenderingError, match="malformed Pandoc Table body"):
        compose_accessible_pandoc_document(
            _document([_header("Malformed body"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_captioned_listing_keeps_source_caption_but_projects_counter_only() -> None:
    caption = "A complete source-owned listing caption that consumes projected vertical geometry"
    code = "\n".join(f"x_{index} = {index}" for index in range(5))
    listing = {
        "t": "CodeBlock",
        "c": [["lst:test", ["python"], [["caption", caption]]], code],
    }
    document = _document([_header("Listing"), listing])

    composition = compose_accessible_pandoc_document(
        document,
        policy=AccessibleSlidePolicy(),
        source="manuscript/listing.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "CodeBlock")
    assert document["blocks"][1]["c"][0][2] == [["caption", caption]]
    assert rendered["c"][0][0] == "lst:test"
    assert rendered["c"][0][2] == [["caption", ""]]
    assert rendered["c"][1] == code

    overheight = {
        "t": "CodeBlock",
        "c": [
            ["lst:test", ["python"], [["caption", caption]]],
            "\n".join(f"x_{index} = {index}" for index in range(8)),
        ],
    }
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-code\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Listing"), overheight]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/listing.md",
        )
    assert exc_info.value.context["projected_caption_lines"] == 1
    assert exc_info.value.context["estimated_lines"] == 9


def test_shell_code_reflows_only_tokens_supported_by_breakable_monospace_contract() -> None:
    fitting = {"t": "CodeBlock", "c": [["", ["bash"], []], "W" * 33 + "'"]}
    fitting_composition = compose_accessible_pandoc_document(
        _document([_header("Fitting shell token"), fitting]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/shell.md",
    )
    assert any(block.get("t") == "CodeBlock" for block in fitting_composition.document["blocks"])

    reflowable = {"t": "CodeBlock", "c": [["", ["bash"], []], "W" * 35]}
    reflowed_composition = compose_accessible_pandoc_document(
        _document([_header("Reflowable shell token"), reflowable]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/shell.md",
    )
    reflowed = next(block for block in reflowed_composition.document["blocks"] if block.get("t") == "Para")
    assert reflowed["c"][0]["t"] == "Code"

    for unsafe_token in ("W" * 34 + "'", "W" * 34 + "{"):
        unsafe = {"t": "CodeBlock", "c": [["", ["bash"], []], unsafe_token]}
        with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-code-line\]") as exc_info:
            compose_accessible_pandoc_document(
                _document([_header("Unsafe shell token"), unsafe]),
                policy=AccessibleSlidePolicy(),
                source="manuscript/shell.md",
            )
        assert exc_info.value.context["first_offending_token"] == unsafe_token
        assert exc_info.value.context["maximum_characters"] == 34


def test_semantic_composer_isolates_figures_equations_code_and_evidence() -> None:
    image = {
        "t": "Image",
        "c": [["", [], []], _inlines("Trend lines"), ["trend.png", ""]],
    }
    figure = {
        "t": "Figure",
        "c": [["fig:trend", [], []], [None, [_paragraph("A detailed caption")]], [{"t": "Plain", "c": [image]}]],
    }
    equation = {"t": "Para", "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, "x = y"]}]}
    code = {"t": "CodeBlock", "c": [["", ["python"], []], "result = aggregate(request)"]}
    evidence = {"t": "BlockQuote", "c": [_paragraph("Bounded evidence statement")]}

    composition = compose_accessible_pandoc_document(
        _document([_header("Reading order"), figure, equation, code, evidence]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/methods.md",
    )

    classes = [classes for _title, classes in _classed_headers(composition.document)]
    assert classes == [
        {"figure-led"},
        {"equation-led"},
        {"code-led"},
        {"evidence-slide"},
    ]
    assert composition.figure_frame_count == 1
    assert "A detailed caption" not in " ".join(_visible_text(composition.document).split())
    rendered_figure = next(block for block in composition.document["blocks"] if block["t"] == "Figure")
    assert rendered_figure["c"][1] == [None, []]
    rendered_image = rendered_figure["c"][2][0]["c"][0]
    assert ["width", "98%"] in rendered_image["c"][0][2]
    assert ["height", "70%"] in rendered_image["c"][0][2]


def test_semantic_composer_drops_page_break_and_keeps_crossref_suffixed_equation_atomic() -> None:
    page_break = {"t": "RawBlock", "c": ["tex", "\\newpage"]}
    equation = {
        "t": "Para",
        "c": [
            {"t": "Math", "c": [{"t": "DisplayMath"}, "x = y"]},
            {"t": "Space"},
            {"t": "Str", "c": "{#eq:identity}"},
        ],
    }

    composition = compose_accessible_pandoc_document(
        _document([_header("Equation"), page_break, equation]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/formalism.md",
    )

    assert composition.frame_count == 1
    assert all(block != page_break for block in composition.document["blocks"])
    assert _classed_headers(composition.document)[0][1] == {"equation-led"}


def test_long_title_figure_allocation_uses_title_adjusted_body_geometry() -> None:
    image = {"t": "Image", "c": [["", [], []], _inlines("Trend"), ["trend.png", ""]]}
    figure = {
        "t": "Figure",
        "c": [["fig:trend", [], []], [None, []], [{"t": "Plain", "c": [image]}]],
    }
    authored_title = (
        "A deliberately wide evidence heading that wraps across multiple projection lines for careful reading"
    )
    composition = compose_accessible_pandoc_document(
        _document(
            [
                _header(authored_title),
                figure,
            ]
        ),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    assert composition.section_divider_count == 1
    headers = _classed_headers(composition.document)
    assert "section-divider" in headers[0][1]
    assert "part 2" in headers[1][0]
    continuation_headers = [block for block in composition.document["blocks"] if block["t"] == "Header"]
    continuation_header = continuation_headers[1]["c"]
    assert continuation_header[2]
    visible_title = " ".join(_visible_text(continuation_header[2]).split())
    assert proportional_text_width_units(visible_title) <= 36
    assert any(
        pair
        == [
            "aria-label",
            f"{authored_title}, part 2",
        ]
        for pair in continuation_header[1][2]
    )
    rendered_figure = next(block for block in composition.document["blocks"] if block["t"] == "Figure")
    rendered_image = rendered_figure["c"][2][0]["c"][0]
    # The compact continuation title fits one projected title line while the
    # complete authored heading remains its accessible name.
    assert ["width", "98%"] in rendered_image["c"][0][2]
    assert ["height", "70%"] in rendered_image["c"][0][2]


@pytest.mark.parametrize("authored_title", ["W" * 22, "unbreakable_identifier_" + "x" * 64])
def test_unbreakable_title_fails_before_divider_or_content_render(authored_title: str) -> None:
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-title-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header(authored_title), _paragraph("Bounded content.")]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["first_offending_token"] == authored_title
    assert exc_info.value.context["required_width_units"] > exc_info.value.context["available_width_units"]


def test_multi_panel_figure_preserves_one_bounded_authored_row() -> None:
    left = _image("left.png", width="45%", alt="Left panel")
    right = _image("right.png", width="45%", alt="Right panel")
    figure = {
        "t": "Figure",
        "c": [
            ["fig:panels", [], []],
            [None, [_paragraph("Complete caption")]],
            [{"t": "Plain", "c": [left, {"t": "Space"}, right]}],
        ],
    }

    composition = compose_accessible_pandoc_document(
        _document([_header("Panel comparison"), figure]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Figure")
    images = [item for item in rendered["c"][2][0]["c"] if item.get("t") == "Image"]
    assert len(images) == 2
    assert [[pair for pair in image["c"][0][2] if pair[0] == "width"] for image in images] == [
        [["width", "45%"]],
        [["width", "45%"]],
    ]
    assert all(["height", "70%"] in image["c"][0][2] for image in images)
    assert all("accessible-multi-image-panel" in image["c"][0][1] for image in images)


def test_multi_panel_figure_rejects_hard_line_break_pseudo_rows() -> None:
    figure = {
        "t": "Figure",
        "c": [
            ["fig:panels", [], []],
            [None, []],
            [
                {
                    "t": "Plain",
                    "c": [
                        _image("left.png", width="45%", alt="Left"),
                        {"t": "LineBreak"},
                        _image("right.png", width="45%", alt="Right"),
                    ],
                }
            ],
        ],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.multi-image-layout\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Panel comparison"), figure]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert "pseudo-rows" in str(exc_info.value)


def test_multi_panel_figure_requires_declared_minimum_usable_width() -> None:
    figure = {
        "t": "Figure",
        "c": [
            ["fig:panels", [], []],
            [None, []],
            [
                {
                    "t": "Plain",
                    "c": [
                        _image("left.png", width="30%", alt="Left"),
                        {"t": "Space"},
                        _image("right.png", width="30%", alt="Right"),
                    ],
                }
            ],
        ],
    }

    with pytest.raises(RenderingError, match=r"\[slides\.density\.multi-image-layout\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Panel comparison"), figure]),
            policy=AccessibleSlidePolicy(min_figure_area_percent=70),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["authored_total_width_percent"] == 60
    assert exc_info.value.context["minimum_total_width_percent"] == 70


@pytest.mark.parametrize(
    "body",
    [
        [
            {"t": "Plain", "c": [_image("left.png", width="45%", alt="Left")]},
            {"t": "Plain", "c": [_image("right.png", width="45%", alt="Right")]},
        ],
        [
            {
                "t": "Plain",
                "c": [
                    _image("left.png", width="55%", alt="Left"),
                    {"t": "Space"},
                    _image("right.png", width="55%", alt="Right"),
                ],
            }
        ],
    ],
)
def test_multi_panel_figure_fails_closed_on_unbounded_layout(body: list[dict[str, Any]]) -> None:
    figure = {"t": "Figure", "c": [["fig:panels", [], []], [None, []], body]}

    with pytest.raises(RenderingError, match=r"\[slides\.density\.multi-image-layout\]"):
        compose_accessible_pandoc_document(
            _document([_header("Panel comparison"), figure]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_single_image_figure_rejects_peer_prose_but_accepts_image_only_body() -> None:
    valid = {
        "t": "Figure",
        "c": [
            ["fig:single", [], []],
            [None, [_paragraph("Complete caption")]],
            [{"t": "Plain", "c": [_image("single.png", alt="Single panel")]}],
        ],
    }
    composition = compose_accessible_pandoc_document(
        _document([_header("Single panel"), valid]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )
    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Figure")
    assert ["width", "98%"] in rendered["c"][2][0]["c"][0]["c"][0][2]

    invalid = {
        "t": "Figure",
        "c": [
            ["fig:mixed", [], []],
            [None, []],
            [
                {"t": "Plain", "c": [_image("single.png", alt="Single panel")]},
                _paragraph("Peer prose that must not bypass density accounting."),
            ],
        ],
    }
    with pytest.raises(RenderingError, match=r"\[slides\.density\.mixed-image-frame\]"):
        compose_accessible_pandoc_document(
            _document([_header("Mixed single panel"), invalid]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_image_only_paragraph_receives_allocation_and_mixed_image_prose_fails_closed() -> None:
    image_paragraph = {"t": "Para", "c": [_image("trend.png", alt="Trend")]}
    composition = compose_accessible_pandoc_document(
        _document([_header("Image"), image_paragraph]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )
    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Para")
    assert ["width", "98%"] in rendered["c"][0]["c"][0][2]
    assert ["height", "70%"] in rendered["c"][0]["c"][0][2]

    mixed = {"t": "Para", "c": [_image("trend.png"), {"t": "Space"}, *_inlines("Peer prose")]}
    with pytest.raises(RenderingError, match=r"\[slides\.density\.mixed-image-frame\]"):
        compose_accessible_pandoc_document(
            _document([_header("Mixed"), mixed]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_linked_and_classed_image_wrappers_preserve_targets_and_allocation() -> None:
    linked = _linked_image("thumb.png", "full.png")
    composition = compose_accessible_pandoc_document(
        _document([_header("Linked image"), {"t": "Para", "c": [linked]}]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )
    rendered_link = next(block for block in composition.document["blocks"] if block["t"] == "Para")["c"][0]
    assert rendered_link["c"][2] == ["full.png", "Open full-size figure"]
    assert ["width", "98%"] in rendered_link["c"][1][0]["c"][0][2]
    assert ["height", "70%"] in rendered_link["c"][1][0]["c"][0][2]

    row = {
        "t": "Plain",
        "c": [
            _linked_image("left.png", "left-full.png", width="45%"),
            {"t": "Space"},
            _linked_image("right.png", "right-full.png", width="45%"),
        ],
    }
    figure = {"t": "Figure", "c": [["fig:links", [], []], [None, []], [row]]}
    composition = compose_accessible_pandoc_document(
        _document([_header("Linked panels"), figure]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )
    rendered = next(block for block in composition.document["blocks"] if block["t"] == "Figure")
    links = [item for item in rendered["c"][2][0]["c"] if item.get("t") == "Link"]
    assert [link["c"][2][0] for link in links] == ["left-full.png", "right-full.png"]

    wrapped = {
        "t": "Div",
        "c": [
            ["", ["figure-wrapper"], []],
            [{"t": "Para", "c": [{"t": "Span", "c": [["", ["panel"], []], [_image("panel.png")]]}]}],
        ],
    }
    wrapped_composition = compose_accessible_pandoc_document(
        _document([_header("Wrapped image"), wrapped]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )
    assert wrapped_composition.figure_frame_count == 1
    wrapped_div = next(block for block in wrapped_composition.document["blocks"] if block["t"] == "Div")
    wrapped_image = wrapped_div["c"][1][0]["c"][0]["c"][1][0]
    assert ["width", "98%"] in wrapped_image["c"][0][2]

    with pytest.raises(RenderingError, match=r"\[slides\.density\.mixed-image-frame\]"):
        compose_accessible_pandoc_document(
            _document(
                [
                    _header("Linked prose"),
                    {"t": "Para", "c": [_linked_image("thumb.png", "full.png", sibling_text="details")]},
                ]
            ),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )


def test_semantic_composer_rejects_accidental_title_only_but_accepts_section_divider() -> None:
    with pytest.raises(RenderingError, match=r"\[slides\.structure\.title-only\]"):
        compose_accessible_pandoc_document(
            _document([_header("Orphan heading")]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/empty.md",
        )

    composition = compose_accessible_pandoc_document(
        _document([_header("Methods", level=1)]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/methods.md",
    )
    assert composition.frame_count == 1
    assert composition.section_divider_count == 1


def test_semantic_composer_validates_title_only_divider_geometry() -> None:
    title = "W" * 23

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-title-token\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header(title, level=1)]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/divider.md",
        )

    assert exc_info.value.context["first_offending_token"] == title


@pytest.mark.parametrize(
    "separator",
    [
        {"t": "HorizontalRule"},
        {"t": "RawBlock", "c": ["tex", r"\pagebreak"]},
    ],
)
def test_semantic_composer_does_not_lose_separator_only_headings(separator: dict[str, Any]) -> None:
    with pytest.raises(RenderingError, match=r"\[slides\.structure\.title-only\]"):
        compose_accessible_pandoc_document(
            _document([_header("Orphan heading"), separator]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/orphan.md",
        )

    composition = compose_accessible_pandoc_document(
        _document([_header("Methods", level=1), separator]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/methods.md",
    )
    assert composition.frame_count == 1
    assert composition.section_divider_count == 1


def test_accessible_beamer_overflow_discards_derivative_with_stable_diagnostic(tmp_path: Path) -> None:
    log_file = tmp_path / "deck.log"
    compiled_pdf = tmp_path / "deck.pdf"
    log_file.write_text("Overfull \\vbox (3.5pt too high) detected at line 42\n", encoding="utf-8")
    compiled_pdf.write_bytes(b"%PDF-1.7\nfailed-layout")

    with pytest.raises(RenderingError, match=r"\[slides\.density\.beamer-overflow\]") as exc_info:
        _reject_accessible_beamer_overflow(log_file, compiled_pdf)

    assert not compiled_pdf.exists()
    assert exc_info.value.context["diagnostic_code"] == "slides.density.beamer-overflow"
    assert exc_info.value.context["finding_count"] == 1


def test_accessible_beamer_overflow_gate_ignores_non_layout_log_findings(tmp_path: Path) -> None:
    log_file = tmp_path / "deck.log"
    compiled_pdf = tmp_path / "deck.pdf"
    log_file.write_text(
        "LaTeX Warning: Reference `fig:other-deck' on page 2 undefined on input line 42.\n",
        encoding="utf-8",
    )
    compiled_pdf.write_bytes(b"%PDF-1.7\nlayout-valid")

    _reject_accessible_beamer_overflow(log_file, compiled_pdf)

    assert compiled_pdf.exists()


def test_accessible_reveal_names_slides_on_opening_headings_and_orders_navigation(tmp_path: Path) -> None:
    """Post-processing produces resolvable names without leaking build identities."""

    reveal = tmp_path / "deck_slides.html"
    reveal.write_text(
        "<!doctype html><html><head>"
        "<title>.deck-random.pandoc.accessible</title>"
        '<link rel="stylesheet" href="https://unpkg.com/reveal.js@5.2.1/dist/theme/white.css">'
        '</head><body><div class="reveal"><div class="slides">'
        '<section class="slide level2"><h2>Evidence <em>boundary</em></h2><p>First.</p></section>'
        '<section class="slide level2"><h2>Evidence <em>boundary</em></h2><p>Second.</p></section>'
        "</div></div><script>Reveal.initialize({keyboard: true});</script></body></html>",
        encoding="utf-8",
    )

    enhance_accessible_reveal(
        reveal,
        policy=AccessibleSlidePolicy(reader_href="../web/index.html"),
        registry_path=None,
    )
    # The transform is intentionally idempotent; rerunning a validation-stage
    # enhancement cannot duplicate document or slide identities.
    enhance_accessible_reveal(
        reveal,
        policy=AccessibleSlidePolicy(reader_href="../web/index.html"),
        registry_path=None,
    )
    rendered = reveal.read_text(encoding="utf-8")

    assert "<title>Evidence boundary — presentation</title>" in rendered
    assert '<h1 id="presentation-title-' in rendered
    assert 'class="visually-hidden">Evidence boundary — presentation</h1>' in rendered
    assert "</h2 id=" not in rendered
    heading_ids = re.findall(r'<h2\b[^>]*\bid="([^"]+)"', rendered)
    labelled_by = re.findall(r'<section\b[^>]*\baria-labelledby="([^"]+)"', rendered)
    assert len(heading_ids) == len(set(heading_ids)) == 2
    assert labelled_by == heading_ids
    assert rendered.index('class="skip-link"') < rendered.index('class="slide-reader-nav"')
    assert accessible_reveal_output_issues(reveal) == ()


def test_reveal_crossrefs_use_aux_numbers_and_preserve_bibliographic_citations() -> None:
    content = (
        '<section id="sec:local"><h2>Local</h2>'
        '<p>See <span class="citation" data-cites="sec:local">'
        "(<strong>sec:local?</strong>)</span>, "
        '<span class="citation" data-cites="eq:foreign">'
        "(<strong>eq:foreign?</strong>)</span>, and "
        '<span class="citation" data-cites="smith2026">(Smith 2026)</span>.</p></section>'
    )

    resolved = resolve_reveal_cross_references(
        content,
        {"sec:local": "2.1", "eq:foreign": "7"},
        strict=True,
    )

    assert '<a class="cross-reference" href="#sec:local">Section 2.1</a>' in resolved
    assert '<span class="cross-reference">Equation (7)</span>' in resolved
    assert '<span class="citation" data-cites="smith2026">(Smith 2026)</span>' in resolved
    assert "sec:local?" not in resolved
    assert "eq:foreign?" not in resolved


def test_reveal_raw_inline_math_references_use_aux_numbers_and_consume_tex_join() -> None:
    content = (
        '<section id="sec:local"><h2>Local</h2>'
        '<p>See Section~<span class="math inline">\\(\\ref{sec:local}\\)</span> '
        'and identity (<span class="math inline">\\(\\ref{eq:foreign}\\)</span>).</p></section>'
    )

    resolved = resolve_reveal_cross_references(
        content,
        {"sec:local": "2.1", "eq:foreign": "7"},
        strict=True,
    )

    assert 'Section\N{NO-BREAK SPACE}<a class="cross-reference" href="#sec:local">2.1</a>' in resolved
    assert 'identity (<span class="cross-reference">7</span>)' in resolved
    assert "~" not in resolved
    assert r"\ref{" not in resolved


def test_reveal_inline_equation_references_have_one_parenthesis_pair() -> None:
    content = (
        '<p>Equation <span class="math inline">\\(\\eqref{eq:model}\\)</span>; '
        'Equation (<span class="math inline">\\(\\eqref{eq:model}\\)</span>); '
        'identity (<span class="math inline">\\(\\ref{eq:model}\\)</span>).</p>'
    )

    resolved = resolve_reveal_cross_references(content, {"eq:model": "7"}, strict=True)
    visible = " ".join(re.sub(r"<[^>]+>", "", resolved).split())

    assert visible == "Equation (7); Equation (7); identity (7)."
    assert "((7))" not in visible


@pytest.mark.parametrize("command", ["ref", "eqref"])
def test_reveal_parenthesized_reference_consumes_tex_join(command: str) -> None:
    content = f'<p>Equation~(<span class="math inline">\\(\\{command}{{eq:model}}\\)</span>).</p>'

    resolved = resolve_reveal_cross_references(content, {"eq:model": "7"}, strict=True)
    visible = re.sub(r"<[^>]+>", "", resolved)

    assert visible == "Equation\N{NO-BREAK SPACE}(7)."
    assert "~" not in visible
    assert "((7))" not in visible
    assert reveal_reference_and_math_issues(resolved) == ()


def test_reveal_raw_reference_validation_ignores_code_but_covers_unsupported_reference_family() -> None:
    code = r"<pre><code>Use \ref{sec:example} and \pageref{sec:example} literally.</code></pre>"
    assert "raw TeX cross-reference" not in " ".join(reveal_reference_and_math_issues(code))

    for command in ("pageref", "nameref", "subref"):
        issues = reveal_reference_and_math_issues(rf"<p>Use \{command}{{sec:example}}.</p>")
        assert "Reveal deck contains a raw TeX cross-reference command" in issues


def test_reveal_raw_inline_math_reference_is_strict_and_visible_validation_fails_closed() -> None:
    content = '<p><span class="math inline">\\(\\ref{thm:missing}\\)</span></p>'

    with pytest.raises(RenderingError, match="cannot resolve references") as exc_info:
        resolve_reveal_cross_references(content, {}, strict=True)

    assert exc_info.value.context["unresolved_labels"] == ["thm:missing"]
    assert "Reveal deck contains a raw TeX cross-reference command" in reveal_reference_and_math_issues(content)


def test_reveal_crossrefs_humanize_standalone_and_strict_mode_rejects_missing_aux() -> None:
    content = (
        '<span class="citation" data-cites="sec:results-hierarchical">'
        "(<strong>sec:results-hierarchical?</strong>)</span>"
    )

    standalone = resolve_reveal_cross_references(content)
    assert "results hierarchical section" in standalone
    assert "sec:" not in standalone
    assert "?" not in standalone

    with pytest.raises(RenderingError, match=r"\[slides\.crossref\.reveal-unresolved\]") as exc_info:
        resolve_reveal_cross_references(content, strict=True)
    assert exc_info.value.context["unresolved_labels"] == ["sec:results-hierarchical"]


@pytest.mark.parametrize(
    "body",
    [
        "[@eq:model; @smith2026]",
        "(<strong>eq:model?</strong>; Smith 2026)",
    ],
)
def test_reveal_mixed_crossref_span_resolves_reference_and_preserves_bibliography(body: str) -> None:
    content = f'<span class="citation" data-cites="eq:model smith2026">{body}</span>'

    resolved = resolve_reveal_cross_references(content, {"eq:model": "7"}, strict=True)

    assert "Equation (7)" in resolved
    assert 'data-cites="smith2026"' in resolved
    assert "@smith2026" in resolved or "Smith 2026" in resolved
    assert "eq:model" not in re.sub(r"<[^>]+>", "", resolved)
    assert reveal_reference_and_math_issues(resolved) == ()


def test_reveal_crossref_suppresses_duplicate_authored_kind() -> None:
    content = (
        '<p>See <span class="citation" data-cites="fig:model">(<strong>fig:model?</strong>)</span>. '
        'Figure <span class="citation" data-cites="fig:model">(<strong>fig:model?</strong>)</span>. '
        'Table <span class="citation" data-cites="tbl:values">(<strong>tbl:values?</strong>)</span>.</p>'
    )

    resolved = resolve_reveal_cross_references(
        content,
        {"fig:model": "7", "tbl:values": "3"},
        strict=True,
    )
    visible = " ".join(re.sub(r"<[^>]+>", "", resolved).split())

    assert visible == "See Figure 7. Figure 7. Table 3."
    assert "Figure Figure" not in visible
    assert "Table Table" not in visible


def test_reveal_citation_crossrefs_handle_authored_parentheses_and_tex_join() -> None:
    content = (
        '<p>Equation (<span class="citation" data-cites="eq:model">'
        "(<strong>eq:model?</strong>)</span>); "
        'identity (<span class="citation" data-cites="eq:model">'
        "(<strong>eq:model?</strong>)</span>); "
        'Figure (<span class="citation" data-cites="fig:model">'
        "(<strong>fig:model?</strong>)</span>); "
        'Section~<span class="citation" data-cites="sec:model">'
        "(<strong>sec:model?</strong>)</span>.</p>"
    )

    resolved = resolve_reveal_cross_references(
        content,
        {"eq:model": "7", "fig:model": "2", "sec:model": "3"},
        strict=True,
    )
    visible = " ".join(re.sub(r"<[^>]+>", "", resolved).split(" "))

    assert visible == "Equation (7); identity (7); Figure (2); Section\N{NO-BREAK SPACE}3."
    assert "Equation Equation" not in visible
    assert "Figure Figure" not in visible
    assert "Section Section" not in visible
    assert "((7))" not in visible
    assert "~" not in visible
    assert reveal_reference_and_math_issues(resolved) == ()


@pytest.mark.parametrize(
    ("identifiers", "body", "expected"),
    [
        (
            "fig:model eq:model",
            "(<strong>fig:model?</strong>; <strong>eq:model?</strong>)",
            "See (Figure 2; Equation 7).",
        ),
        (
            "eq:model eq:second",
            "(<strong>eq:model?</strong>; <strong>eq:second?</strong>)",
            "See (7; 8).",
        ),
    ],
)
def test_reveal_parenthesized_multi_reference_citations_keep_types_unambiguous(
    identifiers: str,
    body: str,
    expected: str,
) -> None:
    content = f'<p>See (<span class="citation" data-cites="{identifiers}">{body}</span>).</p>'

    resolved = resolve_reveal_cross_references(
        content,
        {"fig:model": "2", "eq:model": "7", "eq:second": "8"},
        strict=True,
    )
    visible = re.sub(r"<[^>]+>", "", resolved)

    assert visible == expected
    assert reveal_reference_and_math_issues(resolved) == ()


def test_reveal_mathjax_validation_requires_one_exact_sri_loader() -> None:
    marker = _MATHJAX_CONFIG_SCRIPT
    exact = f'<script src="{MATHJAX_URL}" integrity="{_MATHJAX_INTEGRITY}" crossorigin="anonymous"></script>'
    wrong = f'<script src="{MATHJAX_URL}" integrity="sha384-AAAA" crossorigin="anonymous"></script>'

    assert reveal_reference_and_math_issues(marker + exact) == ()
    assert "exact pinned SRI" in " ".join(reveal_reference_and_math_issues(marker + wrong))
    assert "exactly one pinned MathJax loader" in " ".join(reveal_reference_and_math_issues(marker + exact + exact))
    legacy = (
        f'<script src="{ACCESSIBLE_REVEAL_URL}/plugin/math/math.js"></script>'
        "<script>Reveal.initialize({plugins: [ RevealMath ]});</script>"
    )
    assert "competing legacy RevealMath" in " ".join(reveal_reference_and_math_issues(marker + exact + legacy))

    empty_config = "<script data-template-mathjax-config></script>"
    assert "one canonical MathJax configuration" in " ".join(reveal_reference_and_math_issues(empty_config + exact))
    assert "one canonical MathJax configuration" in " ".join(reveal_reference_and_math_issues(exact + marker))


def test_reveal_mathjax_validation_rejects_nonempty_duplicate_loader_body() -> None:
    exact = f'<script src="{MATHJAX_URL}" integrity="{_MATHJAX_INTEGRITY}" crossorigin="anonymous"></script>'
    competing = f'<script src="{MATHJAX_URL}">ignored</script>'

    issues = reveal_reference_and_math_issues(_MATHJAX_CONFIG_SCRIPT + exact + competing)

    assert "exactly one pinned MathJax loader" in " ".join(issues)

    query_loader = f'<script src="{MATHJAX_URL}?bypass=1"></script>'
    query_issues = reveal_reference_and_math_issues(_MATHJAX_CONFIG_SCRIPT + exact + query_loader)
    assert "exactly one pinned MathJax loader" in " ".join(query_issues)

    duplicate_attribute = exact.replace(
        f'integrity="{_MATHJAX_INTEGRITY}"',
        f'integrity="{_MATHJAX_INTEGRITY}" integrity="sha384-AAAA"',
    )
    attribute_issues = reveal_reference_and_math_issues(_MATHJAX_CONFIG_SCRIPT + duplicate_attribute)
    assert "exact pinned SRI" in " ".join(attribute_issues)


def test_reveal_mathjax_activation_normalizes_existing_loaders(tmp_path: Path) -> None:
    html_file = tmp_path / "deck.html"
    raw = (
        "<html><head>"
        f'<script src="{MATHJAX_URL}" integrity="sha384-AAAA"></script>'
        f'<script defer src="{MATHJAX_URL}?bypass=1"></script>'
        "</head><body></body></html>"
    )
    html_file.write_text(activate_hardened_reveal_mathjax(raw), encoding="utf-8")

    harden_mathjax_script(html_file)

    hardened = html_file.read_text(encoding="utf-8")
    assert hardened.count(MATHJAX_URL) == 1
    assert hardened.count(_MATHJAX_INTEGRITY) == 1
    assert hardened.count("data-template-mathjax-config") == 1
    assert reveal_reference_and_math_issues(hardened) == ()


def test_reveal_mathjax_activation_removes_standalone_plugin_line_without_whitespace_residue() -> None:
    raw = (
        "<html><head>"
        f'<script src="{MATHJAX_URL}"></script>'
        "</head><body>\n"
        f'  <script src="{ACCESSIBLE_REVEAL_URL}/plugin/math/math.js"></script>\n'
        "  <script>Reveal.initialize({plugins: [ RevealMath ]});</script>\n"
        "</body></html>\n"
    )

    activated = activate_hardened_reveal_mathjax(raw)

    assert re.search(r"(?m)^[ \t]+$", activated) is None
    assert "/plugin/math/math.js" not in activated


def test_reveal_math_label_promotion_and_integrity_checks_reject_raw_derivatives() -> None:
    raw = (
        '<span class="math display">$$\\begin{aligned}x&amp;=1\\end{aligned}$$</span> '
        "{#eq:model} "
        '<span class="citation" data-cites="eq:model">(<strong>eq:model?</strong>)</span>'
    )

    promoted = promote_display_math_labels(raw)
    assert 'id="eq:model"' in promoted
    assert "{#eq:model}" not in promoted
    issues = reveal_reference_and_math_issues(promoted)
    assert "Reveal deck contains an unresolved cross-reference placeholder" in issues
    assert "Reveal display math retains literal $$ delimiters" in issues
    assert "Reveal display math contains an unrendered TeX environment without an executable math backend" in issues


def test_accessible_reveal_renderer_discards_output_that_fails_post_render_validation(tmp_path: Path) -> None:
    source = tmp_path / "deck.json"
    source.write_text("{}", encoding="utf-8")
    output = tmp_path / "deck.html"

    def write_invalid_reveal(command: list[str], **_kwargs: object) -> None:
        target = Path(command[command.index("-o") + 1])
        target.write_text(
            "<!doctype html><html><head><title>Invalid</title>"
            '<link rel="stylesheet" href="https://unpkg.com/reveal.js@5.2.1/dist/theme/white.css">'
            '</head><body><div class="reveal"><div class="slides">'
            '<section class="slide level2"><h2>Invalid math</h2><p>\\begin{aligned}x=1\\end{aligned}</p>'
            "</section></div></div><script>Reveal.initialize({keyboard: true});</script></body></html>",
            encoding="utf-8",
        )

    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path),
            slides_dir=str(tmp_path),
            slides_profile="accessible",
        ),
        process_runner=write_invalid_reveal,
    )

    with pytest.raises(RenderingError, match=r"\[slides\.accessibility\.reveal-output\]") as exc_info:
        renderer._render_revealjs(source, output)

    assert "Reveal deck contains a TeX display environment outside a math span" in exc_info.value.context["issues"]
    assert not output.exists()


@pytest.mark.slow
def test_real_accessible_reveal_resolves_crossrefs_and_hardens_complex_math(tmp_path: Path) -> None:
    """The browser surface receives numbered refs and executable aligned math."""

    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    pdf_dir = tmp_path / "output" / "pdf"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    pdf_dir.mkdir(parents=True)
    source = manuscript / "deck.md"
    source.write_text(
        "## Model {#sec:model}\n\n"
        "The local display [@eq:model] and the external discussion [@sec:other] are bounded references.\n\n"
        "$$\n\\begin{aligned}\nq(s) &= \\operatorname{normalize}(p(s)) \\\\\n\\log q(s) &= \\log p(s) - \\log Z.\n\\end{aligned}\n$$ {#eq:model}\n",
        encoding="utf-8",
    )
    (manuscript / "references.bib").write_text(
        "@article{fixture2026, title={Fixture}, author={Example, Ada}, year={2026}}\n",
        encoding="utf-8",
    )
    (pdf_dir / "_combined_manuscript.aux").write_text(
        "\\newlabel{sec:model}{{2}{4}{Model}{section.2}{}}\n"
        "\\newlabel{sec:other}{{3}{7}{Other}{section.3}{}}\n"
        "\\newlabel{eq:model}{{7}{5}{Model equation}{equation.7}{}}\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            pdf_dir=str(pdf_dir),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    output = renderer.render(
        source,
        output_format="revealjs",
        manuscript_dir=manuscript,
        strict_cross_deck_refs=True,
    )
    rendered = output.read_text(encoding="utf-8")

    assert MATHJAX_URL in rendered
    assert "data-template-mathjax-config" in rendered
    assert re.search(rf'<script\b[^>]*src="{re.escape(MATHJAX_URL)}"[^>]*integrity="sha384-', rendered)
    assert 'crossorigin="anonymous"' in rendered
    assert "RevealMath" not in rendered
    assert '<a class="cross-reference" href="#eq:model">Equation (7)</a>' in rendered
    assert '<span class="cross-reference">Section 3</span>' in rendered
    assert 'id="eq:model"' in rendered
    assert "eq:model?" not in rendered
    assert "sec:other?" not in rendered
    assert "{#eq:model}" not in rendered
    assert "$$" not in rendered
    assert r"\begin{aligned}" in rendered
    assert re.search(r"(?m)^[ \t]+$", rendered) is None
    assert accessible_reveal_output_issues(output) == ()


@pytest.mark.slow
def test_real_accessible_reveal_preserves_multi_image_widths_in_final_css(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    figures = tmp_path / "output" / "figures"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    figures.mkdir(parents=True)
    for name in ("left.png", "right.png"):
        _write_png(figures / name)
    source = manuscript / "panels.md"
    source.write_text(
        "## Panel comparison\n\n"
        "![Left panel](../output/figures/left.png){width=45%} "
        "![Right panel](../output/figures/right.png){width=45%}\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            figures_dir=str(figures),
            slides_profile="accessible",
        )
    )

    output = renderer.render(
        source,
        output_format="revealjs",
        manuscript_dir=manuscript,
        figures_dir=figures,
    )
    rendered = output.read_text(encoding="utf-8")
    image_tags = re.findall(r"<img\b[^>]+(?:left|right)\.png[^>]*>", rendered)

    assert len(image_tags) == 2
    assert all('class="accessible-multi-image-panel"' in tag for tag in image_tags)
    assert all(re.search(r'style="[^"]*width:\s*45(?:\.0)?%', tag) for tag in image_tags)
    assert ".reveal section.figure-led img:not(.accessible-multi-image-panel)" in rendered
    assert ".reveal section.figure-led img.accessible-multi-image-panel" in rendered
    universal_rule = re.search(r"\.reveal section\.figure-led img \{(?P<body>[^}]*)\}", rendered)
    assert universal_rule is not None
    assert "width: 100% !important" not in universal_rule.group("body")
    assert accessible_reveal_output_issues(output) == ()
    assert not list(slides.glob(".*.pandoc*.json"))


@pytest.mark.slow
def test_failed_accessible_pair_composition_removes_both_stale_derivatives(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    slides = tmp_path / "output" / "slides"
    slides.mkdir(parents=True)
    stale_pdf = slides / "dense_slides.pdf"
    stale_html = slides / "dense_slides.html"
    stale_pdf.write_bytes(b"%PDF-1.7 stale\n%%EOF\n")
    stale_html.write_text("stale prior deck", encoding="utf-8")
    source = tmp_path / "dense.md"
    source.write_text(
        "## Dense\n\n" + " ".join(f"word{index}" for index in range(81)) + "\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match="slides.density.indivisible-prose"):
        renderer.render_accessible_pair(source)

    assert not stale_pdf.exists()
    assert not stale_html.exists()
    assert not list(slides.glob(".*.pandoc*.json"))


def test_accessible_bibliography_conflict_cleans_raw_pandoc_json(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "citations.md"
    source.write_text("## Citation\n\nA bounded citation [@SharedKey].\n", encoding="utf-8")
    (manuscript / "a.bib").write_text(
        "@article{SharedKey, title={First}, author={Example, Ada}, year={2026}}\n",
        encoding="utf-8",
    )
    (manuscript / "b.bib").write_text(
        "@article{sharedkey, title={Second}, author={Example, Ben}, year={2026}}\n",
        encoding="utf-8",
    )

    def unexpected_process(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("bibliography validation must precede Pandoc execution")

    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        ),
        process_runner=unexpected_process,
    )

    with pytest.raises(BibliographyConflictError, match="Case-insensitive duplicate citation keys"):
        renderer.render(source, output_format="revealjs", manuscript_dir=manuscript)

    assert not list(slides.glob(".*.pandoc.json"))
    assert not list(slides.glob(".*.accessible.json"))
    assert not list(slides.glob(".*.accessible.json.tmp"))


@pytest.mark.slow
def test_real_accessible_reveal_render_has_semantics_long_description_and_reader_link(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    figures = tmp_path / "output" / "figures"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    figures.mkdir(parents=True)
    source = manuscript / "deck.md"
    source.write_text(
        "## Result\n\n"
        "A bounded result is shown with a non-color square marker and dashed line.\n\n"
        "![Visible trend caption.](../output/figures/trend.png){#fig:trend}\n\n"
        "## Values\n\n"
        "| Seed | Estimate |\n|---:|---:|\n" + "".join(f"| {index} | {index / 10:.1f} |\n" for index in range(10)),
        encoding="utf-8",
    )
    _write_png(figures / "trend.png")
    (figures / "figure_registry.json").write_text(
        json.dumps(
            {
                "schema_version": "1.2",
                "generated_by": "source-owned-test-producer",
                "exact_value_artifact": {
                    "json_path": "output/figures/figure_exact_values.json",
                    "markdown_path": "output/figures/figure_exact_values.md",
                    "identifiers": ["fig-values:trend"],
                },
                "figures": [
                    {
                        "label": "fig:trend",
                        "filename": "trend.png",
                        "alt_text": "A dashed line with square markers rises from left to right.",
                        "long_description": (
                            "Reading left to right, five square markers rise monotonically.\n\n"
                            "This explanatory fixture carries no scientific generalization."
                        ),
                        "exact_value_fallback": "fig-values:trend",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            figures_dir=str(figures),
            slides_profile="accessible",
        )
    )

    rendered = renderer.render(
        source,
        output_format="revealjs",
        manuscript_dir=manuscript,
        figures_dir=figures,
    ).read_text(encoding="utf-8")

    assert '<main id="main-content" tabindex="-1"' in rendered
    assert 'role="region" aria-label="Presentation slides"' in rendered
    assert rendered.count('role="main"') == 0
    assert rendered.count('aria-roledescription="slide"') == 3
    assert rendered.count('aria-labelledby="') >= 3
    assert "</h2 id=" not in rendered
    assert "<title>Result — presentation</title>" in rendered
    assert re.search(r'<h1\b[^>]*class="visually-hidden"', rendered)
    assert rendered.index('class="skip-link"') < rendered.index('class="slide-reader-nav"')
    assert 'aria-label="Presentation companion"' in rendered
    assert ">Open canonical HTML manuscript</a>" in rendered
    assert "https://unpkg.com/reveal.js@5.2.1/dist/theme/white.css" in rendered
    assert "theme/metropolis.css" not in rendered
    assert "keyboard: true" in rendered
    assert "main#main-content { inline-size: 100%; block-size: 100vh; min-block-size: 100vh; }" in rendered
    assert "min-height: 70vh" in rendered
    assert "height: calc(70vh - 5.5rem)" in rendered
    assert 'alt="A dashed line with square markers rises from left to right."' in rendered
    assert 'class="figure-long-description"' in rendered
    assert 'aria-details="fig-trend-long-description"' in rendered
    assert 'class="figure-exact-values"' in rendered
    assert 'href="../figures/figure_exact_values.md#fig-values-trend"' in rendered
    assert 'class="table-scroll"' in rendered
    assert 'aria-label="Scrollable data table"' in rendered
    assert rendered.count("<tr") == 7  # one header plus the six-row geometry-bounded excerpt
    assert not list(slides.glob(".*.pandoc*.json"))


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_accessible_beamer_preserves_plain_and_linked_image_aspect_ratio(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    figures = tmp_path / "output" / "figures"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    figures.mkdir(parents=True)
    for name in ("plain.png", "linked.png", "left.png", "right.png"):
        _write_png(figures / name)
    source = manuscript / "images.md"
    source.write_text(
        "## Plain image under a deliberately long accessible presentation heading\n\n"
        "![](../output/figures/plain.png)\n\n"
        "## Linked image\n\n"
        "[![Linked projection](../output/figures/linked.png)]"
        '(../output/figures/linked.png "Open full-size linked projection")\n\n'
        "## Linked panels\n\n"
        "[![Left panel](../output/figures/left.png){width=45%}]"
        '(../output/figures/left.png "Open full-size left panel") '
        "[![Right panel](../output/figures/right.png){width=45%}]"
        '(../output/figures/right.png "Open full-size right panel")\n',
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            figures_dir=str(figures),
            slides_profile="accessible",
            slides_min_figure_area_percent=80,
            latex_compiler=compiler,
        )
    )

    result = renderer.render(
        source,
        output_format="beamer",
        manuscript_dir=manuscript,
        figures_dir=figures,
    )

    assert result.is_file()
    tex = result.with_suffix(".tex").read_text(encoding="utf-8")
    for name in ("plain.png", "linked.png", "left.png", "right.png"):
        image_command = re.search(rf"\\includegraphics\[(?P<options>[^]]+)\]\{{[^}}]*{name}\}}", tex)
        assert image_command is not None
        assert "keepaspectratio" in image_command.group("options")


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_accessible_pair_uses_one_contract_for_beamer_and_reveal(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    pdf_dir = tmp_path / "output" / "pdf"
    figures = tmp_path / "output" / "figures"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    pdf_dir.mkdir(parents=True)
    figures.mkdir(parents=True)
    _write_png(figures / "allocation.png")
    source = manuscript / "deck.md"
    source.write_text(
        "## Evidence boundary {#sec:evidence-boundary}\n\n"
        "The projected derivative states one bounded engineering result and links the canonical reader.\n\n"
        "See Section~\\ref{sec:evidence-boundary} and identity (\\ref{eq:model}).\n\n"
        "## Figure allocation\n\n"
        "![A one-pixel renderer fixture.](../output/figures/allocation.png){#fig:allocation}\n\n"
        "## Numbering parity\n\n"
        "The local display is Equation [@eq:model].\n\n"
        "$$x = 1$$ {#eq:model}\n",
        encoding="utf-8",
    )
    (pdf_dir / "_combined_manuscript.aux").write_text(
        r"\newlabel{sec:evidence-boundary}{{3.2}{8}{Evidence boundary}{subsection.3.2}{}}"
        "\n" + r"\newlabel{eq:model}{{7}{9}{Model}{equation.7}{}}" + "\n",
        encoding="utf-8",
    )
    config = RenderingConfig(
        output_dir=str(tmp_path / "output"),
        pdf_dir=str(pdf_dir),
        slides_dir=str(slides),
        figures_dir=str(figures),
        slides_profile="accessible",
        latex_compiler=compiler,
    )

    pdf_result, html_result = SlidesRenderer(config).render_accessible_pair(
        source,
        manuscript_dir=manuscript,
        figures_dir=figures,
        strict_cross_deck_refs=True,
    )

    assert pdf_result.is_file()
    assert pdf_result.stat().st_size > 1_000
    assert html_result.is_file()
    reveal = html_result.read_text(encoding="utf-8")
    assert 'aria-label="Presentation slides"' in reveal
    assert 'aria-label="Presentation companion"' in reveal
    assert "data-template-accessible-slides" in reveal
    assert "https://unpkg.com/reveal.js@5.2.1/dist/theme/white.css" in reveal
    assert accessible_reveal_output_issues(html_result) == ()
    tex = pdf_result.with_suffix(".tex").read_text(encoding="utf-8")
    header = (slides / "_slides_math_header.tex").read_text(encoding="utf-8")
    assert "allowframebreaks" not in tex
    assert r"\setbeamerfont{frametitle}{size*={28pt}{32pt}}" in header
    assert r"\setbeamerfont{normal text}{size*={20pt}{24pt}}" in header
    assert r"\setbeamerfont{caption}{size*={16pt}{19pt}}" in header
    assert "Untagged PDF derivative" in header
    assert "HTML reader" in header
    assert r"height=0.7\textheight" in tex
    assert r"width=0.98\linewidth" in tex
    assert "keepaspectratio" in tex
    assert r"\caption{}" not in tex
    # Pandoc-crossref chooses format-specific prose (``eq. 7`` in TeX and
    # ``(7)`` in the browser), but both canonical derivatives must consume the
    # combined AUX's exact number rather than locally renumbering it as 1.
    assert "The local display is Equation eq.~7." in tex
    assert "See Section~3.2 and identity (7)." in " ".join(tex.split())
    assert r"\textasciitilde{}" not in tex
    assert r"\ref{eq:model}" not in tex
    visible_reveal = " ".join(re.sub(r"<[^>]+>", "", reveal).split())
    assert "The local display is Equation (7)." in visible_reveal
    assert "See Section 3.2 and identity (7)." in visible_reveal
    assert r"\ref{" not in visible_reveal
    assert "Equation Equation" not in visible_reveal
    assert not list(slides.glob(".*.pandoc*.json"))


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_accessible_captioned_listings_keep_counter_without_projecting_full_caption(tmp_path: Path) -> None:
    if not shutil.which("pandoc") or not shutil.which("pandoc-crossref") or not shutil.which("pdftotext"):
        pytest.skip("Pandoc, pandoc-crossref, and pdftotext are required")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "captioned-listings.md"
    caption = "A complete source-owned listing caption that consumes projected vertical geometry"
    listings: list[str] = []
    for lines in (4, 5):
        code = "\n".join(f"x_{index} = {index}" for index in range(lines))
        listings.append(f'## Listing {lines}\n\n```{{#lst:test-{lines} .python caption="{caption}"}}\n{code}\n```\n')
    source.write_text("\n".join(listings), encoding="utf-8")
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_result, html_result = renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert pdf_result.is_file()
    assert html_result.is_file()
    tex = pdf_result.with_suffix(".tex").read_text(encoding="utf-8")
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert tex.count(r"\caption{}") == 2
    assert r"\label{lst:test-4}" in tex
    assert r"\label{lst:test-5}" in tex
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log
    extracted = subprocess.run(
        ["pdftotext", str(pdf_result), "-"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "Listing 1:" in extracted
    assert "Listing 2:" in extracted
    assert caption not in extracted

    canonical_html = tmp_path / "canonical.html"
    subprocess.run(
        [
            "pandoc",
            str(source),
            "-t",
            "html",
            "--filter",
            shutil.which("pandoc-crossref") or "pandoc-crossref",
            "-o",
            str(canonical_html),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    canonical_text = " ".join(canonical_html.read_text(encoding="utf-8").split())
    assert caption in canonical_text


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_accessible_pair_sizes_unresolved_section_reference_fallbacks(tmp_path: Path) -> None:
    if not shutil.which("pandoc") or not shutil.which("pandoc-crossref"):
        pytest.skip("Pandoc and pandoc-crossref are required")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "deck.md"
    source.write_text(
        "## Server robustness setting\n\n"
        "Five structural extension studies (Studies 5–9, Supplementary sections) build on the same POMDP "
        "substrate and are described there: the moving disjoint-FOV sentinel ([@sec:results-moving]), the "
        "2-level hierarchical POMDP ([@sec:results-hierarchical]), the $N$-level extension "
        "([@sec:results-3level]), the 2-D sensitivity sweep ([@sec:results-sensitivity]), and parameter "
        "recovery ([@sec:results-parameter-recovery]).\n",
        encoding="utf-8",
    )
    config = RenderingConfig(
        output_dir=str(tmp_path / "output"),
        slides_dir=str(slides),
        slides_profile="accessible",
        latex_compiler=compiler,
    )

    pdf_result, html_result = SlidesRenderer(config).render_accessible_pair(
        source,
        manuscript_dir=manuscript,
    )

    assert pdf_result.is_file()
    assert html_result.is_file()
    tex = pdf_result.with_suffix(".tex").read_text(encoding="utf-8")
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert "Server robustness setting (part 2)" in tex
    assert r"\emph{results hierarchical section}" in tex
    assert "sec:results-" not in tex
    assert "Overfull \\vbox" not in log
    assert not list(slides.glob(".*.pandoc*.json"))


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_accessible_pair_budgets_citeproc_expansion_before_beamer(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "citations.md"
    source.write_text(
        "## Citation-rich synthesis\n\n"
        "The first bounded synthesis relates the generalized update, the federated objective, the belief-sharing "
        "term, and the robust loss while preserving each source claim [compare @bissiri2016, especially chapter "
        "twelve and appendix alpha; @mildner2025; @friston2024; "
        "@futami2018]. The second bounded synthesis relates divergence control, influence analysis, coherent "
        "updating, and matched inference while preserving each evidence class [@knoblauch2019; @fujisawa2008; "
        "@ghosh2016; @wilcoxon1945].\n",
        encoding="utf-8",
    )
    (manuscript / "references.bib").write_text(
        "\n".join(
            f"@article{{{key}, title={{{title}}}, author={{{author}}}, journal={{Journal}}, year={{{year}}}}}"
            for key, title, author, year in [
                ("bissiri2016", "General Bayes", "Bissiri, Pier Giovanni and Holmes, Christopher", "2016"),
                ("mildner2025", "Federated GVI", "Mildner, Clara and Westerhout, Tessa", "2025"),
                ("friston2024", "Belief sharing", "Friston, Karl and Albarracin, Mahault", "2024"),
                ("futami2018", "Robust inference", "Futami, Futoshi and Sato, Issei", "2018"),
                ("knoblauch2019", "Generalised variational inference", "Knoblauch, Jeremias and Jewson, Jack", "2019"),
                ("fujisawa2008", "Robust divergence", "Fujisawa, Hironori and Eguchi, Shinto", "2008"),
                ("ghosh2016", "Influence functions", "Ghosh, Abhik and Basu, Ayanendranath", "2016"),
                ("wilcoxon1945", "Matched comparisons", "Wilcoxon, Frank", "1945"),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    config = RenderingConfig(
        output_dir=str(tmp_path / "output"),
        slides_dir=str(slides),
        slides_profile="accessible",
        latex_compiler=compiler,
    )

    pdf_result, html_result = SlidesRenderer(config).render_accessible_pair(
        source,
        manuscript_dir=manuscript,
    )

    assert pdf_result.is_file()
    assert html_result.is_file()
    tex = pdf_result.with_suffix(".tex").read_text(encoding="utf-8")
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert "Citation-rich synthesis (part 2)" in tex
    assert "compare Bissiri" in tex
    assert "chapter twelve and appendix alpha" in tex
    assert "Overfull \\vbox" not in log
    assert "Overfull \\hbox" not in log


@pytest.mark.slow
@pytest.mark.parametrize(
    ("surface", "diagnostic_code"),
    [
        ("prose", "slides.density.indivisible-prose-token"),
        ("table", "slides.density.indivisible-table-width"),
    ],
)
def test_real_citeproc_long_family_name_fails_geometry_before_derivatives(
    tmp_path: Path,
    surface: str,
    diagnostic_code: str,
) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    long_family = "W" * 24
    source = manuscript / f"long-citation-{surface}.md"
    body = "Evidence [@longfamily2026].\n" if surface == "prose" else "| Source |\n|---|\n| [@longfamily2026] |\n"
    source.write_text(f"## Long family boundary\n\n{body}", encoding="utf-8")
    (manuscript / "references.bib").write_text(
        "@article{longfamily2026,\n"
        f"  author = {{Ada {{{long_family}}}}},\n"
        "  title = {A source-bound citation},\n"
        "  journal = {Journal},\n"
        "  year = {2026}\n"
        "}\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=rf"\[{re.escape(diagnostic_code)}\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert long_family in exc_info.value.context["first_offending_token"]
    assert exc_info.value.context["required_width_units"] > exc_info.value.context["available_width_units"]
    assert not (slides / f"{source.stem}_slides.pdf").exists()
    assert not (slides / f"{source.stem}_slides.html").exists()
    assert not list(slides.glob(".*.pandoc*.json"))


@pytest.mark.slow
@pytest.mark.parametrize(("glyph", "count"), [("W", 23), ("A", 32), ("m", 28)])
def test_real_pandoc_overwide_prose_glyph_token_fails_preflight(
    tmp_path: Path,
    glyph: str,
    count: int,
) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / f"prose-glyph-{ord(glyph)}.md"
    token = glyph * count
    source.write_text(f"## Prose token\n\n{token}\n", encoding="utf-8")
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose-token\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context["first_offending_token"] == token
    assert not (slides / f"{source.stem}_slides.pdf").exists()
    assert not (slides / f"{source.stem}_slides.html").exists()


@pytest.mark.slow
@pytest.mark.parametrize("literal", ["'", "[", "{"])
def test_real_pandoc_long_nonrewritable_prose_code_fails_preflight(tmp_path: Path, literal: str) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / f"prose-code-{ord(literal)}.md"
    code = "a" * 80 + literal
    source.write_text(f"## Prose code token\n\n`{code}`\n", encoding="utf-8")
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose-token\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context["first_offending_token"] == code
    assert not (slides / f"{source.stem}_slides.pdf").exists()
    assert not (slides / f"{source.stem}_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_pandoc_hard_line_boundary_passes_eight_and_rejects_nine(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    passing_source = manuscript / "hard-lines-pass.md"
    failing_source = manuscript / "hard-lines-fail.md"
    passing_source.write_text(
        "## Hard lines pass\n\n" + "  \n".join("x" for _ in range(8)) + "\n",
        encoding="utf-8",
    )
    failing_source.write_text(
        "## Hard lines fail\n\n" + "  \n".join("x" for _ in range(9)) + "\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_result, html_result = renderer.render_accessible_pair(passing_source, manuscript_dir=manuscript)
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert pdf_result.is_file()
    assert html_result.is_file()
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose\]") as exc_info:
        renderer.render_accessible_pair(failing_source, manuscript_dir=manuscript)
    assert exc_info.value.context["estimated_lines"] == 9
    assert not (slides / "hard-lines-fail_slides.pdf").exists()
    assert not (slides / "hard-lines-fail_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_proportional_prose_and_title_widths_fail_before_latex(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    passing_source = manuscript / "wide-prose-pass.md"
    passing_source.write_text("## Wide prose\n\n" + " ".join(["WW"] * 72) + "\n", encoding="utf-8")
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_result, html_result = renderer.render_accessible_pair(passing_source, manuscript_dir=manuscript)
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert pdf_result.is_file()
    assert html_result.is_file()
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log

    wide_prose = manuscript / "wide-prose-fail.md"
    wide_prose.write_text("## Wide prose\n\n" + " ".join(["WW"] * 80) + "\n", encoding="utf-8")
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose\]") as prose_error:
        renderer.render_accessible_pair(wide_prose, manuscript_dir=manuscript)
    assert prose_error.value.context["estimated_lines"] == 9
    assert prose_error.value.context["maximum_lines"] == 8

    titles = {
        "wide-title": "W" * 22,
        "identifier-title": "unbreakable_identifier_" + "x" * 64,
    }
    for stem, title in titles.items():
        source = manuscript / f"{stem}.md"
        source.write_text(f"## {title}\n\nBounded content.\n", encoding="utf-8")
        with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-title-token\]") as title_error:
            renderer.render_accessible_pair(source, manuscript_dir=manuscript)
        assert title_error.value.context["first_offending_token"] == title
        assert not (slides / f"{stem}_slides.pdf").exists()
        assert not (slides / f"{stem}_slides.html").exists()


@pytest.mark.slow
@pytest.mark.parametrize(
    ("stem", "markdown"),
    [
        (
            "body-note",
            "## Note boundary\n\nBounded statement.[^1]\n\n[^1]: A projected footnote is unsupported.\n",
        ),
        (
            "heading-note",
            "## Note boundary^[A title footnote is unsupported.]\n\nBounded statement.\n",
        ),
    ],
)
def test_real_pandoc_note_fails_before_projecting_subfloor_footnote(
    tmp_path: Path,
    stem: str,
    markdown: str,
) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / f"{stem}.md"
    source.write_text(markdown, encoding="utf-8")
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-note\]"):
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert not (slides / f"{stem}_slides.pdf").exists()
    assert not (slides / f"{stem}_slides.html").exists()


@pytest.mark.slow
def test_real_pandoc_optional_aligned_spacing_fails_before_derivatives(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "aligned-spacing.md"
    math_source = r"\begin{aligned}x&=1\\[10cm]y&=2\end{aligned}"
    source.write_text(f"## Aligned spacing\n\n$${math_source}$$\n", encoding="utf-8")
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-math-geometry\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context["unsupported_commands"] == ["row-spacing"]
    assert not (slides / "aligned-spacing_slides.pdf").exists()
    assert not (slides / "aligned-spacing_slides.html").exists()


@pytest.mark.slow
@pytest.mark.parametrize("surface", ["prose", "table", "heading"])
def test_real_pandoc_unknown_math_geometry_fails_before_derivatives(tmp_path: Path, surface: str) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / f"unknown-math-{surface}.md"
    math = r"$\rule{50cm}{1pt}$"
    if surface == "prose":
        heading = "Unknown math geometry"
        body = math
    elif surface == "table":
        heading = "Unknown math geometry"
        body = f"| Expression |\n|---|\n| {math} |"
    else:
        heading = f"Unknown math geometry {math}"
        body = "Bounded statement."
    source.write_text(f"## {heading}\n\n{body}\n", encoding="utf-8")
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-math-geometry\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context["unsupported_commands"] == ["rule"]
    assert not (slides / f"{source.stem}_slides.pdf").exists()
    assert not (slides / f"{source.stem}_slides.html").exists()


@pytest.mark.slow
def test_real_pandoc_raw_table_spacing_fails_before_derivatives(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "raw-table-spacing.md"
    source.write_text(
        "## Raw table spacing\n\n| Expression |\n|---|\n| \\hspace*{50cm} X |\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-raw-geometry\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context["unsupported_command"] == "hspace"
    assert not (slides / "raw-table-spacing_slides.pdf").exists()
    assert not (slides / "raw-table-spacing_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_nested_fraction_depth_sixteen_passes_and_seventeen_fails_preflight(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    passing_source = manuscript / "fraction-depth-pass.md"
    failing_source = manuscript / "fraction-depth-fail.md"
    passing_source.write_text(
        "## Fraction depth pass\n\n$$" + _nested_fraction_source(16) + "$$\n",
        encoding="utf-8",
    )
    failing_source.write_text(
        "## Fraction depth fail\n\n$$" + _nested_fraction_source(17) + "$$\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_result, html_result = renderer.render_accessible_pair(passing_source, manuscript_dir=manuscript)
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert pdf_result.is_file()
    assert html_result.is_file()
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log

    with pytest.raises(RenderingError, match=r"\[slides\.density\.math-height\]") as exc_info:
        renderer.render_accessible_pair(failing_source, manuscript_dir=manuscript)
    assert exc_info.value.context["estimated_lines"] == 9
    assert not (slides / "fraction-depth-fail_slides.pdf").exists()
    assert not (slides / "fraction-depth-fail_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_supported_multiline_math_rows_pass_then_fail_preflight(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()

    def aligned(rows: int, *, separator: str = r"\\ ") -> str:
        lines = [rf"x_{{{index}}}&={index}" for index in range(rows)]
        return r"\begin{aligned}" + separator.join(lines) + r"\end{aligned}"

    def substack(rows: int) -> str:
        body = r"\\ ".join("a" for _ in range(rows))
        return r"x_{\substack{" + body + r"}}=1"

    passing_source = manuscript / "multiline-pass.md"
    unspaced_rows = aligned(2, separator=r"\\")
    passing_source.write_text(
        f"## Row separator\n\n$${unspaced_rows}$$\n\n"
        f"## Aligned six\n\n$${aligned(6)}$$\n\n"
        f"## Substack fourteen\n\n$${substack(14)}$$\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_result, html_result = renderer.render_accessible_pair(passing_source, manuscript_dir=manuscript)
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert pdf_result.is_file()
    assert html_result.is_file()
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log

    failing_cases = {
        "aligned-seven": aligned(7),
        "substack-fifteen": substack(15),
    }
    for stem, math_source in failing_cases.items():
        source = manuscript / f"{stem}.md"
        source.write_text(f"## {stem}\n\n$${math_source}$$\n", encoding="utf-8")
        with pytest.raises(RenderingError, match=r"\[slides\.density\.math-height\]") as exc_info:
            renderer.render_accessible_pair(source, manuscript_dir=manuscript)
        assert exc_info.value.context["math_source"] == math_source
        assert exc_info.value.context["estimated_lines"] == 9
        assert exc_info.value.context["maximum_lines"] == 8
        assert not (slides / f"{stem}_slides.pdf").exists()
        assert not (slides / f"{stem}_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_accessible_pair_renders_ordinary_three_five_and_six_column_tables(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "tables.md"
    source.write_text(
        "## Notation mapping\n\n"
        "| Symbol | Meaning | Code term |\n"
        "|---|---|---|\n"
        "| $o$ | Observation/outcome index | `observation_or_outcome_index` |\n\n"
        "## Robustness onset\n\n"
        "| Mechanism | Onset rate | Naive @ worst | Robust @ worst | Robust method @ worst |\n"
        "|---|---:|---:|---:|---|\n"
        "| confident-wrong | 0.25 | 0.6306 | 0.6599 | reverse-KL preset |\n\n"
        "## Inference and planning\n\n"
        "| Method | Raw p | q | Power | Target $n_{\\rm trial}$ | Reject |\n"
        "|---|---:|---:|---:|---:|---|\n"
        "| Robust preset | 0.001 | 0.004 | 0.91 | 64 | yes |\n",
        encoding="utf-8",
    )
    config = RenderingConfig(
        output_dir=str(tmp_path / "output"),
        slides_dir=str(slides),
        slides_profile="accessible",
        latex_compiler=compiler,
    )

    pdf_result, html_result = SlidesRenderer(config).render_accessible_pair(
        source,
        manuscript_dir=manuscript,
    )

    assert pdf_result.is_file()
    assert html_result.is_file()
    tex = pdf_result.with_suffix(".tex").read_text(encoding="utf-8")
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert tex.count(r"\begin{longtable}") == 3
    assert "Observation/outcome" in tex
    assert r"\breaktt{observation\_or\_outcome\_index}" in tex
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log


@pytest.mark.slow
def test_real_pandoc_grid_table_code_block_fails_as_indivisible_monospace(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "verbatim-grid.md"
    code_line = "aaaaa-" * 8
    inner_width = len(code_line) + 4
    border = "+" + "-" * (inner_width + 2) + "+"
    header_border = "+" + "=" * (inner_width + 2) + "+"
    source.write_text(
        "\n".join(
            [
                "## Verbatim grid boundary",
                "",
                border,
                "| " + "Code".ljust(inner_width) + " |",
                header_border,
                "| " + ("    " + code_line).ljust(inner_width) + " |",
                border,
                "",
            ]
        ),
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context["first_offending_token"] == code_line
    assert exc_info.value.context["required_width_units"] > 43
    assert not (slides / "verbatim-grid_slides.pdf").exists()
    assert not (slides / "verbatim-grid_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
@pytest.mark.parametrize(
    ("command", "passing_count", "failing_count"),
    [(r"\sum", 14, 16), (r"\rightarrow", 19, 20)],
)
def test_real_pandoc_table_math_controls_fail_calibrated_width_preflight(
    tmp_path: Path,
    command: str,
    passing_count: int,
    failing_count: int,
) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    passing_source = manuscript / f"math-control-{len(command)}-pass.md"
    failing_source = manuscript / f"math-control-{len(command)}-fail.md"
    passing_math = command * passing_count
    failing_math = command * failing_count
    passing_source.write_text(
        f"## Math control pass\n\n| Expression |\n|---|\n| ${passing_math}$ |\n",
        encoding="utf-8",
    )
    failing_source.write_text(
        f"## Math control fail\n\n| Expression |\n|---|\n| ${failing_math}$ |\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_result, html_result = renderer.render_accessible_pair(passing_source, manuscript_dir=manuscript)
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert pdf_result.is_file()
    assert html_result.is_file()
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        renderer.render_accessible_pair(failing_source, manuscript_dir=manuscript)

    assert exc_info.value.context["first_offending_token"] == failing_math
    assert exc_info.value.context["required_width_units"] > 43
    assert not (slides / f"{failing_source.stem}_slides.pdf").exists()
    assert not (slides / f"{failing_source.stem}_slides.html").exists()


def test_accessible_seqsplit_probe_uses_injected_credential_free_process_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "must-not-cross-render-boundary")
    calls: list[tuple[list[str], dict[str, object]]] = []

    def locate_seqsplit(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="/texmf/seqsplit.sty\n", stderr="")

    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path),
            slides_dir=str(tmp_path),
            slides_profile="accessible",
            security_profile="untrusted",
            untrusted_temp_root=str(tmp_path),
        ),
        process_runner=locate_seqsplit,
    )

    renderer._require_accessible_seqsplit()

    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command == ["kpsewhich", "seqsplit.sty"]
    assert kwargs["check"] is False
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True
    assert kwargs["timeout"] == 30
    environment = kwargs["env"]
    assert isinstance(environment, dict)
    assert set(environment) <= {"PATH", "LANG", "LC_ALL", "HOME", "TMPDIR"}
    assert environment["HOME"] == str(tmp_path)
    assert environment["TMPDIR"] == str(tmp_path)
    assert "AWS_SECRET_ACCESS_KEY" not in environment
    assert "must-not-cross-render-boundary" not in environment.values()


@pytest.mark.slow
def test_accessible_long_code_requires_seqsplit_before_latex(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    empty_texmf = tmp_path / "empty-texmf"
    manuscript.mkdir()
    empty_texmf.mkdir()
    source = manuscript / "seqsplit-required.md"
    source.write_text(
        "## Long code capability\n\n| Code |\n|---|\n| `" + "a" * 64 + "` |\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TEXMFHOME", str(empty_texmf))
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=r"\[slides\.capability\.seqsplit-required\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context == {
        "diagnostic_code": "slides.capability.seqsplit-required",
        "required_latex_package": "seqsplit",
    }
    assert not (slides / "seqsplit-required_slides.pdf").exists()
    assert not (slides / "seqsplit-required_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_pandoc_grid_table_list_width_and_height_boundaries(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()

    def write_grid(path: Path, items: list[str]) -> None:
        inner_width = max(len("Items"), *(len(item) + 2 for item in items)) + 2
        border = "+" + "-" * (inner_width + 2) + "+"
        header_border = "+" + "=" * (inner_width + 2) + "+"
        path.write_text(
            "\n".join(
                [
                    f"## {path.stem}",
                    "",
                    border,
                    "| " + "Items".ljust(inner_width) + " |",
                    header_border,
                    *("| " + ("* " + item).ljust(inner_width) + " |" for item in items),
                    border,
                    "",
                ]
            ),
            encoding="utf-8",
        )

    width_pass = manuscript / "list-width-pass.md"
    width_fail = manuscript / "list-width-fail.md"
    height_pass = manuscript / "list-height-pass.md"
    height_fail = manuscript / "list-height-fail.md"
    write_grid(width_pass, ["a" * 40])
    write_grid(width_fail, ["a" * 42])
    write_grid(height_pass, [f"item-{index}" for index in range(6)])
    write_grid(height_fail, [f"item-{index}" for index in range(8)])
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    for passing_source in (width_pass, height_pass):
        pdf_result, html_result = renderer.render_accessible_pair(passing_source, manuscript_dir=manuscript)
        log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
        assert pdf_result.is_file()
        assert html_result.is_file()
        assert "Overfull \\hbox" not in log
        assert "Overfull \\vbox" not in log

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as width_error:
        renderer.render_accessible_pair(width_fail, manuscript_dir=manuscript)
    assert width_error.value.context["first_offending_token"] == "a" * 42

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table\]") as height_error:
        renderer.render_accessible_pair(height_fail, manuscript_dir=manuscript)
    assert height_error.value.context["first_row_lines"] == 8


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_general_list_width_nested_height_and_font_floor_boundaries(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    if not shutil.which("pdftotext"):
        pytest.skip("pdftotext is required for projected glyph-size evidence")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    width_pass = manuscript / "general-list-width-pass.md"
    width_fail = manuscript / "general-list-width-fail.md"
    nested_pass = manuscript / "nested-list-pass.md"
    nested_fail = manuscript / "nested-list-fail.md"
    width_pass.write_text("## List width pass\n\n- " + "a" * 40 + "\n", encoding="utf-8")
    width_fail.write_text("## List width fail\n\n- " + "a" * 42 + "\n", encoding="utf-8")
    nested_pass.write_text(
        "## Nested list pass\n\n- parent\n" + "".join(f"  - child {index}\n" for index in range(7)),
        encoding="utf-8",
    )
    nested_fail.write_text(
        "## Nested list fail\n\n- parent\n" + "".join(f"  - child {index}\n" for index in range(8)),
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    width_pdf, width_html = renderer.render_accessible_pair(width_pass, manuscript_dir=manuscript)
    assert width_pdf.is_file()
    assert width_html.is_file()
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose-token\]"):
        renderer.render_accessible_pair(width_fail, manuscript_dir=manuscript)

    nested_pdf, nested_html = renderer.render_accessible_pair(nested_pass, manuscript_dir=manuscript)
    assert nested_pdf.is_file()
    assert nested_html.is_file()
    nested_log = nested_pdf.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert "Overfull \\hbox" not in nested_log
    assert "Overfull \\vbox" not in nested_log
    bbox_xml = tmp_path / "nested-list.xml"
    subprocess.run(
        ["pdftotext", "-bbox-layout", str(nested_pdf), str(bbox_xml)],
        check=True,
        capture_output=True,
        text=True,
    )
    words = [
        node
        for node in ET.parse(bbox_xml).getroot().iter()
        if node.tag.endswith("word") and (node.text or "") in {"parent", "child"}
    ]
    assert len(words) == 8
    glyph_heights = [float(node.attrib["yMax"]) - float(node.attrib["yMin"]) for node in words]
    assert min(glyph_heights) >= 18.0

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-list\]") as height_error:
        renderer.render_accessible_pair(nested_fail, manuscript_dir=manuscript)
    assert height_error.value.context["estimated_lines"] == 9
    assert not (slides / "nested-list-fail_slides.pdf").exists()
    assert not (slides / "nested-list-fail_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_definition_list_seven_entries_pass_and_eight_fail_preflight(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()

    def definition_source(path: Path, count: int) -> None:
        path.write_text(
            f"## {path.stem}\n\n" + "\n\n".join(f"term{index}\n: x" for index in range(count)) + "\n",
            encoding="utf-8",
        )

    passing_source = manuscript / "definitions-pass.md"
    failing_source = manuscript / "definitions-fail.md"
    definition_source(passing_source, 7)
    definition_source(failing_source, 8)
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_result, html_result = renderer.render_accessible_pair(passing_source, manuscript_dir=manuscript)
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert pdf_result.is_file()
    assert html_result.is_file()
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-definition-list\]") as exc_info:
        renderer.render_accessible_pair(failing_source, manuscript_dir=manuscript)
    assert exc_info.value.context["estimated_lines"] == 9
    assert not (slides / "definitions-fail_slides.pdf").exists()
    assert not (slides / "definitions-fail_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_one_definition_eight_paragraphs_pass_and_ten_fail_preflight(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()

    def definition_source(path: Path, count: int) -> None:
        continuation = "\n\n".join(f"  paragraph {index}" for index in range(1, count))
        path.write_text(
            f"## {path.stem}\n\nterm\n: paragraph 0\n\n{continuation}\n",
            encoding="utf-8",
        )

    passing_source = manuscript / "one-definition-pass.md"
    failing_source = manuscript / "one-definition-fail.md"
    definition_source(passing_source, 8)
    definition_source(failing_source, 10)
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_result, html_result = renderer.render_accessible_pair(passing_source, manuscript_dir=manuscript)
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert pdf_result.is_file()
    assert html_result.is_file()
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-definition-list\]") as exc_info:
        renderer.render_accessible_pair(failing_source, manuscript_dir=manuscript)
    assert exc_info.value.context["estimated_lines"] == 10
    assert not (slides / "one-definition-fail_slides.pdf").exists()
    assert not (slides / "one-definition-fail_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_loose_list_seven_paragraphs_pass_and_eight_fail_preflight(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()

    def list_source(path: Path, count: int) -> None:
        continuation = "\n\n".join(f"  paragraph {index}" for index in range(1, count))
        path.write_text(
            f"## {path.stem}\n\n- paragraph 0\n\n{continuation}\n",
            encoding="utf-8",
        )

    passing_source = manuscript / "loose-list-pass.md"
    failing_source = manuscript / "loose-list-fail.md"
    list_source(passing_source, 7)
    list_source(failing_source, 8)
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_result, html_result = renderer.render_accessible_pair(passing_source, manuscript_dir=manuscript)
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert pdf_result.is_file()
    assert html_result.is_file()
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-list\]") as exc_info:
        renderer.render_accessible_pair(failing_source, manuscript_dir=manuscript)
    assert exc_info.value.context["estimated_lines"] == 9
    assert not (slides / "loose-list-fail_slides.pdf").exists()
    assert not (slides / "loose-list-fail_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_evidence_quote_nine_paragraphs_pass_and_ten_fail_preflight(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()

    def quote_source(path: Path, count: int) -> None:
        path.write_text(
            f"## {path.stem}\n\n" + "\n>\n".join("> x" for _ in range(count)) + "\n",
            encoding="utf-8",
        )

    passing_source = manuscript / "evidence-pass.md"
    failing_source = manuscript / "evidence-fail.md"
    quote_source(passing_source, 9)
    quote_source(failing_source, 10)
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_result, html_result = renderer.render_accessible_pair(passing_source, manuscript_dir=manuscript)
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert pdf_result.is_file()
    assert html_result.is_file()
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-evidence\]") as exc_info:
        renderer.render_accessible_pair(failing_source, manuscript_dir=manuscript)
    assert exc_info.value.context["estimated_lines"] == 9
    assert not (slides / "evidence-fail_slides.pdf").exists()
    assert not (slides / "evidence-fail_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
@pytest.mark.parametrize(
    ("literal", "latex_literal"),
    [
        ("'", r"\textquotesingle{}"),
        ("[", "{[}"),
        ("]", "{]}"),
        (" ", r"\ "),
    ],
)
def test_real_pandoc_code_serialization_matches_breaktt_predicate_across_threshold(
    tmp_path: Path,
    literal: str,
    latex_literal: str,
) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / f"code-contract-{ord(literal)}.md"
    safe_below = "a" * 15
    safe_at = "a" * 16
    unsafe_below = "a" * 7 + literal + "a" * 7
    unsafe_at = "a" * 7 + literal + "a" * 8
    source.write_text(
        "## Code serialization contract\n\n"
        "| Code |\n|---|\n"
        f"| `{safe_below}` |\n"
        f"| `{safe_at}` |\n"
        f"| `{unsafe_below}` |\n"
        f"| `{unsafe_at}` |\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_result, html_result = renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert pdf_result.is_file()
    assert html_result.is_file()
    tex = pdf_result.with_suffix(".tex").read_text(encoding="utf-8")
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    expected_breakable_count = 2 if literal == " " else 1
    assert tex.count(r"\breaktt{") == expected_breakable_count
    assert rf"\breaktt{{{safe_at}}}" in tex
    serialized_at = f"{'a' * 7}{latex_literal}{'a' * 8}"
    if literal == " ":
        assert rf"\breaktt{{{serialized_at}}}" in tex
    else:
        assert rf"\texttt{{{serialized_at}}}" in tex
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log


@pytest.mark.slow
def test_real_pandoc_gallery_fails_width_preflight_before_derivatives(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "gallery.md"
    source.write_text(
        "## Contamination gallery\n\n"
        "| Mechanism | Evidence class | Naive score | Selected mean | Mean difference | Confidence interval | Win fraction | Display flag |\n"
        "|---|---|---:|---:|---:|---|---:|---|\n"
        "| byzantine | directional | 0.6306 | 0.6599 | 0.0293 | [0.0124, 0.0462] | 0.84 | shown |\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context["column_count"] == 8
    assert exc_info.value.context["required_width_units"] > exc_info.value.context["available_width_units"]
    assert not (slides / "gallery_slides.pdf").exists()
    assert not (slides / "gallery_slides.html").exists()
    assert not list(slides.glob(".*.pandoc*.json"))


@pytest.mark.slow
@pytest.mark.requires_latex
@pytest.mark.parametrize(
    ("glyph", "passing_count", "failing_count"),
    [("A", 30, 31), ("m", 26, 27), ("w", 30, 31), ("W", 22, 23)],
)
def test_real_accessible_table_glyph_boundary_passes_then_fails_preflight(
    tmp_path: Path,
    glyph: str,
    passing_count: int,
    failing_count: int,
) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    passing_source = manuscript / f"glyph-{ord(glyph)}-pass.md"
    failing_source = manuscript / f"glyph-{ord(glyph)}-fail.md"
    passing_token = glyph * passing_count
    failing_token = glyph * failing_count
    passing_source.write_text(
        f"## Glyph boundary pass\n\n| Field |\n|---|\n| {passing_token} |\n",
        encoding="utf-8",
    )
    failing_source.write_text(
        f"## Glyph boundary fail\n\n| Field |\n|---|\n| {failing_token} |\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_result, html_result = renderer.render_accessible_pair(passing_source, manuscript_dir=manuscript)
    log = pdf_result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert pdf_result.is_file()
    assert html_result.is_file()
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        renderer.render_accessible_pair(failing_source, manuscript_dir=manuscript)

    assert exc_info.value.context["first_offending_token"] == failing_token
    assert exc_info.value.context["required_width_units"] > 43
    assert not (slides / f"{failing_source.stem}_slides.pdf").exists()
    assert not (slides / f"{failing_source.stem}_slides.html").exists()


@pytest.mark.slow
@pytest.mark.parametrize("literal", ["{", "\\", "~", "<"])
def test_real_pandoc_braced_code_literals_remain_indivisible_at_preflight(
    tmp_path: Path,
    literal: str,
) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "unsafe-code.md"
    unsafe_code = "W" * 43 + literal
    source.write_text(
        f"## Unsafe code serialization\n\n| Code |\n|---|\n| `{unsafe_code}` |\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            slides_profile="accessible",
        )
    )

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context["first_offending_token"] == unsafe_code
    assert exc_info.value.context["required_width_units"] > 43
    assert not (slides / "unsafe-code_slides.pdf").exists()
    assert not (slides / "unsafe-code_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_accessible_pair_removes_beamer_when_reveal_postprocessing_fails(tmp_path: Path) -> None:
    """A second-member failure cannot leave the first derivative publishable."""

    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    figures = tmp_path / "output" / "figures"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    figures.mkdir(parents=True)
    source = manuscript / "deck.md"
    source.write_text("## Evidence boundary\n\nOne bounded statement.\n", encoding="utf-8")
    (figures / "figure_registry.json").write_text("{malformed", encoding="utf-8")
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            figures_dir=str(figures),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    with pytest.raises(RenderingError, match="Failed to load figure accessibility registry"):
        renderer.render_accessible_pair(source, manuscript_dir=manuscript, figures_dir=figures)

    assert (slides / "deck_slides.tex").is_file()  # Beamer completed before Reveal post-processing failed.
    assert not (slides / "deck_slides.pdf").exists()
    assert not (slides / "deck_slides.html").exists()
    assert not list(slides.glob(".*.pandoc*.json"))
