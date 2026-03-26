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

# Re-exports for backwards compatibility
from infrastructure.rendering._pdf_latex_validation import (  # noqa: F401
    validate_pdf_structure,
    repair_truncated_aux,
)
from infrastructure.rendering._pdf_latex_bibliography import (  # noqa: F401
    process_bibliography,
    log_pdf_success,
)

logger = get_logger(__name__)


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
