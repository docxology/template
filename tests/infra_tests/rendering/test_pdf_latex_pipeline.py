"""Tests for the LaTeX multi-pass compilation pipeline."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from infrastructure.core.exceptions import RenderingError
from infrastructure.rendering._pdf_latex_pipeline import (
    LATEX_CMD_OPTIONS,
    _check_fatal_error,
    _normalize_latex_log,
    _remove_luamml_mathml_cache,
    _recover_invalid_pdf,
)


def test_latex_command_disables_shell_escape() -> None:
    assert "-shell-escape" not in LATEX_CMD_OPTIONS
    assert "-no-shell-escape" in LATEX_CMD_OPTIONS


def test_tagged_math_cache_is_removed_after_successful_pdf_render(tmp_path: Path) -> None:
    """LuaLaTeX's MathML cache must not leak into the reviewer snapshot."""
    cache = tmp_path / "_combined_manuscript-luamml-mathml.html"
    cache.write_text("<math xmlns='http://www.w3.org/1998/Math/MathML' />\n", encoding="utf-8")

    _remove_luamml_mathml_cache(tmp_path)

    assert not cache.exists()
    _remove_luamml_mathml_cache(tmp_path)


def test_latex_log_normalization_preserves_diagnostics_without_trailing_space(tmp_path: Path) -> None:
    log = tmp_path / "latex.log"
    log.write_text("warning with space  \n\nfinal diagnostic\t\n", encoding="utf-8")

    _normalize_latex_log(log)

    assert log.read_text(encoding="utf-8") == "warning with space\n\nfinal diagnostic\n"


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

    # A later caption warning must not hide the earlier actual TeX error.
    caption_tail = "See the caption package documentation for explanation."
    for first_error in ("! Undefined control sequence.", "./book.tex:42: Undefined control sequence."):
        log.write_text(
            "\n".join(
                ["Compiler header", first_error, r"l.42 \undefinedReleaseCommand"]
                + ["Later compiler context"] * 30
                + [caption_tail]
            ),
            encoding="utf-8",
        )
        with pytest.raises(RenderingError, match="LaTeX compilation failed after pass 4") as error:
            _check_fatal_error(result, log, tex, pdf, 4, final_pass=True)
        assert error.value.context["returncode"] == 1
        assert error.value.context["first_error"].startswith(first_error)
        assert r"l.42 \undefinedReleaseCommand" in error.value.context["first_error"]
        assert error.value.context["first_error_log_line"] == 2
        assert caption_tail in error.value.context["last_error"]
        assert first_error not in error.value.context["last_error"]

    # Merged compiler stdout/stderr may hold a backend error absent from TeX's log.
    stdout_log = tmp_path / "_latex_stdout.log"
    stdout_text = "\n".join(["earlier stdout"] * 1000 + ["λ" * 2500, "xdvipdfmx:fatal: owned backend diagnostic"])
    stdout_log.write_text(stdout_text, encoding="utf-8")
    assert result.stderr is None
    for tex_log_present in (True, False):
        if not tex_log_present:
            log.unlink()
        with pytest.raises(RenderingError, match="LaTeX compilation failed") as error:
            _check_fatal_error(result, log, tex, pdf, 4, final_pass=True)
        assert error.value.context["stdout_log_file"] == str(stdout_log)
        assert error.value.context["stdout_tail"] == "\n".join(stdout_text.splitlines()[-20:])[-2000:]
        assert "xdvipdfmx:fatal: owned backend diagnostic" in error.value.context["stdout_tail"]
        assert len(error.value.context["stdout_tail"]) <= 2000
        assert len(error.value.context["stdout_tail"].splitlines()) <= 20
    stdout_log.unlink()
    stdout_log.mkdir()
    with pytest.raises(RenderingError, match="LaTeX compilation failed") as error:
        _check_fatal_error(result, log, tex, pdf, 4, final_pass=True)
    assert error.value.context["stdout_log_file"] == str(stdout_log)
    assert "stdout_tail" not in error.value.context


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


@pytest.mark.parametrize("returncode", [-13, 141])
def test_latex_sigpipe_exit_is_tolerated_on_posix_wrappers(tmp_path: Path, returncode: int) -> None:
    """macOS and shell wrappers expose the same benign SIGPIPE differently."""
    tex = tmp_path / "book.tex"
    pdf = tmp_path / "book.pdf"
    log = tmp_path / "book.log"
    tex.write_text(r"\documentclass{article}\begin{document}OK\end{document}", encoding="utf-8")
    pdf.write_bytes(b"%PDF-1.7\nok\nstartxref\n1\n%%EOF\n")
    log.write_text("Output written on book.pdf (1 page).", encoding="utf-8")
    result: subprocess.CompletedProcess[bytes] = subprocess.CompletedProcess(args=["xelatex"], returncode=returncode)

    assert _check_fatal_error(result, log, tex, pdf, 1) is False


def test_latex_pass_nonzero_exit_with_output_continues(tmp_path: Path) -> None:
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


