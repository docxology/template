"""Accessible Beamer footer and table safe-area regressions."""

from __future__ import annotations

import shutil
from pathlib import Path
import subprocess

import pdfplumber
import pytest
from reportlab.pdfgen import canvas

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._slides_accessibility import AccessibleSlidePolicy
from infrastructure.rendering._slides_accessibility_contracts import (
    ACCESSIBLE_BEAMER_FOOTER_BOTTOM_SKIP_PT,
    ACCESSIBLE_BEAMER_FOOTER_FONT_PT,
    ACCESSIBLE_BEAMER_FOOTER_LEADING_PT,
    ACCESSIBLE_BEAMER_FOOTER_RESERVED_PT,
    ACCESSIBLE_BEAMER_MIN_BOTTOM_CLEARANCE_PT,
    ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT,
    ACCESSIBLE_BEAMER_TABLE_WIDTH_LENGTH,
)
from infrastructure.rendering._slides_beamer_geometry import (
    _accessible_beamer_geometry_issues,
    reject_unsafe_accessible_beamer_geometry,
)
from infrastructure.rendering._slides_math_header import write_slides_math_header
from infrastructure.rendering._slides_tex_tables import inset_accessible_longtables
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer


def _write_geometry_fixture(
    path: Path,
    *,
    edge_word: bool = False,
    edge_rule: bool = False,
    bottom_word: bool = False,
) -> None:
    document = canvas.Canvas(str(path), pagesize=(453.543, 255.12))
    document.setFont("Helvetica", 16)
    document.drawString(0 if edge_word else 28.0, 140.0, "bounded")
    document.drawString(120.0, 0 if bottom_word else 12.0, "reader")
    document.setLineWidth(0.8)
    document.line(0 if edge_rule else 28.0, 100.0, 453.543 if edge_rule else 425.0, 100.0)
    document.save()


def test_accessible_longtable_captures_stable_body_width_without_rewriting_cell_linewidth() -> None:
    source = r"""\begin{frame}{Values}
{\def\LTcaptype{none}
\begin{longtable}[]{@{}
  p{(\linewidth - 2\tabcolsep) * \real{0.4}}
  p{(\linewidth - 2\tabcolsep) * \real{0.6}}@{}}
\toprule
\begin{minipage}[b]{\linewidth}Heading\end{minipage} & Value \\
\midrule
A & B \\
\bottomrule
\end{longtable}
}
\begin{Verbatim}
\begin{longtable} literal example \end{longtable}
\end{Verbatim}
\end{frame}
"""

    rendered, changed = inset_accessible_longtables(source)

    assert changed == 1
    assert rendered.count("% template-accessible-table-inset") == 1
    assert rf"\setlength{{{ACCESSIBLE_BEAMER_TABLE_WIDTH_LENGTH}}}{{\textwidth}}" in rendered
    assert r"\setlength{\LTleft}{\fill}" in rendered
    assert r"\setlength{\LTright}{\fill}" in rendered
    assert rendered.count(rf"{ACCESSIBLE_BEAMER_TABLE_WIDTH_LENGTH} - 2\tabcolsep") == 2
    assert r"\begin{minipage}[b]{\linewidth}" in rendered
    assert r"\begin{longtable} literal example \end{longtable}" in rendered
    assert inset_accessible_longtables(rendered) == (rendered, 0)


def test_accessible_longtable_rejects_an_unmodeled_column_preamble() -> None:
    source = r"""\begin{longtable}{ll}
\toprule
A & B \\
\bottomrule
\end{longtable}
"""

    with pytest.raises(RenderingError, match=r"\[slides\.geometry\.table-preamble\]") as exc_info:
        inset_accessible_longtables(source)

    assert exc_info.value.context == {
        "diagnostic_code": "slides.geometry.table-preamble",
        "table_index": 1,
    }


def test_accessible_header_uses_one_fixed_footer_reservation_and_table_length(tmp_path: Path) -> None:
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    accessible = write_slides_math_header(
        manuscript,
        tmp_path / "accessible",
        accessible_policy=AccessibleSlidePolicy(),
    )
    archive = write_slides_math_header(manuscript, tmp_path / "archive")

    assert accessible is not None
    accessible_text = accessible.read_text(encoding="utf-8")
    assert rf"\newlength{{{ACCESSIBLE_BEAMER_TABLE_WIDTH_LENGTH}}}" in accessible_text
    assert (
        rf"\begin{{beamercolorbox}}[wd=\paperwidth,ht={ACCESSIBLE_BEAMER_FOOTER_FONT_PT}pt,"
        rf"dp={ACCESSIBLE_BEAMER_FOOTER_LEADING_PT - ACCESSIBLE_BEAMER_FOOTER_FONT_PT}pt,center]" in accessible_text
    )
    assert rf"\vskip{ACCESSIBLE_BEAMER_FOOTER_BOTTOM_SKIP_PT}pt" in accessible_text
    assert f"Accessible footer reserved height: {ACCESSIBLE_BEAMER_FOOTER_RESERVED_PT}pt" in accessible_text

    assert archive is not None
    archive_text = archive.read_text(encoding="utf-8")
    assert ACCESSIBLE_BEAMER_TABLE_WIDTH_LENGTH not in archive_text
    assert "Accessible footer reserved height" not in archive_text


