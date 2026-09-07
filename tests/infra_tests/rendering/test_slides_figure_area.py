"""Focused regressions for accessible figure-area allocation and max-fit sizing."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from PIL import Image
import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import (
    AccessibleSlidePolicy,
    accessible_reveal_output_issues,
    compose_accessible_pandoc_document,
)
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer


def _inlines(text: str) -> list[dict[str, Any]]:
    inlines: list[dict[str, Any]] = []
    for index, word in enumerate(text.split()):
        if index:
            inlines.append({"t": "Space"})
        inlines.append({"t": "Str", "c": word})
    return inlines


def _header(text: str) -> dict[str, Any]:
    return {"t": "Header", "c": [2, ["", [], []], _inlines(text)]}


def _image(
    target: str,
    *,
    width: str | None = None,
    style: str | None = None,
) -> dict[str, Any]:
    key_values = [] if width is None else [["width", width]]
    if style is not None:
        key_values.append(["style", style])
    return {
        "t": "Image",
        "c": [["", [], key_values], _inlines("Figure alternative"), [target, ""]],
    }


def _figure(*images: dict[str, Any]) -> dict[str, Any]:
    row: list[dict[str, Any]] = []
    for index, image in enumerate(images):
        if index:
            row.append({"t": "Space"})
        row.append(image)
    return {
        "t": "Figure",
        "c": [["fig:area", [], []], [None, []], [{"t": "Plain", "c": row}]],
    }


def _document(title: str, figure: dict[str, Any]) -> dict[str, Any]:
    return {
        "pandoc-api-version": [1, 23, 1],
        "meta": {},
        "blocks": [_header(title), figure],
    }


def _first_rendered_image(document: dict[str, Any]) -> dict[str, Any]:
    def walk(value: object) -> dict[str, Any] | None:
        if isinstance(value, list):
            for item in value:
                if (found := walk(item)) is not None:
                    return found
            return None
        if not isinstance(value, dict):
            return None
        if value.get("t") == "Image":
            return value
        return walk(value.get("c"))

    image = walk(document["blocks"])
    assert image is not None
    return image


def _key_values(image: dict[str, Any]) -> dict[str, str]:
    return {str(key): str(value) for key, value in image["c"][0][2]}


def test_figure_minimum_is_carried_separately_from_max_fit_bound() -> None:
    composition = compose_accessible_pandoc_document(
        _document("Figure allocation", _figure(_image("unresolved.png"))),
        policy=AccessibleSlidePolicy(min_figure_area_percent=70),
        source="manuscript/results.md",
    )

    image = _first_rendered_image(composition.document)
    attributes = _key_values(image)

    assert "accessible-max-fit-image" in image["c"][0][1]
    assert attributes["width"] == "98%"
    assert attributes["height"] == "80%"
    assert attributes["data-slide-figure-min-allocation-percent"] == "70"
    assert attributes["data-slide-figure-max-fit-height-percent"] == "80"
    assert attributes["data-slide-figure-area-contract"] == "allocation-not-ink-coverage"
    assert attributes["data-slide-figure-intrinsic-status"] == "unresolved"
    assert "--template-figure-safe-max-height:560px" in attributes["style"]
    assert "--template-figure-min-allocation-height:392px" in attributes["style"]


def test_figure_max_fit_tracks_title_safe_body_without_turning_floor_into_cap() -> None:
    composition = compose_accessible_pandoc_document(
        _document(
            "A deliberate two line figure title for careful projection",
            _figure(_image("unresolved.png")),
        ),
        policy=AccessibleSlidePolicy(min_figure_area_percent=70),
        source="manuscript/results.md",
    )

    attributes = _key_values(_first_rendered_image(composition.document))

    assert attributes["height"] == "60%"
    assert attributes["data-slide-figure-min-allocation-percent"] == "70"
    assert attributes["data-slide-figure-max-fit-height-percent"] == "60"
    assert "--template-figure-min-allocation-height:294px" in attributes["style"]


def test_local_intrinsic_geometry_is_validated_without_treating_whitespace_as_failure(
    tmp_path: Path,
) -> None:
    manuscript = tmp_path / "manuscript"
    figures = tmp_path / "output" / "figures"
    manuscript.mkdir()
    figures.mkdir(parents=True)
    portrait = figures / "portrait.png"
    Image.new("RGB", (240, 600), "white").save(portrait)

    composition = compose_accessible_pandoc_document(
        _document("Portrait evidence", _figure(_image("../output/figures/portrait.png"))),
        policy=AccessibleSlidePolicy(),
        source=str(manuscript / "results.md"),
        authorized_image_roots=(figures,),
    )
    attributes = _key_values(_first_rendered_image(composition.document))

    assert attributes["data-slide-figure-intrinsic-status"] == "validated"
    assert attributes["data-slide-figure-intrinsic-width"] == "240"
    assert attributes["data-slide-figure-intrinsic-height"] == "600"
    assert attributes["data-slide-figure-intrinsic-aspect"] == "0.4"
    assert attributes["height"] == "80%"


def test_corrupt_resolvable_raster_fails_with_stable_figure_area_diagnostic(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    figures = tmp_path / "output" / "figures"
    manuscript.mkdir()
    figures.mkdir(parents=True)
    (figures / "corrupt.png").write_bytes(b"not a raster image")

    with pytest.raises(RenderingError, match=r"\[slides\.density\.figure-area\]") as exc_info:
        compose_accessible_pandoc_document(
            _document("Corrupt figure", _figure(_image("../output/figures/corrupt.png"))),
            policy=AccessibleSlidePolicy(),
            source=str(manuscript / "results.md"),
            authorized_image_roots=(figures,),
        )

    assert exc_info.value.context["diagnostic_code"] == "slides.density.figure-area"
    assert exc_info.value.context["figure_target"] == "../output/figures/corrupt.png"


def test_structurally_underallocated_multi_image_row_fails_as_figure_area() -> None:
    with pytest.raises(RenderingError, match=r"\[slides\.density\.figure-area\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(
                "Underallocated panels",
                _figure(_image("left.png", width="30%"), _image("right.png", width="30%")),
            ),
            policy=AccessibleSlidePolicy(min_figure_area_percent=70),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["diagnostic_code"] == "slides.density.figure-area"
    assert exc_info.value.context["authored_total_width_percent"] == 60
    assert exc_info.value.context["minimum_total_width_percent"] == 70


def test_authored_image_css_cannot_override_renderer_owned_figure_geometry() -> None:
    malicious_style = "height:200vh!important;max-height:none!important"

    with pytest.raises(RenderingError, match=r"\[slides\.density\.figure-style\]") as exc_info:
        compose_accessible_pandoc_document(
            _document(
                "Bounded figure",
                _figure(_image("figure.png", style=malicious_style)),
            ),
            policy=AccessibleSlidePolicy(),
            source="manuscript/results.md",
        )

    assert exc_info.value.context["figure_target"] == "figure.png"
    assert exc_info.value.context["authored_style"] == malicious_style


@pytest.mark.slow
def test_real_authored_image_css_fails_before_reveal_or_beamer_derivatives(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc is required")
    manuscript = tmp_path / "manuscript"
    figures = tmp_path / "output" / "figures"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    figures.mkdir(parents=True)
    Image.new("RGB", (320, 180), "white").save(figures / "override.png")
    source = manuscript / "style-override.md"
    source.write_text(
        "## Bounded figure\n\n"
        "![Figure alternative.](../output/figures/override.png)"
        '{style="height:200vh!important;max-height:none!important"}\n',
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

    with pytest.raises(RenderingError, match=r"\[slides\.density\.figure-style\]"):
        renderer.render_accessible_pair(
            source,
            manuscript_dir=manuscript,
            figures_dir=figures,
        )

    assert not (slides / "style-override_slides.html").exists()
    assert not (slides / "style-override_slides.pdf").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_beamer_and_reveal_max_fit_single_and_multi_images(tmp_path: Path) -> None:
    pandoc = shutil.which("pandoc")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if pandoc is None or compiler is None:
        pytest.skip("Pandoc and a LaTeX compiler are required")
    manuscript = tmp_path / "manuscript"
    figures = tmp_path / "output" / "figures"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    figures.mkdir(parents=True)
    for name, color in (("portrait.png", "#3b6ea8"), ("left.png", "#d97706"), ("right.png", "#0f766e")):
        Image.new("RGB", (240, 600), color).save(figures / name)
    source = manuscript / "figures.md"
    source.write_text(
        "## Portrait figure\n\n"
        "![Portrait fixture.](../output/figures/portrait.png)\n\n"
        "## Matched panels\n\n"
        "![Left panel.](../output/figures/left.png){width=45%} "
        "![Right panel.](../output/figures/right.png){width=45%}\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            figures_dir=str(figures),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_path, html_path = renderer.render_accessible_pair(
        source,
        manuscript_dir=manuscript,
        figures_dir=figures,
    )

    assert pdf_path.is_file() and pdf_path.stat().st_size > 1_000
    assert html_path.is_file() and html_path.stat().st_size > 1_000
    tex = pdf_path.with_suffix(".tex").read_text(encoding="utf-8")
    reveal = html_path.read_text(encoding="utf-8")
    assert tex.count(r"height=0.8\textheight") == 3
    assert tex.count("keepaspectratio") >= 3
    assert r"height=0.7\textheight" not in tex
    assert reveal.count("accessible-max-fit-image") >= 3
    assert reveal.count('data-slide-figure-min-allocation-percent="70"') >= 3
    assert reveal.count('data-slide-figure-max-fit-height-percent="80"') >= 3
    assert "height: var(--template-figure-safe-max-height) !important" in reveal
    assert "height: calc(70vh" not in reveal
    assert re.search(
        r'class="[^"]*accessible-max-fit-image[^"]*"[^>]*style="[^"]*width:\s*45(?:\.0)?%',
        reveal,
    )
    assert accessible_reveal_output_issues(html_path) == ()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_beamer_continuation_figure_respects_title_and_footer_safe_fit(tmp_path: Path) -> None:
    """A max-fit labeled figure must fit below a compact continuation title."""

    pandoc = shutil.which("pandoc")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if pandoc is None or compiler is None:
        pytest.skip("Pandoc and a LaTeX compiler are required")
    manuscript = tmp_path / "manuscript"
    figures = tmp_path / "output" / "figures"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    figures.mkdir(parents=True)
    Image.new("RGB", (1883, 1487), "#3b6ea8").save(figures / "efe-decomposition.png")
    source = manuscript / "continuation-figure.md"
    prelude = "\n\n---\n\n".join(f"Bounded prelude {index}." for index in range(1, 17))
    source.write_text(
        "## Expected-free-energy identity as an algebraic check\n\n"
        f"{prelude}\n\n---\n\n"
        "![Expected-free-energy decomposition.](../output/figures/efe-decomposition.png)"
        "{#fig:efe-decomp width=85%}\n",
        encoding="utf-8",
    )
    renderer = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            figures_dir=str(figures),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    )

    pdf_path, html_path = renderer.render_accessible_pair(
        source,
        manuscript_dir=manuscript,
        figures_dir=figures,
    )

    tex = pdf_path.with_suffix(".tex").read_text(encoding="utf-8")
    assert pdf_path.is_file() and pdf_path.stat().st_size > 1_000
    assert html_path.is_file() and html_path.stat().st_size > 1_000
    assert r"\begin{frame}{Expected-free-energy\ldots{} (part 17)}" in tex
    assert r"height=0.8\textheight" in tex
    assert "keepaspectratio" in tex
    assert r"\refstepcounter{figure}\label{fig:efe-decomp}" in tex
    assert 'data-slide-figure-min-allocation-percent="70"' in html_path.read_text(encoding="utf-8")
    assert accessible_reveal_output_issues(html_path) == ()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_archive_figure_sizing_remains_on_historical_path(tmp_path: Path) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc is required")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("A LaTeX compiler is required")
    manuscript = tmp_path / "manuscript"
    figures = tmp_path / "output" / "figures"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    figures.mkdir(parents=True)
    Image.new("RGB", (240, 600), "white").save(figures / "portrait.png")
    source = manuscript / "archive.md"
    source.write_text(
        "## Historical archive figure\n\n"
        "```{=latex}\n"
        "\\begin{figure}\n"
        "\\includegraphics[width=\\linewidth,height=\\textheight]"
        "{../output/figures/portrait.png}\n"
        "\\caption{Portrait.}\n"
        "\\end{figure}\n"
        "```\n",
        encoding="utf-8",
    )

    result = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(slides),
            figures_dir=str(figures),
            slides_profile="archive",
            latex_compiler=compiler,
        )
    ).render(source, output_format="beamer", manuscript_dir=manuscript, figures_dir=figures)

    tex = result.with_suffix(".tex").read_text(encoding="utf-8")
    assert r"height=0.40\textheight" in tex
    assert r"height=0.8\textheight" not in tex
    assert "data-slide-figure-min-allocation-percent" not in tex
    assert r"\caption{Portrait.}" in tex
