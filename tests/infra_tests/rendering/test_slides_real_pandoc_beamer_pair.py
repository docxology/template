"""Real-pandoc accessible beamer pair renders: aspect ratio, contract, captions, citeproc budgets (split from test_slides_accessibility.py)."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import accessible_reveal_output_issues
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer
from ._slides_accessibility_helpers import (
    _write_png,
)


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
    assert r"height=0.8\textheight" in tex
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
