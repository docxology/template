"""Semantic composer math pricing: raw TeX geometry, aligned environments, and math height/width (split from test_slides_accessibility.py)."""

from __future__ import annotations

from typing import Any
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    compose_accessible_pandoc_document,
)
from infrastructure.rendering._slides_accessibility_contracts import (
    tex_math_width_units,
    tex_math_vertical_line_demand,
    unsupported_tex_math_commands,
)
from ._slides_accessibility_helpers import (
    _inlines,
    _header,
    _paragraph,
    _nested_fraction_source,
    _document,
    _table_values,
)


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


@pytest.mark.parametrize(
    "math_source",
    [
        r"1,\dots,n",
        r"1,\ldots,n",
        r"\arg\min_x f(x)",
        r"q^\ast",
        r"\textstyle\sum_i x_i",
        r"D_\alpha\xrightarrow[\alpha\to 1]{}\mathrm{KL}",
        r"A^\star",
        r"x\downarrow y",
        r"\lfloor x\rfloor",
        r"x^\top y",
    ],
)
def test_semantic_composer_accepts_declared_standard_math_commands(math_source: str) -> None:
    equation = {"t": "Para", "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, math_source]}]}

    composition = compose_accessible_pandoc_document(
        _document([_header("Standard math"), equation]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/standard-math.md",
    )

    assert composition.frame_count == 1
    assert unsupported_tex_math_commands(math_source) == ()


def test_standard_math_command_widths_are_positive_except_for_style() -> None:
    expected_widths = {
        r"\dots": 3,
        r"\ldots": 3,
        r"\arg": 3,
        r"\ast": 2,
        r"\xrightarrow": 3,
        r"\star": 2,
        r"\downarrow": 3,
        r"\lfloor": 1,
        r"\rfloor": 1,
        r"\top": 2,
    }

    assert {source: tex_math_width_units(source) for source in expected_widths} == expected_widths
    assert tex_math_width_units(r"\textstyle x") == tex_math_width_units("x")


@pytest.mark.parametrize(
    "labeled_arrow",
    [
        r"\xrightarrow{\alpha}",
        r"\xrightarrow[\alpha\to 1]{\mathrm{limit}}",
    ],
)
def test_xrightarrow_width_includes_its_visible_labels(labeled_arrow: str) -> None:
    assert tex_math_width_units(labeled_arrow) > tex_math_width_units(r"\xrightarrow{}")


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
    raw_reference = {"t": "RawInline", "c": ["tex", r"\ref{thm:bounded}"]}
    paragraph = {
        "t": "Para",
        "c": [*_inlines("See theorem"), raw_reference],
    }

    composition = compose_accessible_pandoc_document(
        _document([_header("Formal reference"), paragraph]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/formalism.md",
    )

    assert composition.frame_count == 1
    rendered = next(block for block in composition.document["blocks"] if block.get("t") == "Para")
    assert rendered["c"][-2] == raw_reference
    assert rendered["c"][-1] == {
        "t": "RawInline",
        "c": [
            "html",
            '<span class="citation formal-reference" data-cites="thm:bounded">(<strong>thm:bounded?</strong>)</span>',
        ],
    }


@pytest.mark.parametrize(("node_type", "source_format"), [("RawBlock", "html"), ("RawInline", "openxml")])
def test_semantic_composer_rejects_authored_writer_specific_raw_content(
    node_type: str,
    source_format: str,
) -> None:
    raw = {"t": node_type, "c": [source_format, "<style>section{height:200vh}</style>"]}
    block = raw if node_type == "RawBlock" else {"t": "Para", "c": [raw]}

    with pytest.raises(RenderingError, match=r"\[slides\.density\.unsupported-raw-geometry\]") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Writer-specific raw content"), block]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/raw-content.md",
        )

    assert exc_info.value.context["unsupported_command"] == f"raw-format:{source_format}"


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
    [("aligned", 5, 6, 7, 8), ("substack", 12, 13, 7, 8)],
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
    assert exc_info.value.context["maximum_lines"] == 7


def test_semantic_composer_models_display_and_table_math_height() -> None:
    passing_math = {"t": "Math", "c": [{"t": "DisplayMath"}, _nested_fraction_source(14)]}
    passing_equation = {"t": "Para", "c": [passing_math]}
    composition = compose_accessible_pandoc_document(
        _document([_header("Fraction depth"), passing_equation]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/math.md",
    )
    assert composition.frame_count == 1

    failing_source = _nested_fraction_source(15)
    failing_equation = {"t": "Para", "c": [{"t": "Math", "c": [{"t": "DisplayMath"}, failing_source]}]}
    with pytest.raises(RenderingError, match=r"\[slides\.density\.math-height\]") as equation_error:
        compose_accessible_pandoc_document(
            _document([_header("Fraction depth"), failing_equation]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/math.md",
        )
    assert equation_error.value.context["estimated_lines"] == 8

    table = _table_values(["Expression"], [["placeholder"]])
    table["c"][4][0][3][0][1][0][4][0]["c"] = [{"t": "Math", "c": [{"t": "InlineMath"}, failing_source]}]
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table\]") as table_error:
        compose_accessible_pandoc_document(
            _document([_header("Fraction table"), table]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/math.md",
        )
    assert table_error.value.context["first_row_lines"] == 8
