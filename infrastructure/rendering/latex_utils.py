"""LaTeX compilation utilities."""

import hashlib
import re
import subprocess
import time
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from infrastructure.core.determinism import deterministic_subprocess_env, resolve_source_date_epoch
from infrastructure.core.exceptions import CompilationError
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_latex_validation import validate_pdf_structure

logger = get_logger(__name__)

_STALE_AUX_EXTENSIONS = (
    ".aux",
    ".bbl",
    ".blg",
    ".lof",
    ".lot",
    ".nav",
    ".out",
    ".snm",
    ".toc",
    ".vrb",
)
_TEXT_SIDECAR_EXTENSIONS = (*_STALE_AUX_EXTENSIONS, ".log")

_SIGPIPE_RETURNCODES = {-13, 141}

# TeX Live 2026's beamer redefines \reserved@a in a way that trips the LaTeX
# kernel parameter-number guard, emitting
#   ! Illegal parameter number in definition of \reserved@a.
# on every run. xelatex exits non-zero, yet still writes a fully valid PDF.
# This is the *only* error signature we tolerate on a non-zero exit, and only
# when the produced PDF exists and passes structural validation. Any other
# error signature, a missing PDF, or a structurally invalid PDF still fails.
_BEAMER_RESERVED_A_SIGNATURE = r"Illegal parameter number in definition of \reserved@a"
_PDF_ID_RE = re.compile(rb"/ID\s*\[\s*<([0-9A-Fa-f]{32})>\s*<([0-9A-Fa-f]{32})>\s*\]")
_FONT_SUBSET_RE = re.compile(r"^/[A-Z]{6}\+(?P<font>.+)$")
_FONT_SUBSET_BYTES_RE = re.compile(rb"[A-Z]{6}\+")


def _is_tolerable_beamer_reserved_a(
    returncode: int,
    pdf_exists: bool,
    pdf_valid: bool,
    log_content: str,
) -> bool:
    """Return whether a non-zero exit is the benign TeX Live 2026 beamer warning.

    Tolerate the failure only when ALL hold:

    * the compiler exited non-zero (otherwise there is nothing to tolerate),
    * a PDF was actually produced and is structurally valid, and
    * the log contains the exact ``\\reserved@a`` parameter-number signature.

    A missing/invalid PDF or any other error signature returns ``False`` so the
    normal :class:`CompilationError` path runs.
    """
    if returncode == 0:
        return False
    if not (pdf_exists and pdf_valid):
        return False
    return _BEAMER_RESERVED_A_SIGNATURE in log_content


def _clean_stale_aux_files(output_dir: Path, tex_stem: str) -> None:
    """Remove stale LaTeX sidecar files before a fresh compile."""
    for ext in _STALE_AUX_EXTENSIONS:
        stale_file = output_dir / f"{tex_stem}{ext}"
        if stale_file.exists():
            stale_file.unlink()
            logger.debug(f"Removed stale LaTeX sidecar: {stale_file.name}")


def normalize_latex_sidecars(output_dir: Path, tex_stem: str) -> None:
    """Remove trailing horizontal whitespace from generated LaTeX text files.

    TeX may leave spaces immediately before newlines in ``.aux`` and related
    sidecars. They are semantically redundant, but make deterministic
    publication snapshots fail repository whitespace checks. Normalize only
    the named compilation's UTF-8 text sidecars; PDFs and unrelated files are
    never touched.
    """
    for extension in _TEXT_SIDECAR_EXTENSIONS:
        sidecar = output_dir / f"{tex_stem}{extension}"
        if not sidecar.exists():
            continue
        try:
            content = sidecar.read_text(encoding="utf-8", errors="replace")
            normalized = "\n".join(line.rstrip(" \t") for line in content.splitlines())
            if content:
                normalized += "\n"
            if normalized != content:
                sidecar.write_text(normalized, encoding="utf-8")
        except OSError as exc:
            logger.debug("LaTeX sidecar normalization skipped for %s: %s", sidecar, exc)


