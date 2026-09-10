"""Real-pandoc geometry preflight probes: prose, math, notes, and code boundaries (split from test_slides_accessibility.py)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
import pytest
from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer
from ._slides_accessibility_helpers import (
    _nested_fraction_source,
)


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

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-code-token\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context["first_offending_token"] == code
    assert not (slides / f"{source.stem}_slides.pdf").exists()
    assert not (slides / f"{source.stem}_slides.html").exists()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_pandoc_hard_line_boundary_passes_seven_and_rejects_eight(tmp_path: Path) -> None:
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
        "## Hard lines pass\n\n" + "  \n".join("x" for _ in range(7)) + "\n",
        encoding="utf-8",
    )
    failing_source.write_text(
        "## Hard lines fail\n\n" + "  \n".join("x" for _ in range(8)) + "\n",
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
    assert exc_info.value.context["estimated_lines"] == 8
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
    passing_source.write_text("## Wide prose\n\n" + " ".join(["WW"] * 63) + "\n", encoding="utf-8")
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
    wide_prose.write_text("## Wide prose\n\n" + " ".join(["WW"] * 64) + "\n", encoding="utf-8")
    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-prose\]") as prose_error:
        renderer.render_accessible_pair(wide_prose, manuscript_dir=manuscript)
    assert prose_error.value.context["estimated_lines"] == 8
    assert prose_error.value.context["maximum_lines"] == 7

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
def test_real_nested_fraction_depth_fourteen_passes_and_fifteen_fails_preflight(tmp_path: Path) -> None:
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
        "## Fraction depth pass\n\n$$" + _nested_fraction_source(14) + "$$\n",
        encoding="utf-8",
    )
    failing_source.write_text(
        "## Fraction depth fail\n\n$$" + _nested_fraction_source(15) + "$$\n",
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
    assert exc_info.value.context["estimated_lines"] == 8
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
        f"## Aligned five\n\n$${aligned(5)}$$\n\n"
        f"## Substack twelve\n\n$${substack(12)}$$\n",
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
        "aligned-six": aligned(6),
        "substack-thirteen": substack(13),
    }
    for stem, math_source in failing_cases.items():
        source = manuscript / f"{stem}.md"
        source.write_text(f"## {stem}\n\n$${math_source}$$\n", encoding="utf-8")
        with pytest.raises(RenderingError, match=r"\[slides\.density\.math-height\]") as exc_info:
            renderer.render_accessible_pair(source, manuscript_dir=manuscript)
        assert exc_info.value.context["math_source"] == math_source
        assert exc_info.value.context["estimated_lines"] == 8
        assert exc_info.value.context["maximum_lines"] == 7
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
        "| $o$ | Observation/outcome index | `outcome_ix` |\n\n"
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
    assert r"\breaktt{" not in tex
    assert r"\texttt{outcome\_ix}" in tex
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
def test_accessible_long_code_fails_before_seqsplit_or_derivative_writing(
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

    with pytest.raises(RenderingError, match=r"\[slides\.density\.indivisible-table-width\]") as exc_info:
        renderer.render_accessible_pair(source, manuscript_dir=manuscript)

    assert exc_info.value.context["diagnostic_code"] == "slides.density.indivisible-table-width"
    assert exc_info.value.context["first_offending_token"] == "a" * 64
    assert not (slides / "seqsplit-required_slides.pdf").exists()
    assert not (slides / "seqsplit-required_slides.html").exists()
