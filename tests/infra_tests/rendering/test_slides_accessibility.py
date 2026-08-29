"""Contracts for the opt-in accessible presentation profile.

The archive profile remains the default.  These tests exercise the semantic
Pandoc-AST boundary directly and retain real Pandoc/Beamer smoke coverage for
the two accessible presentation derivatives.
"""

from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    compose_accessible_pandoc_document,
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


def _table(rows: int) -> dict[str, Any]:
    return {
        "t": "Table",
        "c": [
            ["", [], []],
            [None, []],
            [[{"t": "AlignDefault"}, {"t": "ColWidthDefault"}]] * 2,
            [["", [], []], [[_row("key")]]],
            [[["", [], []], 0, [], [_row(str(index)) for index in range(rows)]]],
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
    first = _paragraph(" ".join(f"alpha{index}" for index in range(50)))
    second = _paragraph(" ".join(f"beta{index}" for index in range(50)))

    composition = compose_accessible_pandoc_document(
        _document([_header("Bounded evidence"), first, second]),
        policy=AccessibleSlidePolicy(),
        source="manuscript/results.md",
    )

    headers = _classed_headers(composition.document)
    assert composition.frame_count == 2
    assert [classes for _title, classes in headers] == [{"prose-slide"}, {"prose-slide"}]
    assert "continued 2" in headers[1][0]
    assert composition.document["blocks"][1] == first
    assert composition.document["blocks"][3] == second


def test_semantic_composer_fails_on_an_indivisible_dense_block() -> None:
    dense = _paragraph(" ".join(f"word{index}" for index in range(81)))

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose\].*81 words") as exc_info:
        compose_accessible_pandoc_document(
            _document([_header("Too dense"), dense]),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["diagnostic_code"] == "slides.density.indivisible-prose"
    assert exc_info.value.context["maximum_words"] == 80


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
    assert len(rendered_table["c"][4][0][3]) == 8
    assert "canonical HTML manuscript" in " ".join(_visible_text(rendered_table).split())
    assert len(table["c"][4][0][3]) == 10


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
    assert ["height", "60%"] in rendered_image["c"][0][2]


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


@pytest.mark.slow
def test_failed_accessible_composition_removes_stale_derivative(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    slides = tmp_path / "output" / "slides"
    slides.mkdir(parents=True)
    stale = slides / "dense_slides.html"
    stale.write_text("stale prior deck", encoding="utf-8")
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
        renderer.render(source, output_format="revealjs")

    assert not stale.exists()
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
                "fig:trend": {
                    "filename": "trend.png",
                    "alt_text": "A dashed line with square markers rises from left to right.",
                    "long_description": (
                        "Reading left to right, five square markers rise monotonically.\n\n"
                        "This explanatory fixture carries no scientific generalization."
                    ),
                }
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

    assert '<main id="main-content" tabindex="-1">' in rendered
    assert 'role="region" aria-label="Presentation slides"' in rendered
    assert rendered.count('role="main"') == 0
    assert rendered.count('aria-roledescription="slide"') == 3
    assert rendered.count('aria-labelledby="') >= 3
    assert 'aria-label="Presentation companion"' in rendered
    assert ">Open canonical HTML manuscript</a>" in rendered
    assert "keyboard: true" in rendered
    assert "min-height: 70vh" in rendered
    assert "height: calc(70vh - 5.5rem)" in rendered
    assert 'alt="A dashed line with square markers rises from left to right."' in rendered
    assert 'class="figure-long-description"' in rendered
    assert 'aria-details="fig-trend-long-description"' in rendered
    assert rendered.count("<tr") == 9  # one header plus the eight-row bounded excerpt
    assert not list(slides.glob(".*.pandoc*.json"))


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_accessible_beamer_render_uses_font_floors_and_untagged_boundary(tmp_path: Path) -> None:
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
    _write_png(figures / "allocation.png")
    source = manuscript / "deck.md"
    source.write_text(
        "## Evidence boundary\n\n"
        "The projected derivative states one bounded engineering result and links the canonical reader.\n\n"
        "## Figure allocation\n\n"
        "![A one-pixel renderer fixture.](../output/figures/allocation.png){#fig:allocation}\n",
        encoding="utf-8",
    )
    config = RenderingConfig(
        output_dir=str(tmp_path / "output"),
        slides_dir=str(slides),
        figures_dir=str(figures),
        slides_profile="accessible",
        latex_compiler=compiler,
    )

    result = SlidesRenderer(config).render(
        source,
        output_format="beamer",
        manuscript_dir=manuscript,
        figures_dir=figures,
    )

    assert result.is_file()
    assert result.stat().st_size > 1_000
    tex = result.with_suffix(".tex").read_text(encoding="utf-8")
    header = (slides / "_slides_math_header.tex").read_text(encoding="utf-8")
    assert "allowframebreaks" not in tex
    assert r"\setbeamerfont{frametitle}{size*={28pt}{32pt}}" in header
    assert r"\setbeamerfont{normal text}{size*={20pt}{24pt}}" in header
    assert r"\setbeamerfont{caption}{size*={16pt}{19pt}}" in header
    assert "Untagged PDF derivative" in header
    assert "HTML reader" in header
    assert r"height=0.6\textheight" in tex
    assert not list(slides.glob(".*.pandoc*.json"))
