"""Tests for latex_utils module."""
import stat

import pytest

from infrastructure.core.exceptions import CompilationError
from infrastructure.rendering.latex_utils import compile_latex


@pytest.mark.requires_latex
def test_compile_latex_success(tmp_path, skip_if_no_latex):
    """Test LaTeX compilation with real compiler."""
    # Create a valid minimal LaTeX file
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(
        r"""\documentclass{article}
\begin{document}
Test document for compilation.
\end{document}
"""
    )

    output_dir = tmp_path / "out"
    output_dir.mkdir()

    # Compile with real LaTeX
    result = compile_latex(tex_file, output_dir)

    # Verify PDF was created
    assert result == output_dir / "test.pdf"
    assert result.exists()
    assert result.stat().st_size > 0


def test_compile_latex_missing_file(tmp_path):
    """Test error handling for missing LaTeX file."""
    with pytest.raises(CompilationError, match="not found"):
        compile_latex(tmp_path / "missing.tex", tmp_path / "out")


def test_compile_latex_recovers_from_truncated_first_pdf(tmp_path):
    """A transient truncated PDF should get one immediate recovery pass."""
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(
        r"""\documentclass{article}
\begin{document}
Recovered document.
\end{document}
""",
        encoding="utf-8",
    )

    fake_compiler = tmp_path / "fake_xelatex.py"
    fake_compiler.write_text(
        r'''#!/usr/bin/env python3
import pathlib
import sys

out_dir = pathlib.Path(".")
for arg in sys.argv[1:]:
    if arg.startswith("-output-directory="):
        out_dir = pathlib.Path(arg.split("=", 1)[1])

tex = pathlib.Path(sys.argv[-1])
attempt_file = out_dir / "attempts.txt"
attempt = int(attempt_file.read_text() or "0") + 1 if attempt_file.exists() else 1
attempt_file.write_text(str(attempt))

pdf = out_dir / f"{tex.stem}.pdf"
log = out_dir / f"{tex.stem}.log"
if attempt == 1:
    pdf.write_bytes(b"%PDF-1.4\npartial\n")
    log.write_text("xdvipdfmx:fatal: Image inclusion failed\n", encoding="utf-8")
    sys.exit(1)

pdf.write_bytes(b"%PDF-1.4\nok\nstartxref\n1\n%%EOF\n")
log.write_text("Output written on test.pdf\n", encoding="utf-8")
''',
        encoding="utf-8",
    )
    fake_compiler.chmod(fake_compiler.stat().st_mode | stat.S_IXUSR)

    output_dir = tmp_path / "out"
    output_dir.mkdir()

    result = compile_latex(tex_file, output_dir, compiler=str(fake_compiler), passes=1)

    assert result == output_dir / "test.pdf"
    assert result.exists()
    assert (output_dir / "attempts.txt").read_text(encoding="utf-8") == "2"


@pytest.mark.requires_latex
def test_compile_latex_failure(tmp_path, skip_if_no_latex):
    """Test error handling for invalid LaTeX."""
    # Create truly invalid LaTeX file (missing \begin{document} and \end{document})
    # This will prevent PDF generation entirely
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(
        r"""\documentclass{article}
% Missing \begin{document} and \end{document} - truly invalid
\invalid_command_that_does_not_exist
"""
    )

    output_dir = tmp_path / "out"
    output_dir.mkdir()

    # Should raise CompilationError for truly invalid LaTeX (no PDF will be generated)
    with pytest.raises(CompilationError):
        compile_latex(tex_file, output_dir)
