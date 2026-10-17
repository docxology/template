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
        package = subprocess.run(["kpsewhich", "seqsplit.sty"], capture_output=True, text=True, check=False, timeout=10)
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
        [compiler, "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape", document.name],
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


@pytest.mark.parametrize("failure", ("nested-parameter", "nested-and-undefined", "undefined-only", "missing-input"))
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