@pytest.mark.parametrize(
    ("fixture_kwargs", "expected_kind"),
    [
        ({"edge_word": True}, "glyph-side-clearance"),
        ({"edge_rule": True}, "rule-side-clearance"),
        ({"bottom_word": True}, "glyph-bottom-clearance"),
    ],
)
def test_rendered_safe_area_rejects_edge_content_and_removes_pdf(
    tmp_path: Path,
    fixture_kwargs: dict[str, bool],
    expected_kind: str,
) -> None:
    pdf = tmp_path / "unsafe.pdf"
    _write_geometry_fixture(pdf, **fixture_kwargs)

    issues = _accessible_beamer_geometry_issues(pdf)
    assert any(issue["kind"] == expected_kind for issue in issues)
    with pytest.raises(RenderingError, match=r"\[slides\.geometry\.beamer-safe-area\]") as exc_info:
        reject_unsafe_accessible_beamer_geometry(pdf)

    assert not pdf.exists()
    assert exc_info.value.context["diagnostic_code"] == "slides.geometry.beamer-safe-area"
    assert exc_info.value.context["minimum_side_clearance_pt"] == ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT
    assert exc_info.value.context["minimum_bottom_clearance_pt"] == ACCESSIBLE_BEAMER_MIN_BOTTOM_CLEARANCE_PT


def test_rendered_safe_area_accepts_inset_content(tmp_path: Path) -> None:
    pdf = tmp_path / "safe.pdf"
    _write_geometry_fixture(pdf)

    assert _accessible_beamer_geometry_issues(pdf) == ()
    reject_unsafe_accessible_beamer_geometry(pdf)
    assert pdf.is_file()