def _actual_latex_pass(tmp_path: Path, body: str) -> tuple[subprocess.CompletedProcess[bytes], Path, Path, Path]:
    compiler = shutil.which("xelatex")
    assert compiler is not None, "the declared LaTeX provider must be prepared"
    tex = tmp_path / "book.tex"
    tex.write_text(r"\documentclass{article}\begin{document}" + body + r"\end{document}")
    result = subprocess.run(
        [compiler, *LATEX_CMD_OPTIONS, "-output-directory", str(tmp_path), str(tex)],
        cwd=tmp_path,
        capture_output=True,
        timeout=30,
        check=False,
    )
    return result, tmp_path / "book.log", tex, tmp_path / "book.pdf"


@pytest.mark.requires_latex
@pytest.mark.timeout(45)
def test_latex_final_pass_nonzero_exit_with_output_fails(tmp_path: Path) -> None:
    """A real compiler may emit a PDF after a recoverable error and still fail."""
    result, log, tex, pdf = _actual_latex_pass(tmp_path, r"OK\undefinedReleaseCommand")
    assert result.returncode == 1, result.stdout + result.stderr
    assert pdf.read_bytes().startswith(b"%PDF-")
    diagnostic = log.read_text()
    assert "Undefined control sequence" in diagnostic and "Output written on" in diagnostic
    assert "That makes 100 errors" not in diagnostic
    assert _check_fatal_error(result, log, tex, pdf, 1) is False
    with pytest.raises(RenderingError, match="LaTeX compilation failed after pass 4") as error:
        _check_fatal_error(result, log, tex, pdf, 4, final_pass=True)
    assert "Undefined control sequence" in error.value.context["first_error"]
    assert "undefinedReleaseCommand" in error.value.context["first_error"]
    assert error.value.context["first_error_log_line"] > 0
    assert error.value.context["returncode"] == 1


@pytest.mark.requires_latex
@pytest.mark.timeout(45)
def test_latex_final_pass_actual_zero_exit_allows_output(tmp_path: Path) -> None:
    result, log, tex, pdf = _actual_latex_pass(tmp_path, "Clean compiler control")
    assert result.returncode == 0, result.stdout + result.stderr
    assert pdf.read_bytes().startswith(b"%PDF-")
    assert "Output written on" in log.read_text()
    assert _check_fatal_error(result, log, tex, pdf, 4, final_pass=True) is False


@pytest.mark.timeout(15)
@pytest.mark.parametrize("wrapped", [False, True])
def test_latex_final_pass_rejects_real_sigpipe_process_status(tmp_path: Path, wrapped: bool) -> None:
    """Original POSIX and shell-mapped termination statuses both fail final admission."""
    assert os.name == "posix", "this mandatory process control requires POSIX"
    program = "import os,signal;signal.signal(signal.SIGPIPE,signal.SIG_DFL);os.kill(os.getpid(),signal.SIGPIPE)"
    command = [sys.executable, "-I", "-c", program]
    if wrapped:
        shell = shutil.which("sh")
        assert shell is not None
        command = [shell, "-c", '"$@"; status=$?; exit "$status"', "owned-wrapper", *command]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, timeout=5, check=False)
    assert result.returncode == (141 if wrapped else -13)
    log = tmp_path / "terminated.log"
    log.write_text("No final compiler success was observed.\n")
    with pytest.raises(RenderingError, match="LaTeX compilation failed after pass 4"):
        _check_fatal_error(result, log, tmp_path / "book.tex", tmp_path / "book.pdf", 4, final_pass=True)


@pytest.mark.requires_latex
@pytest.mark.timeout(45)
@pytest.mark.parametrize("failed", [False, True])
def test_latex_recovery_requires_actual_zero_exit_with_valid_pdf(tmp_path: Path, failed: bool) -> None:
    compiler = shutil.which("xelatex")
    assert compiler is not None
    tex = tmp_path / "book.tex"
    body = r"OK\undefinedReleaseCommand" if failed else "Clean recovery control"
    tex.write_text(r"\documentclass{article}\begin{document}" + body + r"\end{document}")
    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(b"owned truncated PDF before recovery")
    command = [compiler, *LATEX_CMD_OPTIONS, "-output-directory", str(tmp_path), str(tex)]
    if failed:
        with pytest.raises(RenderingError, match="LaTeX compilation failed after pass 5"):
            _recover_invalid_pdf(tmp_path, command, pdf, tex)
    else:
        _recover_invalid_pdf(tmp_path, command, pdf, tex)
    assert pdf.read_bytes().startswith(b"%PDF-")
    assert "Output written on" in (tmp_path / "book.log").read_text()


@pytest.mark.timeout(15)
def test_latex_recovery_rejects_real_zero_exit_with_invalid_output(tmp_path: Path) -> None:
    pdf = tmp_path / "book.pdf"
    tex = tmp_path / "book.tex"
    program = "from pathlib import Path;import sys;Path(sys.argv[1]).write_bytes(b'owned truncated provider output')"
    command = [sys.executable, "-I", "-c", program, str(pdf)]
    with pytest.raises(RenderingError, match="PDF still structurally invalid after recovery pass"):
        _recover_invalid_pdf(tmp_path, command, pdf, tex)
    assert pdf.read_bytes() == b"owned truncated provider output"
