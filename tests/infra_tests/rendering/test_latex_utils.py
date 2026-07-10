"""Tests for latex_utils module."""

import inspect
import stat

import pytest
from reportlab.pdfgen import canvas

from infrastructure.core.exceptions import CompilationError
from infrastructure.rendering._pdf_latex_validation import validate_pdf_structure
from infrastructure.rendering.latex_utils import compile_latex, ensure_pdf_at


def test_compile_latex_disables_shell_escape() -> None:
    source = inspect.getsource(compile_latex)
    assert '"-shell-escape",' not in source
    assert "-no-shell-escape" in source


def _write_valid_pdf(path) -> None:
    """Write a real, structurally valid PDF using reportlab (a dev dep)."""
    c = canvas.Canvas(str(path))
    c.drawString(72, 72, "Beamer regression fixture")
    c.showPage()
    c.save()
    assert validate_pdf_structure(path), "fixture PDF must be structurally valid"


def test_ensure_pdf_at_noop_when_paths_match(tmp_path):
    """When compiled and target paths match, return target unchanged."""
    pdf = tmp_path / "deck.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    assert ensure_pdf_at(pdf, pdf) == pdf
    assert pdf.exists()


def test_ensure_pdf_at_renames_compiled_pdf(tmp_path):
    """When LaTeX stem differs from requested output, move PDF to target."""
    compiled = tmp_path / "slides_slides.pdf"
    target = tmp_path / "slides.pdf"
    compiled.write_bytes(b"%PDF-1.4 fake\n")

    result = ensure_pdf_at(compiled, target)

    assert result == target
    assert target.exists()
    assert not compiled.exists()


def test_ensure_pdf_at_replaces_existing_target(tmp_path):
    """An existing target file is replaced atomically via Path.replace."""
    compiled = tmp_path / "a.pdf"
    target = tmp_path / "b.pdf"
    compiled.write_bytes(b"%PDF-1.4 new\n")
    target.write_bytes(b"stale\n")

    ensure_pdf_at(compiled, target)

    assert target.read_bytes().startswith(b"%PDF-1.4")


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
        r"""#!/usr/bin/env python3
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
""",
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


# --- TeX Live 2026 beamer \reserved@a tolerance -----------------------------

# Exact log line TeX Live 2026 beamer emits while still producing a valid PDF.
_RESERVED_A_LOG = (
    "[1\n\n] (./test.toc)\n"
    "! Illegal parameter number in definition of \\reserved@a.\n"
    "<to be read again> \n"
    "                   l\n"
    "l.42 \\begin{frame}\n"
    "Output written on test.pdf (3 pages).\n"
)


def _write_fake_compiler(path, *, log_text: str, write_valid_pdf: bool, exit_code: int) -> None:
    """Write a no-mocks fake xelatex that emits a log + optional valid PDF.

    The fake compiler reuses reportlab (a dev dependency) to write a real,
    structurally valid PDF so the tolerance path sees an authentic file — no
    mocking of validation or subprocess.
    """
    body = f"""#!/usr/bin/env python3
import pathlib
import sys

out_dir = pathlib.Path(".")
for arg in sys.argv[1:]:
    if arg.startswith("-output-directory="):
        out_dir = pathlib.Path(arg.split("=", 1)[1])

tex = pathlib.Path(sys.argv[-1])
pdf = out_dir / f"{{tex.stem}}.pdf"
log = out_dir / f"{{tex.stem}}.log"

log.write_text({log_text!r}, encoding="utf-8")

if {write_valid_pdf!r}:
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(pdf))
    c.drawString(72, 72, "fake beamer deck")
    c.showPage()
    c.save()

sys.exit({exit_code})
"""
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_compile_latex_tolerates_beamer_reserved_a_with_valid_pdf(tmp_path):
    """Non-zero exit + valid PDF + \\reserved@a signature => no raise, returns PDF."""
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(
        r"""\documentclass{beamer}
\begin{document}
\begin{frame}Hello\end{frame}
\end{document}
""",
        encoding="utf-8",
    )

    fake_compiler = tmp_path / "fake_xelatex.py"
    _write_fake_compiler(
        fake_compiler,
        log_text=_RESERVED_A_LOG,
        write_valid_pdf=True,
        exit_code=1,
    )

    output_dir = tmp_path / "out"
    output_dir.mkdir()

    # Single pass keeps the fixture deterministic; the tolerance branch must
    # accept the non-zero exit because the PDF is real and valid.
    result = compile_latex(tex_file, output_dir, compiler=str(fake_compiler), passes=1)

    assert result == output_dir / "test.pdf"
    assert result.exists()
    assert validate_pdf_structure(result)


def test_compile_latex_reserved_a_still_raises_when_pdf_missing(tmp_path):
    """Same signature but NO PDF produced must still raise CompilationError."""
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(
        r"""\documentclass{beamer}
\begin{document}
\begin{frame}Hello\end{frame}
\end{document}
""",
        encoding="utf-8",
    )

    fake_compiler = tmp_path / "fake_xelatex.py"
    _write_fake_compiler(
        fake_compiler,
        log_text=_RESERVED_A_LOG,
        write_valid_pdf=False,
        exit_code=1,
    )

    output_dir = tmp_path / "out"
    output_dir.mkdir()

    with pytest.raises(CompilationError):
        compile_latex(tex_file, output_dir, compiler=str(fake_compiler), passes=1)


def test_compile_latex_other_signature_still_raises_even_with_valid_pdf(tmp_path):
    """A valid PDF + non-zero exit but a DIFFERENT error signature must raise.

    Guards against the tolerance branch broadly swallowing non-zero exits.
    """
    tex_file = tmp_path / "test.tex"
    tex_file.write_text(
        r"""\documentclass{beamer}
\begin{document}
\begin{frame}Hello\end{frame}
\end{document}
""",
        encoding="utf-8",
    )

    fake_compiler = tmp_path / "fake_xelatex.py"
    _write_fake_compiler(
        fake_compiler,
        log_text="! Undefined control sequence.\nl.10 \\bogusmacro\nOutput written on test.pdf (1 page).\n",
        write_valid_pdf=True,
        exit_code=1,
    )

    output_dir = tmp_path / "out"
    output_dir.mkdir()

    with pytest.raises(CompilationError):
        compile_latex(tex_file, output_dir, compiler=str(fake_compiler), passes=1)