def _canonicalize_pdf_objects(objects: Sequence[object]) -> None:
    """Remove TeX's random six-letter font-subset prefixes in-place."""
    try:
        from pypdf.generic import ArrayObject, DictionaryObject, NameObject, StreamObject
    except ImportError as exc:  # pragma: no cover - exercised in minimal installs
        raise CompilationError(
            "Deterministic PDF canonicalization requires the rendering extra (pypdf).",
            context={"dependency": "pypdf"},
        ) from exc

    def visit(value: object) -> None:
        if isinstance(value, StreamObject):
            # Never decode/re-encode raster image streams during metadata
            # canonicalization.  pypdf's get_data() path can rewrite
            # XeTeX/dvipdfmx image filters and silently corrupt wide PNGs
            # (including horizontal tiling and RGB channels) even though the
            # source PDF is structurally valid.  Font subset prefixes live in
            # font streams and content streams, not image payloads.
            if str(value.get("/Subtype", "")) == "/Image":
                return
            stream_data = value.get_data()
            canonical_data = _FONT_SUBSET_BYTES_RE.sub(b"AAAAAA+", stream_data)
            if canonical_data != stream_data:
                value.set_data(canonical_data)
            return
        if isinstance(value, DictionaryObject):
            for key, child in list(value.items()):
                if str(key) in {"/BaseFont", "/FontName"} and isinstance(child, NameObject):
                    match = _FONT_SUBSET_RE.match(str(child))
                    if match:
                        value[key] = NameObject(f"/AAAAAA+{match.group('font')}")
                else:
                    visit(child)
        elif isinstance(value, ArrayObject):
            for child in value:
                visit(child)

    for obj in objects:
        visit(obj)


def _normalize_pdf_identifier(pdf_bytes: bytes) -> bytes:
    """Replace a compiler-generated PDF ID with a content-derived stable ID."""
    match = _PDF_ID_RE.search(pdf_bytes)
    if match is None:
        raise CompilationError("Deterministic PDF canonicalization found no PDF file identifier")

    placeholder = b"/ID [ <" + (b"0" * 32) + b"> <" + (b"0" * 32) + b"> ]"
    without_id = pdf_bytes[: match.start()] + placeholder + pdf_bytes[match.end() :]
    stable_id = hashlib.sha256(without_id).hexdigest()[:32].encode("ascii")
    replacement = b"/ID [ <" + stable_id + b"> <" + stable_id + b"> ]"
    return pdf_bytes[: match.start()] + replacement + pdf_bytes[match.end() :]


def canonicalize_pdf_for_determinism(pdf_path: Path, *, repo_root: Path | None = None) -> Path:
    """Canonicalize compiler-random PDF metadata when a build epoch is pinned.

    TeX Live's current XeTeX/xdvipdfmx stack honors ``SOURCE_DATE_EPOCH`` for
    ``/CreationDate`` but still varies the PDF identifier, Creator timestamp,
    and six-letter font-subset prefixes. Rewriting those narrow fields through
    the pinned rendering dependency makes the full PDF byte-stable while
    leaving page content and layout unchanged.
    """
    epoch = resolve_source_date_epoch(repo_root=repo_root)
    if epoch is None:
        return pdf_path

    try:
        from pypdf import PdfReader, PdfWriter
        from pypdf.generic import ArrayObject, ByteStringObject
    except ImportError as exc:  # pragma: no cover - exercised in minimal installs
        raise CompilationError(
            "Deterministic PDF builds require the rendering extra (pypdf).",
            context={"dependency": "pypdf", "pdf": str(pdf_path)},
        ) from exc

    reader = PdfReader(str(pdf_path))
    writer = PdfWriter(clone_from=str(pdf_path))
    # PDF identifiers are optional.  Some valid compiler outputs omit the
    # trailer /ID, while others expose a non-hex or otherwise unmatchable ID
    # through pypdf when cloning.  Replace either form with a deterministic
    # placeholder so canonicalization can always derive and install a
    # content-based identifier instead of rejecting a valid PDF.  pypdf has no
    # public setter for trailer IDs.
    placeholder = b"\x00" * 16
    writer._ID = ArrayObject([ByteStringObject(placeholder), ByteStringObject(placeholder)])
    _canonicalize_pdf_objects(writer._objects)  # pypdf has no public tree mutator

    metadata = {
        key: str(value)
        for key, value in (reader.metadata or {}).items()
        if key in {"/Producer", "/Keywords", "/Subject", "/Title"} and value is not None
    }
    metadata["/Creator"] = "XeTeX deterministic output"
    metadata["/CreationDate"] = datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("D:%Y%m%d%H%M%SZ")
    writer.add_metadata(metadata)

    temporary_path = pdf_path.with_name(f".{pdf_path.name}.deterministic")
    try:
        with temporary_path.open("wb") as handle:
            writer.write(handle)
        temporary_path.write_bytes(_normalize_pdf_identifier(temporary_path.read_bytes()))
        temporary_path.replace(pdf_path)
    except OSError as exc:
        raise CompilationError(
            "Deterministic PDF canonicalization could not replace the compiled PDF",
            context={"pdf": str(pdf_path), "temporary": str(temporary_path)},
        ) from exc
    finally:
        temporary_path.unlink(missing_ok=True)
    return pdf_path


