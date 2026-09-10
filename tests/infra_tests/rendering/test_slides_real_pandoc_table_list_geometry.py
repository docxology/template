"""Real-pandoc table, list, and definition-list geometry preflight boundaries (split from test_slides_accessibility.py)."""

from __future__ import annotations

import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer


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
    # One header unit, two longtable rule/strut units, and five list units
    # exactly consume the separate eight-unit compact-table budget. A sixth
    # list line is therefore the first fail-closed table boundary at the
    # 20-point body floor; this does not enlarge regular prose capacity.
    write_grid(height_pass, [f"item-{index}" for index in range(5)])
    write_grid(height_fail, [f"item-{index}" for index in range(6)])
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
    assert height_error.value.context["first_row_lines"] == 6


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
        "## Nested list pass\n\n- parent\n" + "".join(f"  - child {index}\n" for index in range(6)),
        encoding="utf-8",
    )
    nested_fail.write_text(
        "## Nested list fail\n\n- parent\n" + "".join(f"  - child {index}\n" for index in range(7)),
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
    assert len(words) == 7
    glyph_heights = [float(node.attrib["yMax"]) - float(node.attrib["yMin"]) for node in words]
    assert min(glyph_heights) >= 18.0

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-list\]") as height_error:
        renderer.render_accessible_pair(nested_fail, manuscript_dir=manuscript)
    assert height_error.value.context["estimated_lines"] == 8
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
    assert exc_info.value.context["estimated_lines"] == 8
    assert not (slides / "definitions-fail_slides.pdf").exists()
    assert not (slides / "definitions-fail_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_one_definition_seven_paragraphs_pass_and_eight_fail_preflight(tmp_path: Path) -> None:
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
    assert exc_info.value.context["estimated_lines"] == 8
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
    assert exc_info.value.context["estimated_lines"] == 8
    assert not (slides / "loose-list-fail_slides.pdf").exists()
    assert not (slides / "loose-list-fail_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_evidence_quote_eight_paragraphs_pass_and_nine_fail_preflight(tmp_path: Path) -> None:
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
    quote_source(passing_source, 8)
    quote_source(failing_source, 9)
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
    assert exc_info.value.context["estimated_lines"] == 8
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
def test_real_pandoc_accessible_code_stays_contiguous_across_archive_breaktt_threshold(
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
    assert r"\breaktt{" not in tex
    assert rf"\texttt{{{safe_at}}}" in tex
    serialized_at = f"{'a' * 7}{latex_literal}{'a' * 8}"
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
