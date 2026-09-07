"""Tests for latex_utils module."""

import inspect
import io
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from pypdf import PdfReader
from pypdf import PdfWriter

from infrastructure.core.exceptions import CompilationError
from infrastructure.rendering._pdf_latex_validation import validate_pdf_structure
from infrastructure.rendering.latex_utils import (
    canonicalize_pdf_for_determinism,
    compile_latex,
    ensure_pdf_at,
    normalize_latex_sidecars,
)


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


def test_canonicalize_pdf_adds_identifier_when_source_omits_one(tmp_path, monkeypatch):
    """Valid PDFs without a trailer ID still receive deterministic metadata."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    pdf = tmp_path / "without-id.pdf"
    writer = PdfWriter()
    writer._header = b"%PDF-2.0"
    writer.add_blank_page(width=72, height=72)
    writer.write(pdf)
    assert b"/ID" not in pdf.read_bytes()

    prior_recursion_limit = sys.getrecursionlimit()
    canonicalize_pdf_for_determinism(pdf, repo_root=tmp_path)

    content = pdf.read_bytes()
    assert b"/ID [ <" in content
    assert content.startswith(b"%PDF-2.0")
    assert validate_pdf_structure(pdf)
    assert sys.getrecursionlimit() == prior_recursion_limit


def test_canonicalize_pdf_worker_failure_preserves_original_and_removes_temp(tmp_path, monkeypatch):
    """A failed isolated worker cannot replace the source or leak its temp."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    pdf = tmp_path / "failure.pdf"
    pdf.write_bytes(b"%PDF-2.0\ninvalid object graph\n%%EOF\n")
    original = pdf.read_bytes()
    prior_recursion_limit = sys.getrecursionlimit()

    with pytest.raises(CompilationError, match="worker failed"):
        canonicalize_pdf_for_determinism(pdf, repo_root=tmp_path)

    assert pdf.read_bytes() == original
    assert sys.getrecursionlimit() == prior_recursion_limit
    assert list(tmp_path.glob(".failure.pdf.*.deterministic")) == []


def test_canonicalize_pdf_temp_creation_error_is_compilation_error(tmp_path, monkeypatch):
    """Parent-side temporary-file failures remain typed and non-destructive."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    name_max = os.pathconf(tmp_path, "PC_NAME_MAX")
    pdf = tmp_path / ("x" * (name_max - len(".pdf")) + ".pdf")
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(pdf)
    original = pdf.read_bytes()

    with pytest.raises(CompilationError, match="could not replace"):
        canonicalize_pdf_for_determinism(pdf, repo_root=tmp_path)

    assert pdf.read_bytes() == original


def test_canonicalize_pdf_preserves_pdf_2_header(tmp_path, monkeypatch):
    """Canonicalization must not downgrade tagged PDF 2.0 output to PDF 1.3."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    pdf = tmp_path / "pdf-2.pdf"
    writer = PdfWriter()
    writer.pdf_header = "%PDF-2.0"
    writer.add_blank_page(width=72, height=72)
    writer.write(pdf)

    canonicalize_pdf_for_determinism(pdf, repo_root=tmp_path)

    assert pdf.read_bytes().startswith(b"%PDF-2.0\n")
    assert PdfReader(str(pdf)).pdf_header == "%PDF-2.0"


def test_canonicalize_pdf_preserves_source_file_mode(tmp_path, monkeypatch):
    """Atomic replacement retains the compiled PDF's publication permissions."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    pdf = tmp_path / "mode.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.write(pdf)
    pdf.chmod(0o644)

    canonicalize_pdf_for_determinism(pdf, repo_root=tmp_path)

    assert stat.S_IMODE(pdf.stat().st_mode) == 0o644


def _write_deep_tagged_pdf(path) -> None:
    """Create a real PDF 2.0 structure tree beyond the parent recursion limit."""
    script = r"""
import sys
from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import BooleanObject, DictionaryObject, NameObject

sys.setrecursionlimit(10_000)
target = Path(sys.argv[1])
writer = PdfWriter()
writer.pdf_header = "%PDF-2.0"
writer.add_blank_page(width=72, height=72)
child = None
for _ in range(500):
    node = DictionaryObject({NameObject("/S"): NameObject("/P")})
    if child is not None:
        node[NameObject("/K")] = child
    child = writer._add_object(node)
