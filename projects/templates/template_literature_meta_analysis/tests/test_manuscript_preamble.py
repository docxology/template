"""Portable LaTeX contracts for the source-owned manuscript preamble."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREAMBLE_PATH = PROJECT_ROOT / "manuscript" / "preamble.md"
SECTION_BARRIER = r"\AddToHook{cmd/section/before}{\clearpage}"


def _source_preamble() -> str:
    return PREAMBLE_PATH.read_text(encoding="utf-8")


def _label_page(aux: str, label: str) -> int:
    match = re.search(rf"\\newlabel\{{{re.escape(label)}\}}\{{\{{[^}}]*\}}\{{(\d+)\}}", aux)
    assert match is not None, f"missing LaTeX label {label!r} in:\n{aux}"
    return int(match.group(1))


def test_section_float_barrier_is_kernel_only() -> None:
    """The source contract must not regress to a non-portable package."""
    preamble = _source_preamble()

    assert "placeins" not in preamble.casefold()
    assert r"\FloatBarrier" not in preamble
    assert preamble.count(SECTION_BARRIER) == 1


def test_section_float_barrier_compiles_and_flushes_queued_float(tmp_path: Path) -> None:
    """A real kernel compile must place a queued float before the next section."""
    compiler = shutil.which("pdflatex")
    if compiler is None:
        pytest.skip("pdflatex is not installed")

    source = "\n".join(
        (
            r"\documentclass{article}",
            r"\newcount\portablebarriercount",
            r"\let\portableoriginalclearpage\clearpage",
            (
                r"\renewcommand{\clearpage}{\global\advance\portablebarriercount by 1\relax"
                r"\portableoriginalclearpage}"
            ),
            SECTION_BARRIER,
            r"\begin{document}",
            r"\section{First}",
            r"First-section text.",
            r"\begin{figure}[p]",
            r"\centering\rule{1cm}{1cm}",
            r"\caption{Queued float}\label{fig:queued}",
            r"\end{figure}",
            r"\section{Second}\label{sec:second}",
            r"Second-section text.",
            r"\typeout{PORTABLE-BARRIER-COUNT=\the\portablebarriercount}",
            r"\end{document}",
            "",
        )
    )
    tex_path = tmp_path / "section-barrier.tex"
    tex_path.write_text(source, encoding="utf-8")

    result = subprocess.run(
        [compiler, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    log = (tmp_path / "section-barrier.log").read_text(encoding="utf-8", errors="replace")
    assert result.returncode == 0, result.stdout + result.stderr + log
    assert "PORTABLE-BARRIER-COUNT=2" in log

    aux = (tmp_path / "section-barrier.aux").read_text(encoding="utf-8")
    assert _label_page(aux, "fig:queued") < _label_page(aux, "sec:second")
