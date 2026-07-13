"""LaTeX multi-pass compilation pipeline."""

import os
import subprocess
import time
from pathlib import Path

from infrastructure.core.determinism import deterministic_subprocess_env
from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.progress import log_progress_bar
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_latex_helpers import (
    check_latex_log_for_graphics_errors,
    parse_missing_latex_package_from_log,
)
from infrastructure.rendering._pdf_latex_bibliography import (
    process_bibliography,
    log_pdf_success,
)
from infrastructure.rendering._pdf_latex_validation import (
    repair_truncated_aux,
    validate_pdf_structure,
)

logger = get_logger(__name__)

# Constants for LaTeX compilation
LATEX_CMD_OPTIONS = ["-interaction=nonstopmode", "-no-shell-escape"]
STALE_AUX_EXTENSIONS = [".aux", ".bbl", ".blg", ".toc", ".out", ".lof", ".lot"]
SIGPIPE_EXIT = 141
MAX_LATEX_PASSES = 4
MAX_CONSECUTIVE_FAILURES = 2


def _clean_stale_aux_files(output_dir: Path, tex_stem: str) -> None:
    """Remove stale auxiliary files from previous compilation runs."""
    for ext in STALE_AUX_EXTENSIONS:
        stale_file = output_dir / f"{tex_stem}{ext}"
        if stale_file.exists():
            stale_file.unlink()
            logger.debug(f"  Cleaned stale auxiliary file: {stale_file.name}")


def _run_latex_pass(
    cmd: list[str], output_dir: Path, tex_stem: str, pass_num: int, timeout: int
) -> subprocess.CompletedProcess[bytes]:
    """Execute a single LaTeX-engine pass and return the result."""
    aux_file = output_dir / f"{tex_stem}.aux"
    latex_stdout_log = output_dir / "_latex_stdout.log"

    # Pin SOURCE_DATE_EPOCH in deterministic mode so the engine stamps a stable
    # /CreationDate (byte-stable PDFs). No-op in wall-clock mode — a faithful
    # copy of os.environ. repo_root is the output_dir's owning checkout; the
    # resolver walks git from there.
    with open(latex_stdout_log, "w", encoding="utf-8") as stdout_sink:
        result = subprocess.run(
            cmd,
            check=False,
            stdout=stdout_sink,
            stderr=subprocess.STDOUT,
            cwd=str(output_dir),
            timeout=timeout,
            env=deterministic_subprocess_env(repo_root=output_dir),
        )

    repair_truncated_aux(aux_file)
    return result


def _check_fatal_error(
    result: subprocess.CompletedProcess[bytes],
    log_file: Path,
    combined_tex: Path,
    output_file: Path,
    pass_num: int,
    final_pass: bool = False,
) -> bool:
    """Check if a fatal error occurred during LaTeX compilation.

    Returns True if compilation should stop, False to continue.
    Raises RenderingError on unrecoverable failures.
    """
    log_content = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
    fatal_markers = (
        "Fatal error occurred",
        "Emergency stop",
        "That makes 100 errors",
        "TeX capacity exceeded",
    )
    has_fatal_marker = any(marker in log_content for marker in fatal_markers)
    is_fatal_exit = result.returncode not in (0, SIGPIPE_EXIT)

    if has_fatal_marker or (is_fatal_exit and (final_pass and "Output written on" not in log_content)):
        if log_file.exists():
            missing_pkg = parse_missing_latex_package_from_log(log_file)
            if missing_pkg:
                raise RenderingError(
                    f"Missing LaTeX package: {missing_pkg}",
                    context={
                        "package": missing_pkg,
                        "source": str(combined_tex),
                        "log_file": str(log_file),
                    },
                )

            log_tail = "\n".join(log_content.splitlines()[-20:])
            raise RenderingError(
                f"LaTeX compilation failed after pass {pass_num}",
                context={
                    "source": str(combined_tex),
                    "log_file": str(log_file),
                    "returncode": result.returncode,
                    "last_error": log_tail or (result.stderr[:500] if result.stderr else "No stderr"),
                },
            )
        raise RenderingError(
            f"LaTeX compilation failed (pass {pass_num})",
            context={"source": str(combined_tex), "output": str(output_file)},
        )
    if is_fatal_exit:
        logger.warning(
            "  LaTeX pass %d exited with code %s but wrote output; continuing multi-pass compile",
            pass_num,
            result.returncode,
        )
    return False


def _handle_graphics_warnings(log_file: Path, pass_num: int) -> None:
    """Log any graphics-related warnings from the LaTeX log."""
    graphics_issues = check_latex_log_for_graphics_errors(log_file)
    for error in graphics_issues.get("graphics_errors", []):
        logger.warning(f"  Graphics error: {error}")
    for missing in graphics_issues.get("missing_files", []):
        logger.warning(f"  Missing file: {missing}")
    for warning in graphics_issues.get("graphics_warnings", []):
        logger.warning(f"  Graphics warning: {warning[:100]}...")