def _is_recoverable_compile_failure(
    result: subprocess.CompletedProcess[str],
    pdf_exists: bool,
    pdf_valid: bool,
) -> bool:
    """Return whether a failed pass is worth retrying immediately.

    XeLaTeX/xdvipdfmx can occasionally leave a truncated PDF on the first pass
    for large image-heavy Beamer decks, then produce a valid file on rerun once
    aux/navigation files settle. Only recover when there is evidence of that
    transient state; genuine syntax failures still surface normally.
    """
    if pdf_exists and not pdf_valid:
        return True
    return result.returncode in _SIGPIPE_RETURNCODES


def ensure_pdf_at(compiled: Path, target: Path) -> Path:
    """Place a compiled PDF at *target* when LaTeX wrote a different filename.

    Args:
        compiled: Path returned by ``compile_latex`` (typically ``{tex_stem}.pdf``).
        target: Caller-requested output path.

    Returns:
        *target* after any rename.
    """
    if compiled == target:
        return target
    if target.exists():
        target.unlink()
    compiled.replace(target)
    return target


def compile_latex(
    tex_file: Path | str,
    output_dir: Path | str | None = None,
    compiler: str = "xelatex",
    timeout: int = 300,
    passes: int = 2,
) -> Path:
    """Compile LaTeX file to PDF.

    Args:
        tex_file: Path to .tex file
        output_dir: Directory for output
        compiler: Compiler command (xelatex, pdflatex)
        timeout: Timeout in seconds

    Returns:
        Path to generated PDF
    """
    tex_path = Path(tex_file)
    out_dir = Path(output_dir) if output_dir is not None else tex_path.parent

    if not tex_path.exists():
        raise CompilationError("LaTeX file not found", context={"file": str(tex_file)})

    out_dir.mkdir(parents=True, exist_ok=True)
    _clean_stale_aux_files(out_dir, tex_path.stem)

    cmd = [
        compiler,
        "-interaction=nonstopmode",
        "-no-shell-escape",
        f"-output-directory={out_dir}",
        str(tex_path),
    ]

    logger.info(f"Compiling {tex_path} with {compiler}")

    try:
        start_time = time.time()

        max_passes = max(1, int(passes))
        for i in range(max_passes):
            pass_start = time.time()
            logger.debug(f"Pass {i + 1}/{max_passes}...")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tex_path.parent,  # Run in file directory for imports
                env=deterministic_subprocess_env(repo_root=tex_path.parent),
            )

            pass_duration = time.time() - pass_start
            logger.debug(f"Pass {i + 1} completed in {pass_duration:.2f}s")

            pdf_file_temp = out_dir / f"{tex_path.stem}.pdf"
            log_file = out_dir / f"{tex_path.stem}.log"
            log_content = log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() else ""
            pdf_exists = pdf_file_temp.exists()
            pdf_valid = validate_pdf_structure(pdf_file_temp) if pdf_exists else False

            if result.returncode != 0 or not pdf_exists or not pdf_valid:
                if _is_recoverable_compile_failure(result, pdf_exists, pdf_valid):
                    logger.warning(
                        "LaTeX pass %d produced an invalid/truncated PDF; retrying once before failing",
                        i + 1,
                    )
                    if pdf_exists and not pdf_valid:
                        pdf_file_temp.unlink(missing_ok=True)

                    recovery_result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=tex_path.parent,
                        env=deterministic_subprocess_env(repo_root=tex_path.parent),
                    )
                    log_content = log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() else ""
                    pdf_exists = pdf_file_temp.exists()
                    pdf_valid = validate_pdf_structure(pdf_file_temp) if pdf_exists else False

                    if recovery_result.returncode == 0 and pdf_exists and pdf_valid:
                        logger.info("LaTeX compilation recovered after retry")
                        continue

                    result = recovery_result

                # TeX Live 2026 beamer emits the \reserved@a parameter-number
                # error and exits non-zero while still producing a valid PDF.
                # Downgrade that one signature to a warning and accept the PDF;
                # everything else falls through to the failure path below.
                if _is_tolerable_beamer_reserved_a(result.returncode, pdf_exists, pdf_valid, log_content):
                    logger.warning(
                        "Tolerating TeX Live 2026 beamer \\reserved@a warning "
                        "(exit code %d) — a valid PDF was produced on pass %d",
                        result.returncode,
                        i + 1,
                    )
                    continue

                if not log_content:
                    log_content = "No log file"

                # Enhanced error analysis for better troubleshooting
                error_hints = []

                # Detect specific LaTeX error patterns
                if "*** (job aborted, no legal \\end found)" in log_content:
                    error_hints.append(
                        "Document structure error: missing \\end{document} or unmatched \\begin{}/\\end{} pairs"  # noqa: E501
                    )
                if "Undefined control sequence" in log_content:
                    error_hints.append("Undefined LaTeX command - check for typos or missing packages")
                if "File `" in log_content and "not found" in log_content:
                    error_hints.append("Missing file reference - check figure paths and bibliography files")
                if "LaTeX Error: File" in log_content and "not found" in log_content:
                    error_hints.append("Missing LaTeX package - install required packages")
                if "Missing \\begin{document}" in log_content:
                    error_hints.append("Missing \\begin{document} command - check document structure")
                if "Division by 0" in log_content and "graphics" in log_content.lower():
                    error_hints.append("Graphics error - ensure PNG files are valid and readable")
                if pdf_exists and not pdf_valid:
                    error_hints.append("PDF was written but is structurally invalid/truncated")

                # Extract the most recent error messages for context
                error_lines = []
                for line in reversed(log_content.split("\n")):
                    line = line.strip()
                    if line and ("Error" in line or "!" in line or "***" in line):
                        error_lines.append(line)
                        if len(error_lines) >= 5:  # Get last 5 error lines
                            break
                recent_errors = "\n".join(reversed(error_lines)) if error_lines else "No specific errors found in log"

                enhanced_suggestions = [
                    f"Check full log file: {log_file}",
                    "Verify LaTeX syntax in source file",
                    "Ensure all required packages are available",
                    "Check for missing figure files or incorrect paths",
                    "Verify document has proper \\begin{document} and \\end{document} structure",
                ]

                if error_hints:
                    enhanced_suggestions.extend([f"Common issue: {hint}" for hint in error_hints])

                raise CompilationError(
                    f"LaTeX compilation failed (exit code: {result.returncode})",
                    context={
                        "exit_code": result.returncode,
                        "pdf_exists": pdf_exists,
                        "pdf_structure_valid": pdf_valid,
                        "stderr": result.stderr[:300] if result.stderr else "",
                        "log_file": str(log_file),
                        "log_tail": (log_content[-800:] if len(log_content) > 800 else log_content),
                        "recent_errors": recent_errors,
                        "detected_issues": error_hints,
                    },
                    suggestions=enhanced_suggestions,
                )

        pdf_file = out_dir / f"{tex_path.stem}.pdf"
        if not pdf_file.exists():
            raise CompilationError("PDF not generated", context={"expected": str(pdf_file)})
        if not validate_pdf_structure(pdf_file):
            raise CompilationError("PDF generated but failed structural validation", context={"pdf": str(pdf_file)})

        canonicalize_pdf_for_determinism(pdf_file, repo_root=tex_path.parent)
        normalize_latex_sidecars(out_dir, tex_path.stem)
        total_duration = time.time() - start_time
        logger.info(f"LaTeX compilation completed in {total_duration:.2f}s")

        return pdf_file

    except subprocess.TimeoutExpired as e:
        raise CompilationError("Compilation timed out", context={"timeout": timeout}) from e
    except OSError as e:
        raise CompilationError(f"Execution failed: {e}", context={"command": compiler}) from e
