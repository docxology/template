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
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    _estimated_visible_characters,
    accessible_reveal_output_issues,
    compose_accessible_pandoc_document,
    enhance_accessible_reveal,
)
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


def _citation(identifier: str) -> dict[str, Any]:
    return {
        "t": "Cite",
        "c": [
            [
                {
                    "citationId": identifier,
                    "citationPrefix": [],
                    "citationSuffix": [],
                    "citationMode": {"t": "NormalCitation"},
                    "citationNoteNum": 0,
                    "citationHash": 0,
                }
            ],
            [{"t": "Str", "c": f"[@{identifier}]"}],
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
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}]] * 2,
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

    assert _estimated_visible_characters(section_reference) > 2 * _estimated_visible_characters(bibliography)


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
    # geometry retains four compact rows after the header, table rules, and
    # contextual canonical-reader link are accounted for at 20 points.
    assert len(rendered_table["c"][4][0][3]) == 4
    assert len(rendered_table["c"][4][0][3]) <= AccessibleSlidePolicy().max_table_rows
    assert "canonical HTML manuscript" in " ".join(_visible_text(rendered_table).split())
    assert len(table["c"][4][0][3]) == 10
    assert all(colspec[1]["t"] == "ColWidth" for colspec in rendered_table["c"][2])
    assert all(colspec[1]["t"] == "ColWidthDefault" for colspec in table["c"][2])


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
    assert len(rendered["c"][4][0][3]) == 2


def test_table_excerpt_uses_contextual_reader_fallback_when_no_whole_row_fits() -> None:
    table = _table_values(
        [
            "Method",
            "Contamination rate",
            "Rank-biserial-derived d-equivalent",
            "Interpretive label",
            "Raw p value",
            "Adjusted q value",
            "Reject null",
        ],
        [["RKL", "0.5", "saturated", "large", "1e-8", "2e-8", "yes"]],
    )

    composition = compose_accessible_pandoc_document(
        _document([_header("Paired contrasts"), table]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    assert composition.excerpted_table_count == 1
    assert not any(block["t"] == "Table" for block in composition.document["blocks"])
    fallback = next(block for block in composition.document["blocks"] if block["t"] == "Div")
    assert "table-reader-fallback" in fallback["c"][0][1]
    assert ["data-diagnostic-code", "slides.density.table-reader-fallback"] in fallback["c"][0][2]
    assert ["data-columns", "7"] in fallback["c"][0][2]
    assert ["data-body-rows", "1"] in fallback["c"][0][2]
    assert ["data-available-lines", "8"] in fallback["c"][0][2]
    visible = " ".join(_visible_text(fallback).split())
    assert "20-point frame geometry" in visible
    assert "canonical HTML manuscript" in visible


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
    assert "caption, long description, and exact values" in " ".join(_visible_text(composition.document).split())
    rendered_figure = next(block for block in composition.document["blocks"] if block["t"] == "Figure")
    rendered_image = rendered_figure["c"][2][0]["c"][0]
    assert ["height", "55%"] in rendered_image["c"][0][2]


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
    composition = compose_accessible_pandoc_document(
        _document(
            [
                _header("A deliberately long evidence heading that wraps across multiple projection lines"),
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
    continuation_header = next(block for block in composition.document["blocks"] if block["t"] == "Header")["c"]
    assert continuation_header[2]
    rendered_figure = next(block for block in composition.document["blocks"] if block["t"] == "Figure")
    rendered_image = rendered_figure["c"][2][0]["c"][0]
    assert ["height", "41%"] in rendered_image["c"][0][2]


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
    assert accessible_reveal_output_issues(output) == ()


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
    assert 'aria-label="Scrollable table: Open the canonical HTML manuscript' in rendered
    assert rendered.count("<tr") == 5  # one header plus the four-row geometry-bounded excerpt
    assert not list(slides.glob(".*.pandoc*.json"))


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
        "## Evidence boundary\n\n"
        "The projected derivative states one bounded engineering result and links the canonical reader.\n\n"
        "## Figure allocation\n\n"
        "![A one-pixel renderer fixture.](../output/figures/allocation.png){#fig:allocation}\n\n"
        "## Numbering parity\n\n"
        "The local display is Equation [@eq:model].\n\n"
        "$$x = 1$$ {#eq:model}\n",
        encoding="utf-8",
    )
    (pdf_dir / "_combined_manuscript.aux").write_text(
        r"\newlabel{eq:model}{{7}{9}{Model}{equation.7}{}}" + "\n",
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
    assert r"height=0.55\textheight" in tex
    # Pandoc-crossref chooses format-specific prose (``eq. 7`` in TeX and
    # ``(7)`` in the browser), but both canonical derivatives must consume the
    # combined AUX's exact number rather than locally renumbering it as 1.
    assert "The local display is Equation eq.~7." in tex
    assert r"\ref{eq:model}" not in tex
    visible_reveal = " ".join(re.sub(r"<[^>]+>", "", reveal).split())
    assert "The local display is Equation (7)." in visible_reveal
    assert "Equation Equation" not in visible_reveal
    assert not list(slides.glob(".*.pandoc*.json"))


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
