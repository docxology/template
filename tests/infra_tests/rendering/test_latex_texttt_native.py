"""Real TeX proves both shared wrapping-header branches compile without tolerance."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from pypdf import PdfReader

from infrastructure.rendering.latex_texttt import make_long_texttt_breakable
from infrastructure.rendering.latex_utils import compile_latex
from infrastructure.core.exceptions import CompilationError
from infrastructure.rendering._slides_math_header import write_slides_math_header

pytestmark = [pytest.mark.requires_latex, pytest.mark.timeout(90)]


@pytest.mark.parametrize("writer", ("article", "beamer"))
@pytest.mark.parametrize("fallback", (False, True), ids=("selected-package", "missing-package-fallback"))
def test_real_wrapping_header_compiles_without_nested_parameter_errors(
    tmp_path: Path, fallback: bool, writer: str
) -> None:
    compiler = shutil.which("xelatex")
    assert compiler is not None, "prepare the declared actual XeLaTeX provider"
    if not fallback:
        package = subprocess.run(
            ["kpsewhich", "seqsplit.sty"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert package.returncode == 0 and package.stdout.strip(), "prepare the actual seqsplit package"
    token = "MeaningfulLongIdentifier0123456789"
    if writer == "article":
        source, replacements = make_long_texttt_breakable(
            r"\documentclass{article}" + "\n" + r"\begin{document}\texttt{" + token + r"}\end{document}" + "\n"
        )
        assert replacements == 1
    else:
        manuscript = tmp_path / "manuscript"
        manuscript.mkdir()
        header = write_slides_math_header(manuscript, tmp_path)
        assert header is not None
        source = (
            r"\documentclass{beamer}"
            + "\n"
            + header.read_text()
            + "\n"
            + r"\begin{document}\begin{frame}\breaktt{"
            + token
            + r"}\end{frame}\end{document}"
            + "\n"
        )
    if fallback:
        # Change only document input DATA to select a genuinely absent file.
        # No compiler, dependency implementation, or filesystem lookup is replaced.
        source = source.replace("seqsplit.sty", "template-absent-seqsplit-regression.sty")
    document = tmp_path / "wrapping.tex"
    document.write_text(source)
    result = subprocess.run(
        [
            compiler,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-no-shell-escape",
            document.name,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    log = document.with_suffix(".log").read_text(errors="replace")
    assert "Illegal parameter number" not in log
    pdf = PdfReader(document.with_suffix(".pdf"))
    assert token in "".join("".join(page.extract_text().split()) for page in pdf.pages)


@pytest.mark.parametrize(
    "failure",
    ("nested-parameter", "nested-and-undefined", "undefined-only", "missing-input"),
)
def test_nonzero_real_tex_exit_cannot_promote_even_a_valid_pdf(tmp_path: Path, failure: str) -> None:
    compiler = shutil.which("xelatex")
    assert compiler is not None, "prepare the declared actual XeLaTeX provider"
    # This genuine erroneous document recreates the old generated-header defect.
    # The compiler must refuse it even when nonstop recovery leaves a valid PDF.
    broken_header = (
        r"\IfFileExists{template-absent-seqsplit-regression.sty}{}"
        r"{\newcommand{\seqsplit}[1]{#1}}"
    )
    if failure == "undefined-only":
        broken_header = ""
    if failure == "missing-input":
        broken_header = r"\input{template-absent-fatal-input.tex}"
    body = r"Actual output."
    if failure in {"nested-and-undefined", "undefined-only"}:
        body += r"\TemplateUndefinedCommand"
    document = tmp_path / "refused.tex"
    document.write_text(
        r"\documentclass{article}" + "\n" + broken_header + "\n" + r"\begin{document}" + body + r"\end{document}" + "\n"
    )
    with pytest.raises(CompilationError) as caught:
        compile_latex(document, tmp_path / "compiled", compiler=compiler, passes=1)
    assert caught.value.context["exit_code"] != 0
    if failure != "missing-input":
        assert caught.value.context["pdf_exists"] is True
        assert caught.value.context["pdf_structure_valid"] is True
        log = (tmp_path / "compiled/refused.log").read_text(errors="replace")
        if failure == "undefined-only":
            assert "Undefined control sequence" in log
        else:
            assert "Illegal parameter number" in log


@pytest.mark.parametrize("writer", ("article", "beamer"))
def test_real_pandoc_code_wrap_preserves_literal_bodies_and_fits(tmp_path: Path, writer: str) -> None:
    """Actual highlighted tokens and plain verbatim wrap at unchanged font sizes."""
    from infrastructure.rendering._pdf_combined_preamble import inject_latex_preamble

    pandoc = shutil.which("pandoc")
    compiler = shutil.which("xelatex")
    assert pandoc is not None and compiler is not None, "prepare actual Pandoc and XeLaTeX providers"
    token = "LiteralCode0123456789" * 12
    literal = r"\example{literal} $x_1$ {braces} µ"
    markdown = (
        '## Literal code controls\n\n```yaml\ndescription: "' + token + '"\n```\n\n'
        "```\n" + token + "\n" + literal + "\n```\n\nNeighboring real math: $x_1 + 1 = 2$.\n"
    )
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "control.md"
    source.write_text(markdown)
    generated = subprocess.run(
        [
            pandoc,
            str(source),
            "--standalone",
            "--to=" + ("beamer" if writer == "beamer" else "latex"),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert generated.returncode == 0, generated.stdout + generated.stderr
    original = generated.stdout
    body = original.split(r"\begin{document}", 1)[1]
    assert r"\begin{Highlighting}" in body and r"\begin{verbatim}" in body
    if writer == "article":
        wrapped = inject_latex_preamble(original, manuscript)
    else:
        header = write_slides_math_header(manuscript, tmp_path)
        assert header is not None
        wrapped = original.replace(r"\begin{document}", header.read_text() + "\n" + r"\begin{document}", 1)
    # A preamble-only fix may not alter any character of the authored code or
    # neighboring mathematics, including TeX syntax inside literal environments.
    assert wrapped.split(r"\begin{document}", 1)[1] == original.split(r"\begin{document}", 1)[1]
    for name, content in (("unwrapped", original), ("wrapped", wrapped)):
        directory = tmp_path / name
        directory.mkdir()
        document = directory / "control.tex"
        document.write_text(content)
        result = subprocess.run(
            [
                compiler,
                "-interaction=nonstopmode",
                "-halt-on-error",
                "-no-shell-escape",
                document.name,
            ],
            cwd=directory,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        log = document.with_suffix(".log").read_text(errors="replace")
        assert "Missing character" not in log
        if name == "unwrapped":
            assert "Overfull \\hbox" in log, "control must reproduce the actual clipping defect"
        else:
            assert "Overfull \\hbox" not in log, log
            assert "Overfull \\vbox" not in log, log
            pdf = PdfReader(document.with_suffix(".pdf"))
            text = "".join("".join(page.extract_text().split()) for page in pdf.pages)
            assert text.count(token) == 2
            assert "".join(literal.split()) in text


@pytest.mark.parametrize("row_count", (17, 31))
def test_real_archive_tables_keep_every_row_counter_and_nonempty_frame(tmp_path: Path, row_count: int) -> None:
    """Whole-row AST chunks survive the real Pandoc/crossref/Beamer path."""
    import re

    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.rendering.slides_renderer import SlidesRenderer

    assert all(shutil.which(tool) for tool in ("pandoc", "pandoc-crossref", "xelatex"))
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    source = manuscript / "inventory.md"
    source.write_text(
        "## Complete inventory {#sec:inventory}\n\n"
        "| Module | Python Files | AGENTS | README | Export |\n"
        "|---|---:|---|---|---|\n"
        + "".join(f"| module{index:02d} | {index} | yes | yes | capability |\n" for index in range(row_count))
        + "\n: Complete module inventory {#tbl:inventory}\n\n"
        "## Following numbered table\n\n| Key | Value |\n|---|---|\n| FinalRowEvidence | 1 |\n\n"
        ": Following table {#tbl:following}\n\n"
        "## References\n\nSee [@tbl:inventory] and [@tbl:following].\n"
    )
    pdf = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(tmp_path / "output/slides"),
            latex_compiler="xelatex",
            slides_profile="archive",
        )
    ).render(source, output_format="beamer", manuscript_dir=manuscript)
    tex = pdf.with_suffix(".tex").read_text()
    log = pdf.with_suffix(".log").read_text(errors="replace")
    assert "Overfull \\hbox" not in log and "Overfull \\vbox" not in log, log
    assert tex.count(r"\label{tbl:inventory}") == tex.count(r"\label{tbl:following}") == 1
    pages = [page.extract_text() for page in PdfReader(pdf).pages]
    text = "".join("".join(pages).split())
    for index in range(row_count):
        assert text.count(f"module{index:02d}") == 1
    assert "Table1:Completemoduleinventory" in text
    assert "Table2:Followingtable" in text
    references = pages[-1]
    assert re.search(r"(?<![0-9])1(?![0-9])", references)
    assert re.search(r"(?<![0-9])2(?![0-9])", references)
    assert "tbl:inventory" not in references and "tbl:following" not in references and "??" not in references
    for page in pages:
        assert re.search(r"module\d{2}|FinalRowEvidence|See", page), page


@pytest.mark.parametrize("shape", ("portrait", "wide", "tiny"))
def test_real_archive_generated_image_bounds_shrink_without_upscaling(tmp_path: Path, shape: str) -> None:
    """Modern pandocbounded reserves title/caption space and keeps tiny images tiny."""
    import pdfplumber
    from PIL import Image

    from infrastructure.rendering.config import RenderingConfig
    from infrastructure.rendering.slides_renderer import SlidesRenderer

    assert all(shutil.which(tool) for tool in ("pandoc", "pandoc-crossref", "xelatex"))
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir()
    figures = tmp_path / "output/figures"
    figures.mkdir(parents=True)
    size = {"portrait": (200, 800), "wide": (800, 200), "tiny": (12, 12)}[shape]
    image = figures / "geometry.png"
    Image.new("RGB", size, "#12628c").save(image, dpi=(72, 72))
    source = manuscript / "geometry.md"
    source.write_text(
        "## UniqueImageTitle\n\n![CompleteCaptionEvidence: every authored caption word remains visible. "
        "CaptionEndEvidence.](../output/figures/geometry.png)\n\n"
        "## ExplicitImageTitle\n\n![](../output/figures/geometry.png){width=20pt}\n\n"
        "## ExplicitHeightTitle\n\n![](../output/figures/geometry.png){height=20pt}\n\n"
        "## ExplicitBothTitle\n\n![](../output/figures/geometry.png){width=20pt height=20pt}\n"
    )
    pdf = SlidesRenderer(
        RenderingConfig(
            output_dir=str(tmp_path / "output"),
            slides_dir=str(tmp_path / "output/slides"),
            figures_dir=str(figures),
            latex_compiler="xelatex",
            slides_profile="archive",
        )
    ).render(source, output_format="beamer", manuscript_dir=manuscript, figures_dir=figures)
    tex = pdf.with_suffix(".tex").read_text()
    assert r"\pandocbounded{\includegraphics" in tex
    log = pdf.with_suffix(".log").read_text(errors="replace")
    assert "Overfull \\hbox" not in log and "Overfull \\vbox" not in log, log
    with pdfplumber.open(pdf) as document:
        first, explicit, explicit_height, explicit_both = document.pages
        assert len(first.images) == len(explicit.images) == 1
        projected = first.images[0]
        title = first.search("UniqueImageTitle")[0]
        caption = first.search("CompleteCaptionEvidence")[0]
        assert title["bottom"] < projected["top"]
        assert projected["bottom"] < caption["top"]
        assert "CaptionEndEvidence" in first.extract_text()
        assert 4 < projected["x0"] < projected["x1"] < first.width - 4
        assert 4 < projected["top"] < projected["bottom"] < first.height - 4
        assert explicit.images[0]["width"] == pytest.approx(20, abs=0.1)
        assert explicit_height.images[0]["height"] == pytest.approx(20, abs=0.1)
        assert explicit_both.images[0]["width"] == pytest.approx(20, abs=0.1)
        assert explicit_both.images[0]["height"] == pytest.approx(20, abs=0.1)
        if shape == "tiny":
            assert projected["width"] == pytest.approx(12, abs=0.1)
            assert projected["height"] == pytest.approx(12, abs=0.1)


@pytest.mark.parametrize("shape", ("rowspan", "footer", "nested"))
def test_real_archive_table_paginator_leaves_unrecognized_shapes_intact(tmp_path: Path, shape: str) -> None:
    """Real Pandoc AST inputs prove the flat-table gate abstains conservatively."""
    import copy
    import json

    pandoc = shutil.which("pandoc")
    assert pandoc is not None
    markdown = "## Boundary\n\n| Key | Value |\n|---|---|\n" + "".join(
        f"| BoundRow{index:02d} | {index} |\n" for index in range(17)
    )
    parsed = subprocess.run(
        [pandoc, "--from=markdown", "--to=json"],
        input=markdown,
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert parsed.returncode == 0, parsed.stderr
    ast = json.loads(parsed.stdout)
    table = next(block for block in ast["blocks"] if block["t"] == "Table")
    rows = table["c"][4][0][3]
    if shape == "rowspan":
        rows[0][1][1][2] = 2
        rows[1][1].pop(1)
    elif shape == "footer":
        footer = copy.deepcopy(rows[0])
        footer[1][0][4] = [{"t": "Plain", "c": [{"t": "Str", "c": "FooterBoundaryEvidence"}]}]
        table["c"][5][1].append(footer)
    else:
        ast["blocks"] = [ast["blocks"][0], {"t": "BlockQuote", "c": [table]}]
    from infrastructure.rendering import _slides_beamer

    lua = Path(_slides_beamer.__file__).with_name("_beamer_allowframebreaks.lua")
    result = subprocess.run(
        [pandoc, "--from=json", "--to=beamer", "--lua-filter", str(lua)],
        input=json.dumps(ast),
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.count(r"\begin{longtable}") == 1
    assert r"\framebreak" not in result.stdout
    for index in range(17):
        assert result.stdout.count(f"BoundRow{index:02d}") == 1
