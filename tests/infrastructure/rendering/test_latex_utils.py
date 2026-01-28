import shutil
import subprocess
from pathlib import Path

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