@pytest.mark.slow
@pytest.mark.requires_latex
def test_base_install_keeps_archive_available_and_accessible_geometry_fails_loud(
    tmp_path: Path,
) -> None:
    uv = shutil.which("uv")
    pandoc = shutil.which("pandoc")
    compiler = next(
        (name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)),
        None,
    )
    if uv is None or pandoc is None or compiler is None:
        pytest.skip("uv, Pandoc, and a LaTeX compiler are required")
    source = tmp_path / "manuscript" / "capability.md"
    source.parent.mkdir()
    source.write_text("## Capability boundary\n\nVisible body.\n", encoding="utf-8")
    probe = tmp_path / "probe.py"
    probe.write_text(
        """from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering.config import RenderingConfig
from infrastructure.rendering.slides_renderer import SlidesRenderer

source = Path(sys.argv[1])
root = Path(sys.argv[2])
compiler = sys.argv[3]
assert importlib.util.find_spec("pdfplumber") is None

archive_output = root / "archive"
archive = SlidesRenderer(
    RenderingConfig(
        output_dir=str(archive_output),
        slides_dir=str(archive_output / "slides"),
        slides_profile="archive",
        latex_compiler=compiler,
    )
).render(source, output_format="beamer", manuscript_dir=source.parent)
assert archive.is_file()

accessible_output = root / "accessible"
try:
    SlidesRenderer(
        RenderingConfig(
            output_dir=str(accessible_output),
            slides_dir=str(accessible_output / "slides"),
            slides_profile="accessible",
            latex_compiler=compiler,
        )
    ).render(source, output_format="beamer", manuscript_dir=source.parent)
except RenderingError as exc:
    assert exc.context["diagnostic_code"] == "slides.capability.pdf-geometry-required"
    assert exc.context["required_extra"] == "rendering"
else:
    raise AssertionError("accessible Beamer unexpectedly passed without pdfplumber")
assert not (accessible_output / "slides" / "capability_slides.pdf").exists()
print("archive-ok; accessible-failed-loud")
""",
        encoding="utf-8",
    )
    repo_root = Path(__file__).resolve().parents[3]

    completed = subprocess.run(
        [
            uv,
            "run",
            "--isolated",
            "--no-project",
            "--with",
            str(repo_root),
            "python",
            str(probe),
            str(source),
            str(tmp_path / "outputs"),
            compiler,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip().endswith("archive-ok; accessible-failed-loud")


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_accessible_beamer_keeps_footer_and_two_three_five_six_column_tables_inside_safe_area(
    tmp_path: Path,
) -> None:
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
        "## Two columns\n\n"
        "| Role | Meaning |\n|---|---|\n| A | Reference |\n\n"
        "## Three columns\n\n"
        "| Role | Mean | Unit |\n|---|---:|---|\n| B | 0.10 | nat |\n\n"
        "## Five columns\n\n"
        "| Method | Rate | Mean | Lower | Upper |\n|---|---:|---:|---:|---:|\n| C | 0.5 | 0.02 | 0.01 | 0.03 |\n\n"
        "## Six columns\n\n"
        "| Method | Raw | Adjusted | Power | Trials | Result |\n"
        "|---|---:|---:|---:|---:|---|\n"
        "| D | 0.001 | 0.004 | 0.91 | 64 | pass |\n",
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

    result = renderer.render(source, output_format="beamer", manuscript_dir=manuscript)

    assert result.is_file()
    tex = result.with_suffix(".tex").read_text(encoding="utf-8")
    log = result.with_suffix(".log").read_text(encoding="utf-8", errors="ignore")
    assert tex.count("% template-accessible-table-inset") == 4
    assert tex.count(rf"\setlength{{{ACCESSIBLE_BEAMER_TABLE_WIDTH_LENGTH}}}{{\textwidth}}") == 4
    assert "Overfull \\hbox" not in log
    assert "Overfull \\vbox" not in log

    horizontal_rules: list[tuple[float, float, float]] = []
    footer_bottoms: list[tuple[float, float]] = []
    with pdfplumber.open(result) as document:
        for page in document.pages:
            for line in page.lines:
                if abs(float(line["bottom"]) - float(line["top"])) <= 0.75 and float(line["x1"]) > float(line["x0"]):
                    horizontal_rules.append((float(line["x0"]), float(line["x1"]), float(page.width)))
            for word in page.extract_words() or ():
                if word.get("text") == "Untagged":
                    footer_bottoms.append((float(word["bottom"]), float(page.height)))

    assert len(horizontal_rules) == 12
    assert all(x0 >= ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT for x0, _x1, _width in horizontal_rules)
    assert all(x1 <= width - ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT for _x0, x1, width in horizontal_rules)
    assert len(footer_bottoms) == 4
    assert all(bottom <= height - ACCESSIBLE_BEAMER_MIN_BOTTOM_CLEARANCE_PT for bottom, height in footer_bottoms)


@pytest.mark.slow
@pytest.mark.requires_latex
def test_real_accessible_beamer_confines_two_and_three_column_continuation_tables(
    tmp_path: Path,
) -> None:
    if not shutil.which("pandoc"):
        pytest.skip("Pandoc not installed")
    compiler = next((name for name in ("xelatex", "lualatex", "pdflatex") if shutil.which(name)), None)
    if compiler is None:
        pytest.skip("No LaTeX compiler available")
    manuscript = tmp_path / "manuscript"
    slides = tmp_path / "output" / "slides"
    manuscript.mkdir()
    source = manuscript / "continuation_tables.md"
    source.write_text(
        "## Continuation-table geometry\n\n"
        "This bounded introduction occupies the labelled frame before two complete tables. "
        "Each table must therefore begin a continuation frame while retaining the full "
        "twenty-point accessible body type and the protected side clearances.\n\n"
        "| Role | Meaning |\n|---|---|\n"
        "| `alpha_role` | Reference condition |\n"
        "| `beta_role` | Comparison condition |\n\n"
        "| Metric | Mean | Unit |\n|---|---:|---|\n"
        "| Accuracy | 0.91 | proportion |\n"
        "| Log score | 0.12 | nat |\n",
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

    result = renderer.render(source, output_format="beamer", manuscript_dir=manuscript)

    assert result.is_file()
    tex = result.with_suffix(".tex").read_text(encoding="utf-8")
    assert tex.count("% template-accessible-table-inset") == 2
    assert tex.count(rf"\setlength{{{ACCESSIBLE_BEAMER_TABLE_WIDTH_LENGTH}}}{{\textwidth}}") == 2
    assert r"\begin{frame}[fragile]{Continuation-table geometry (part 2)}" in tex
    assert r"\begin{frame}{Continuation-table geometry (part 3)}" in tex

    table_pages = []
    with pdfplumber.open(result) as document:
        for page in document.pages:
            text = page.extract_text() or ""
            if "alpha_role" not in text and "Accuracy" not in text:
                continue
            table_pages.append(page)
            horizontal_rules = [
                line
                for line in page.lines
                if abs(float(line["bottom"]) - float(line["top"])) <= 0.75 and float(line["x1"]) > float(line["x0"])
            ]
            assert len(horizontal_rules) == 3
            assert all(float(line["x0"]) >= ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT for line in horizontal_rules)
            assert all(
                float(line["x1"]) <= float(page.width) - ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT
                for line in horizontal_rules
            )
            table_words = [
                word
                for word in page.extract_words() or ()
                if word.get("text") not in {"Untagged", "PDF", "derivative", "|", "HTML", "reader"}
            ]
            assert table_words
            assert min(float(word["x0"]) for word in table_words) >= ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT
            assert max(float(word["x1"]) for word in table_words) <= (
                float(page.width) - ACCESSIBLE_BEAMER_MIN_SIDE_CLEARANCE_PT
            )

    assert len(table_pages) == 2
