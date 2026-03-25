"""LaTeX multi-pass compilation pipeline."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.progress import log_progress_bar
from infrastructure.core.logging.utils import get_logger
from infrastructure.rendering._pdf_latex_helpers import (
    check_latex_log_for_graphics_errors,
    parse_missing_latex_package_from_log,
)

logger = get_logger(__name__)


def validate_pdf_structure(pdf_path: Path) -> bool:
    """Check that a PDF file has valid trailer markers.

    A structurally valid PDF must end with a cross-reference table
    (``xref`` or ``startxref``) and a ``%%EOF`` marker.  When xelatex
    is killed by SIGPIPE (exit 141), the file may be truncated before
    these markers are written, producing a file that opens partially
    or not at all in some readers.

    Args:
        pdf_path: Path to the PDF file to validate.

    Returns:
        True if the PDF has valid structure, False otherwise.
    """
    try:
        with open(pdf_path, "rb") as f:
            # Read the last 4 KB — xref + EOF are at the very end
            f.seek(0, 2)  # seek to end
            size = f.tell()
            tail_size = min(size, 4096)
            f.seek(size - tail_size)
            tail = f.read(tail_size)

        has_eof = b"%%EOF" in tail
        has_startxref = b"startxref" in tail
        if not has_eof or not has_startxref:
            logger.debug(
                f"  PDF validation: %%EOF={has_eof}, startxref={has_startxref} "
                f"in {pdf_path.name} ({size:,} bytes)"
            )
            return False
        return True
    except Exception as e:  # noqa: BLE001
        logger.debug(f"  PDF validation skipped: {e}")
        return False


def repair_truncated_aux(aux_file: Path) -> None:
    """Repair a truncated .aux file by removing the last incomplete entry."""
    if not aux_file.exists():
        return

    try:
        content = aux_file.read_text(encoding="utf-8", errors="replace")
        if not content:
            return

        lines = content.split("\n")

        # Remove trailing empty lines
        while lines and not lines[-1].strip():
            lines.pop()

        if not lines:
            return

        # Check if the last line has balanced braces
        last_line = lines[-1]
        brace_depth = last_line.count("{") - last_line.count("}")

        if brace_depth != 0:
            # Last line is incomplete — remove it
            removed = lines.pop()
            logger.info(
                f"  ✓ Repaired truncated .aux: removed incomplete entry "
                f"({len(removed)} chars, brace depth {brace_depth})"
            )

            # Also check the new last line in case multiple lines were truncated
            while lines and lines[-1].strip():
                new_last = lines[-1]
                depth = new_last.count("{") - new_last.count("}")
                if depth != 0:
                    lines.pop()
                else:
                    break

            # Write the repaired content
            _tmp = aux_file.with_suffix(aux_file.suffix + ".tmp")
            try:
                _tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
                _tmp.replace(aux_file)
            except Exception:  # noqa: BLE001
                _tmp.unlink(missing_ok=True)
                raise
    except (OSError, UnicodeDecodeError) as e:  # noqa: BLE001
        logger.debug(f"  .aux repair skipped: {e}")


def process_bibliography(tex_file: Path, output_dir: Path, bib_file: Path) -> bool:
    """Process bibliography using bibtex.

    Copies the .bib file into the compilation directory (BibTeX's paranoid mode
    restricts cross-directory access), then runs bibtex against the .aux file.
    """
    if not bib_file.exists():
        logger.warning(
            f"Bibliography file not found: {bib_file} (bibliography processing will be skipped)"
        )
        return False

    bibtex_cmd = "bibtex"
    aux_file = output_dir / f"{tex_file.stem}.aux"

    if not aux_file.exists():
        logger.warning(f"Auxiliary file not found: {aux_file}")
        return False

    try:
        local_bib = output_dir / bib_file.name
        import shutil

        shutil.copy2(str(bib_file), str(local_bib))
        logger.debug(f"Copied bibliography file to: {local_bib}")

        cmd = [bibtex_cmd, aux_file.name]
        logger.info(f"Processing bibliography with {bibtex_cmd}...")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(output_dir),
            timeout=(8 if os.environ.get("PYTEST_CURRENT_TEST") else 600),
        )

        if result.returncode != 0 and result.stderr.strip():
            logger.warning(f"Bibliography processing warning: {result.stderr[:200]}")

        logger.debug(f"✓ Bibliography processed: {bibtex_cmd} {aux_file.stem}")
        return True

    except Exception as e:  # noqa: BLE001
        logger.warning(f"Bibliography processing failed: {e}", exc_info=True)
        return False


def log_pdf_success(output_file: Path, source_files: list[Path], start_time: float) -> None:
    """Log successful PDF generation with size and duration metrics."""
    output_size_kb = output_file.stat().st_size / 1024
    logger.info(f"\nSuccessfully combined {len(source_files)} sections")
    logger.info(f"   Output: {output_file.name}")
    logger.info(f"   Size: {output_size_kb:.1f} KB ({output_size_kb / 1024:.2f} MB)")
    logger.info(f"   Location: {output_file.parent}")
    end_time = time.time()
    total_duration = end_time - start_time
    logger.info(f"   Duration: {total_duration:.2f} seconds")


def compile_latex_manuscript(
    combined_tex: Path,
    combined_md: Path,
    output_dir: Path,
    output_file: Path,
    bib_file: Path,
    bib_exists: bool,
    source_files: list[Path],
) -> Path:
    """Run multi-pass xelatex compilation with bibliography processing."""
    cmd = [
        "xelatex",
        "-interaction=nonstopmode",
        "-shell-escape",
        combined_tex.name,
    ]

    start_time = time.time()

    logger.info(f"Rendering combined manuscript to PDF: {output_file.name}")
    logger.info(f"  Source files: {len(source_files)}")
    if bib_exists:
        logger.info(f"  Bibliography: {bib_file.name}")
    logger.debug(f"  Output directory: {output_dir}")
    logger.debug(f"  Combined TeX file: {combined_tex.name}")
    logger.debug(f"  Combined MD file: {combined_md.name}")

    try:
        temp_pdf = output_dir / "_combined_manuscript.pdf"

        stale_extensions = [".aux", ".bbl", ".blg", ".toc", ".out", ".lof", ".lot"]
        tex_stem = combined_tex.stem
        for ext in stale_extensions:
            stale_file = output_dir / f"{tex_stem}{ext}"
            if stale_file.exists():
                stale_file.unlink()
                logger.debug(f"  Cleaned stale auxiliary file: {stale_file.name}")

        logger.info("  LaTeX compilation pass 1/4...")
        latex_timeout = 8 if os.environ.get("PYTEST_CURRENT_TEST") else 600
        SIGPIPE_EXIT = 141
        xelatex_stdout_log = output_dir / "_xelatex_stdout.log"
        with open(xelatex_stdout_log, "w") as stdout_sink:
            result = subprocess.run(  # type: ignore[assignment]
                cmd,
                check=False,
                stdout=stdout_sink,
                stderr=subprocess.STDOUT,
                cwd=str(output_dir),
                timeout=latex_timeout,
            )

        aux_file = output_dir / f"{tex_stem}.aux"
        repair_truncated_aux(aux_file)

        log_file = output_dir / "_combined_manuscript.log"
        log_content = log_file.read_text() if log_file.exists() else ""
        is_fatal = result.returncode > 1 and result.returncode != SIGPIPE_EXIT
        if "Fatal error occurred" in log_content or (is_fatal and not temp_pdf.exists()):
            raise RenderingError(
                "XeLaTeX compilation failed (pass 1)",
                context={"source": str(combined_tex), "output": str(output_file)},
            )
        if result.returncode == SIGPIPE_EXIT:
            logger.debug(f"  xelatex exited with {SIGPIPE_EXIT} (SIGPIPE) — expected")

        if bib_exists:
            logger.info("  Bibliography processing...")
            try:
                process_bibliography(combined_tex, output_dir, bib_file)
            except Exception as bib_error:  # noqa: BLE001
                logger.warning(f"  Bibliography processing failed: {bib_error}")
                logger.warning("  Continuing PDF generation without bibliography processing")

        max_passes = 4
        consecutive_failures = 0
        max_consecutive_failures = 2

        for run in range(1, max_passes):
            log_progress_bar(run + 1, max_passes, "LaTeX compilation", bar_width=20)
            with open(xelatex_stdout_log, "w") as stdout_sink:
                result = subprocess.run(  # type: ignore[assignment]
                    cmd,
                    check=False,
                    stdout=stdout_sink,
                    stderr=subprocess.STDOUT,
                    cwd=str(output_dir),
                    timeout=latex_timeout,
                )

            repair_truncated_aux(aux_file)

            log_content = log_file.read_text() if log_file.exists() else ""
            is_fatal = result.returncode > 1 and result.returncode != SIGPIPE_EXIT
            if "Fatal error occurred" in log_content or is_fatal:
                consecutive_failures += 1

                if output_file.exists():
                    logger.warning(f"PDF generated but with warnings (run {run + 1})")
                    consecutive_failures = 0
                    break
                else:
                    if log_file.exists():
                        log_content = log_file.read_text()
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

                        if consecutive_failures >= max_consecutive_failures:
                            raise RenderingError(
                                f"LaTeX compilation failed after {consecutive_failures} consecutive attempts",
                                context={
                                    "source": str(combined_tex),
                                    "log_file": str(log_file),
                                    "last_error": (
                                        result.stderr[:500] if result.stderr else "No stderr"
                                    ),
                                },
                            )
                    else:
                        logger.warning(f"LaTeX compilation failed (run {run + 1}), continuing...")
                        raise RenderingError(
                            f"XeLaTeX compilation failed (run {run + 1})",
                            context={"source": str(combined_tex), "output": str(output_file)},
                        )

            if log_file.exists():
                log_content = log_file.read_text()
                if "Rerun" not in log_content and "undefined" not in log_content.lower():
                    logger.info(f"  All references resolved after pass {run + 1}")
                    break

                if run == max_passes - 1:
                    graphics_issues = check_latex_log_for_graphics_errors(log_file)
                    for error in graphics_issues.get("graphics_errors", []):
                        logger.warning(f"  Graphics error: {error}")
                    for missing in graphics_issues.get("missing_files", []):
                        logger.warning(f"  Missing file: {missing}")
                    for warning in graphics_issues.get("graphics_warnings", []):
                        logger.warning(f"  Graphics warning: {warning[:100]}...")

        if temp_pdf.exists():
            if not validate_pdf_structure(temp_pdf):
                logger.warning(
                    "PDF structurally invalid (truncated xref/%%EOF). Re-running recovery pass..."
                )
                with open(xelatex_stdout_log, "w") as stdout_sink:
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
