"""Real TeX/Poppler controls for independent anchored mathematical obligations."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

import pytest

from infrastructure.reporting.native_format_pdf_math import (
    anchored_equations_from_ast,
    inspect_anchored_pdf_math,
    parse_inline_algebra,
)


@pytest.mark.parametrize(
    ("source_expression", "expression", "codes"),
    [
        (r"x^{2}+1", r"x^{2}+1", set()),
        (r"x^{2}+1", r"x^{2}+2", {"pdf.math.content"}),
        (r"x^{2}+1", r"x2+1", {"pdf.math.script"}),
        (r"x^{2}+1", r"\textcolor{white}{x^{2}+1}", {"pdf.math.invisible"}),
        (r"x+\frac{1}{2}", r"x+\frac{1}{2}", set()),
        (r"x+\frac{1}{2}", r"x+\frac{1}{3}", {"pdf.math.content"}),
        (r"x+\frac{1}{2}", r"x+12", {"pdf.math.fraction"}),
        (r"x+\frac{1}{2}", r"x+\genfrac{}{}{0pt}{}{1}{2}", {"pdf.math.fraction_bar"}),
        (r"x+\frac{1}{2}", r"\textcolor{white}{x+\frac{1}{2}}", {"pdf.math.invisible", "pdf.math.fraction_bar"}),
    ],
)
def test_actual_native_mathematical_controls(
    tmp_path: Path, source_expression: str, expression: str, codes: set[str]
) -> None:
    paths = {name: shutil.which(name) for name in ("pandoc", "xelatex", "pdftoppm")}
    if not all(paths.values()):
        pytest.skip("real equation controls require Pandoc, XeLaTeX and Poppler")
    parser = subprocess.run(
        [str(paths["pandoc"]), "--from=markdown+tex_math_dollars", "--to=json"],
        input=("Measured expression $" + source_expression + "$ ends here.\n").encode(),
        capture_output=True,
        check=True,
        timeout=15,
    )
    equations = anchored_equations_from_ast(parser.stdout)
    source = (
        r"\documentclass{article}\usepackage{xcolor,amsmath}\begin{document}"
        r"Measured expression $" + expression + r"$ ends here.\end{document}"
    )
    (tmp_path / "fixture.tex").write_text(source)
    subprocess.run(
        [str(paths["xelatex"]), "-interaction=nonstopmode", "-halt-on-error", "fixture.tex"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
        timeout=30,
    )
    subprocess.run(
        [str(paths["pdftoppm"]), "-png", "-r", "150", str(tmp_path / "fixture.pdf"), str(tmp_path / "page")],
        capture_output=True,
        check=True,
        timeout=30,
    )
    result = inspect_anchored_pdf_math(
        (tmp_path / "fixture.pdf").read_bytes(),
        tuple(path.read_bytes() for path in sorted(tmp_path.glob("page-*.png"))),
        equations,
        deadline=time.monotonic() + 30,
    )
    assert not result["blockers"]
    assert result["status"] == ("fail" if codes else "pass")
    assert {finding["code"] for finding in result["findings"]} == codes
    if not codes:
        assert result["observations"][0]["actual"] == ("x2+1" if source_expression == r"x^{2}+1" else "x+12")
        assert len(result["observations"][0]["glyphs"]) == 4
        assert min(result["observations"][0]["ink_ranges"]) >= 32


@pytest.mark.parametrize("source", [r"\frac{12}{2}", r"\mathbf{x}", "x^{12}", "x^^2", "x_{i}^{2}"])
def test_unknown_mathematics_is_not_silently_discarded(source: str) -> None:
    with pytest.raises(ValueError):
        parse_inline_algebra(source)


def test_header_mathematics_cannot_disappear_from_accounting() -> None:
    ast = {
        "pandoc-api-version": [1, 23],
        "blocks": [{"t": "Header", "c": [1, ["", [], []], [{"t": "Math", "c": [{"t": "InlineMath"}, "x"]}]]}],
    }
    equations = anchored_equations_from_ast(json.dumps(ast).encode())
    assert len(equations) == 1
    assert equations[0].source == "x"
    assert equations[0].blockers == ("math outside independently anchorable paragraph",)
