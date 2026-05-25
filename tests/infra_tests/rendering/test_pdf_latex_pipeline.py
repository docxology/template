"""Tests for the LaTeX multi-pass compilation pipeline."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._pdf_latex_pipeline import _check_fatal_error


def test_latex_pass_nonzero_exit_fails_even_with_partial_pdf(tmp_path: Path) -> None:
    """A partial PDF from XeLaTeX must not be treated as a successful render."""
    tex = tmp_path / "book.tex"
    pdf = tmp_path / "book.pdf"
    log = tmp_path / "book.log"
    tex.write_text(r"\documentclass{article}\begin{document}", encoding="utf-8")
    pdf.write_bytes(b"%PDF-1.7\npartial\nstartxref\n1\n%%EOF\n")
    log.write_text(
        "\n".join(
            [
                "! Missing \\cr inserted.",
                "l.37938 \\end{longtable}",
                "(That makes 100 errors; please try again.)",
                "Output written on book.pdf (374 pages).",
            ]
        ),
        encoding="utf-8",
    )
    result: subprocess.CompletedProcess[bytes] = subprocess.CompletedProcess(args=["xelatex"], returncode=1)

    with pytest.raises(RenderingError, match="LaTeX compilation failed after pass 2"):
        _check_fatal_error(result, log, tex, pdf, 2)


def test_latex_pass_zero_exit_allows_output(tmp_path: Path) -> None:
    """A clean XeLaTeX pass should continue through the pipeline."""
    tex = tmp_path / "book.tex"
    pdf = tmp_path / "book.pdf"
    log = tmp_path / "book.log"
    tex.write_text(r"\documentclass{article}\begin{document}OK\end{document}", encoding="utf-8")
    pdf.write_bytes(b"%PDF-1.7\nok\nstartxref\n1\n%%EOF\n")
    log.write_text("Output written on book.pdf (1 page).", encoding="utf-8")
    result: subprocess.CompletedProcess[bytes] = subprocess.CompletedProcess(args=["xelatex"], returncode=0)

    assert _check_fatal_error(result, log, tex, pdf, 1) is False


def test_latex_pass_nonzero_exit_with_output_continues(tmp_path: Path) -> None:
    """Nonstopmode may exit non-zero while still writing a recoverable PDF."""
    tex = tmp_path / "book.tex"
    pdf = tmp_path / "book.pdf"
    log = tmp_path / "book.log"
    tex.write_text(r"\documentclass{article}\begin{document}OK\end{document}", encoding="utf-8")
    pdf.write_bytes(b"%PDF-1.7\nok\nstartxref\n1\n%%EOF\n")
    log.write_text(
        "\n".join(
            [
                "! Missing $ inserted.",
                "Output written on book.pdf (1 page).",
            ]
        ),
        encoding="utf-8",
    )
    result: subprocess.CompletedProcess[bytes] = subprocess.CompletedProcess(args=["xelatex"], returncode=1)

    assert _check_fatal_error(result, log, tex, pdf, 1) is False