def _recover_invalid_pdf(output_dir: Path, cmd: list[str], temp_pdf: Path, combined_tex: Path) -> None:
    """Attempt a recovery pass if the PDF is structurally invalid."""
    logger.warning("PDF structurally invalid (truncated xref/%%EOF). Re-running recovery pass...")
    latex_stdout_log = output_dir / "_latex_stdout.log"

    with open(latex_stdout_log, "w", encoding="utf-8") as stdout_sink:
        subprocess.run(
            cmd,
            check=False,
            stdout=stdout_sink,
            stderr=subprocess.STDOUT,
            cwd=str(output_dir),
            timeout=(8 if os.environ.get("PYTEST_CURRENT_TEST") else 600),
        )

    if not validate_pdf_structure(temp_pdf):
        logger.warning("PDF still invalid after recovery pass. Best-effort output.")


def compile_latex_manuscript(
    combined_tex: Path,
    combined_md: Path,
    output_dir: Path,
    output_file: Path,
    bib_files: list[Path],
    bib_exists: bool,
    source_files: list[Path],
    latex_compiler: str = "xelatex",
) -> Path:
    """Run multi-pass LaTeX compilation with bibliography processing.

    Executes up to 4 LaTeX passes, with optional bibliography processing
    between passes, and validates the output PDF structure.

    Args:
        combined_tex: Path to the combined LaTeX source file.
        combined_md: Path to the combined Markdown source (for diagnostics).
        output_dir: Directory where compilation artifacts are written.
        output_file: Target path for the final PDF output.
        bib_files: Bibliography file paths to process.
        bib_exists: Whether bibliography files exist.
        source_files: Original Markdown source files (for logging).

    Returns:
        Path to the generated PDF file.

    Raises:
        RenderingError: If compilation fails or PDF is not produced.
    """
    cmd = [latex_compiler, *LATEX_CMD_OPTIONS, combined_tex.name]
    start_time = time.time()
    tex_stem = combined_tex.stem
    latex_timeout = 8 if os.environ.get("PYTEST_CURRENT_TEST") else 600

    logger.info(f"Rendering combined manuscript to PDF: {output_file.name}")
    logger.info(f"  Source files: {len(source_files)}")
    if bib_exists and bib_files:
        bib_desc = bib_files[0].name if len(bib_files) == 1 else ", ".join(p.name for p in bib_files)
        logger.info(f"  Bibliography: {bib_desc}")
    logger.debug(f"  Output directory: {output_dir}")
    logger.debug(f"  Combined TeX file: {combined_tex.name}")
    logger.debug(f"  Combined MD file: {combined_md.name}")

    try:
        temp_pdf = output_dir / "_combined_manuscript.pdf"

        # Phase 1: Clean stale auxiliary files
        _clean_stale_aux_files(output_dir, tex_stem)

        # Phase 2: First compilation pass
        logger.info("  LaTeX compilation pass 1/4...")
        result = _run_latex_pass(cmd, output_dir, tex_stem, 1, latex_timeout)
        log_file = output_dir / "_combined_manuscript.log"

        _check_fatal_error(
            result,
            log_file,
            combined_tex,
            output_file,
            1,
        )
        final_pass_num = 1

        if result.returncode == SIGPIPE_EXIT:
            logger.debug(f"  {latex_compiler} exited with {SIGPIPE_EXIT} (SIGPIPE) — expected")

        # Phase 3: Bibliography processing
        if bib_exists:
            logger.info("  Bibliography processing...")
            try:
                process_bibliography(combined_tex, output_dir, bib_files)
            except Exception as bib_error:  # noqa: BLE001
                logger.warning(f"  Bibliography processing failed: {bib_error}")
                logger.warning("  Continuing PDF generation without bibliography processing")

        # Phase 4: Additional compilation passes (2-4)
        for run in range(1, MAX_LATEX_PASSES):
            log_progress_bar(run + 1, MAX_LATEX_PASSES, "LaTeX compilation", bar_width=20)
            result = _run_latex_pass(cmd, output_dir, tex_stem, run + 1, latex_timeout)

            _check_fatal_error(
                result,
                log_file,
                combined_tex,
                output_file,
                run + 1,
            )
            final_pass_num = run + 1

            log_content = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
            if "Rerun" not in log_content and "undefined" not in log_content.lower():
                logger.info(f"  All references resolved after pass {run + 1}")
                break

            if run == MAX_LATEX_PASSES - 1:
                _handle_graphics_warnings(log_file, run + 1)

        _check_fatal_error(
            result,
            log_file,
            combined_tex,
            output_file,
            final_pass_num,
            final_pass=True,
        )

        # Phase 5: PDF validation and recovery
        if temp_pdf.exists():
            if not validate_pdf_structure(temp_pdf):
                _recover_invalid_pdf(output_dir, cmd, temp_pdf, combined_tex)
            temp_pdf.rename(output_file)
            if output_file.exists():
                log_pdf_success(output_file, source_files, start_time)
            return output_file
        elif output_file.exists():
            log_pdf_success(output_file, source_files, start_time)
            return output_file
        else:
            raise RenderingError(
                "PDF file was not created",
                context={"source": str(combined_tex), "output": str(output_file)},
            )

    except subprocess.CalledProcessError as e:
        raise RenderingError(
            f"Failed to compile LaTeX to PDF: {e.stderr or e.stdout}",
            context={"source": str(combined_tex), "output": str(output_file)},
        ) from e
