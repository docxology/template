"""Real-pandoc accessible reveal/pair renders and stale-derivative cleanup (split from test_slides_accessibility.py)."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._bibliography import BibliographyConflictError
from infrastructure.rendering._slides_accessibility import accessible_reveal_output_issues
from infrastructure.rendering._web_postprocess import MATHJAX_URL
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer
from ._slides_accessibility_helpers import (
    _write_png,
)


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
    assert all(re.search(r'class="[^"]*\baccessible-multi-image-panel\b[^"]*"', tag) for tag in image_tags)
    assert all(re.search(r'class="[^"]*\baccessible-max-fit-image\b[^"]*"', tag) for tag in image_tags)
    assert all(re.search(r'style="[^"]*width:\s*45(?:\.0)?%', tag) for tag in image_tags)
    assert ".reveal section.figure-led img.accessible-max-fit-image:not(.accessible-multi-image-panel)" in rendered
    assert ".reveal section.figure-led img.accessible-max-fit-image.accessible-multi-image-panel" in rendered
    universal_rule = re.search(
        r"\.reveal section\.figure-led img\.accessible-max-fit-image \{(?P<body>[^}]*)\}",
        rendered,
    )
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
    assert "max-block-size: 560px" in rendered
    assert "height: var(--template-figure-safe-max-height) !important" in rendered
    assert "--template-figure-min-allocation-height:392px" in rendered
    assert 'alt="A dashed line with square markers rises from left to right."' in rendered
    assert 'class="figure-long-description"' in rendered
    assert 'aria-details="fig-trend-long-description"' in rendered
    assert 'class="figure-exact-values"' in rendered
    assert 'href="../figures/figure_exact_values.md#fig-values-trend"' in rendered
    assert 'class="table-scroll"' in rendered
    assert 'aria-label="Scrollable data table"' in rendered
    # The calibrated longtable debit leaves room for five complete body rows;
    # Reveal consumes the same geometry-bounded AST as Beamer.
    assert rendered.count("<tr") == 6  # one header plus the five-row excerpt
    assert not list(slides.glob(".*.pandoc*.json"))