structure_root = DictionaryObject(
    {NameObject("/Type"): NameObject("/StructTreeRoot"), NameObject("/K"): child}
)
writer.root_object[NameObject("/StructTreeRoot")] = writer._add_object(structure_root)
writer.root_object[NameObject("/MarkInfo")] = DictionaryObject(
    {NameObject("/Marked"): BooleanObject(True)}
)
writer.write(target)
"""
    result = subprocess.run(  # noqa: S603 - fixed test fixture generator under the project interpreter
        [sys.executable, "-c", script, str(path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def _run_pdf_canonicalization_worker(source, destination) -> subprocess.CompletedProcess[str]:
    repository_root = Path(__file__).resolve().parents[3]
    return subprocess.run(  # noqa: S603 - fixed internal worker module under project interpreter
        [
            sys.executable,
            "-m",
            "infrastructure.rendering._pdf_canonicalization_worker",
            str(source),
            str(destination),
            "1700000000",
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _run_default_policy_pypdf_clone(source) -> subprocess.CompletedProcess[str]:
    script = "import sys; from pypdf import PdfWriter; PdfWriter(clone_from=sys.argv[1], keep_initial_header=True)"
    return subprocess.run(  # noqa: S603 - fixed control using the project interpreter
        [sys.executable, "-c", script, str(source)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_canonicalize_deep_tagged_pdf_worker_isolated_and_idempotent(tmp_path, monkeypatch):
    """Deep tagged trees canonicalize idempotently without changing parent policy."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    pdf = tmp_path / "deep-tagged.pdf"
    second = tmp_path / "deep-tagged-second.pdf"
    _write_deep_tagged_pdf(pdf)
    prior_recursion_limit = sys.getrecursionlimit()
    default_policy = _run_default_policy_pypdf_clone(pdf)

    canonicalize_pdf_for_determinism(pdf, repo_root=tmp_path)
    first_content = pdf.read_bytes()
    worker = _run_pdf_canonicalization_worker(pdf, second)

    assert default_policy.returncode != 0
    assert "RecursionError" in default_policy.stderr
    assert worker.returncode == 0, worker.stderr
    assert second.read_bytes() == first_content
    assert first_content.startswith(b"%PDF-2.0\n")
    assert b"/StructTreeRoot" in first_content
    assert b"/Marked true" in first_content
    assert validate_pdf_structure(pdf)
    assert sys.getrecursionlimit() == prior_recursion_limit
    assert list(tmp_path.glob(".deep-tagged.pdf.*.deterministic")) == []


def test_canonicalize_pdf_preserves_raster_image_streams(tmp_path, monkeypatch):
    """Metadata canonicalization must not rewrite XeTeX-style raster streams."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    image = Image.new("RGB", (32, 16), (20, 140, 220))
    image.putpixel((31, 15), (240, 30, 80))
    image_buffer = io.BytesIO()
    image.save(image_buffer, format="PNG")

    pdf = tmp_path / "image.pdf"
    document = canvas.Canvas(str(pdf), pagesize=(144, 72))
    document.drawImage(ImageReader(io.BytesIO(image_buffer.getvalue())), 0, 0, width=144, height=72)
    document.showPage()
    document.save()

    before = PdfReader(str(pdf)).pages[0].images[0].data
    canonicalize_pdf_for_determinism(pdf, repo_root=tmp_path)
    after = PdfReader(str(pdf)).pages[0].images[0].data

    assert after == before


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


def test_normalize_latex_sidecars_removes_only_named_text_whitespace(tmp_path):
    """Generated text sidecars normalize without touching unrelated files."""
    aux = tmp_path / "deck.aux"
    log = tmp_path / "deck.log"
    other = tmp_path / "other.aux"
    aux.write_text("\\relax  \nline\t\n", encoding="utf-8")
    log.write_text("diagnostic  \n", encoding="utf-8")
    other.write_text("leave me  \n", encoding="utf-8")

    normalize_latex_sidecars(tmp_path, "deck")

    assert aux.read_text(encoding="utf-8") == "\\relax\nline\n"
    assert log.read_text(encoding="utf-8") == "diagnostic\n"
    assert other.read_text(encoding="utf-8") == "leave me  \n"


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


@pytest.mark.requires_latex
@pytest.mark.timeout(30)
def test_compile_latex_is_byte_reproducible_with_pinned_epoch(tmp_path, skip_if_no_latex, monkeypatch):
    """Two real LaTeX runs with the same epoch produce identical PDF bytes."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    tex_file = tmp_path / "reproducible.tex"
    tex_file.write_text(
        r"""\documentclass{article}
\begin{document}
Pinned deterministic publication build.
\end{document}
""",
        encoding="utf-8",
    )

    first = compile_latex(tex_file, tmp_path / "run-one", passes=2)
    second = compile_latex(tex_file, tmp_path / "run-two", passes=2)

    assert first.read_bytes() == second.read_bytes()


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

from pypdf import PdfWriter

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
aux = out_dir / f"{tex.stem}.aux"
if attempt == 1:
    pdf.write_bytes(b"%PDF-1.4\npartial\n")
    log.write_text("xdvipdfmx:fatal: Image inclusion failed\n", encoding="utf-8")
    sys.exit(1)

writer = PdfWriter()
writer.add_blank_page(width=72, height=72)
writer.write(pdf)
log.write_text("Output written on test.pdf\n", encoding="utf-8")
aux.write_text("\\relax  \n", encoding="utf-8")
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
    assert (output_dir / "test.aux").read_text(encoding="utf-8") == "\\relax\n"


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
