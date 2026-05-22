"""LaTeX compilation utilities."""

import subprocess
import time
from pathlib import Path

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

_SIGPIPE_RETURNCODES = {-13, 141}


def _clean_stale_aux_files(output_dir: Path, tex_stem: str) -> None:
    """Remove stale LaTeX sidecar files before a fresh compile."""
    for ext in _STALE_AUX_EXTENSIONS:
        stale_file = output_dir / f"{tex_stem}{ext}"
        if stale_file.exists():
            stale_file.unlink()
            logger.debug(f"Removed stale LaTeX sidecar: {stale_file.name}")


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

    # IMPORTANT: -shell-escape is required for XeTeX to properly determine PNG image
    # dimensions. Without this flag, XeTeX cannot read PNG bounding box information
    # and will produce "Division by 0" errors when including graphics.
    cmd = [
        compiler,
        "-interaction=nonstopmode",
        "-shell-escape",
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
                    )
                    log_content = log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() else ""
                    pdf_exists = pdf_file_temp.exists()
                    pdf_valid = validate_pdf_structure(pdf_file_temp) if pdf_exists else False

                    if recovery_result.returncode == 0 and pdf_exists and pdf_valid:
                        logger.info("LaTeX compilation recovered after retry")
                        continue

                    result = recovery_result

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
                    error_hints.append("Graphics error - ensure PNG files are valid and -shell-escape flag is used")
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

        total_duration = time.time() - start_time
        logger.info(f"LaTeX compilation completed in {total_duration:.2f}s")

        return pdf_file

    except subprocess.TimeoutExpired as e:
        raise CompilationError("Compilation timed out", context={"timeout": timeout}) from e
    except OSError as e:
        raise CompilationError(f"Execution failed: {e}", context={"command": compiler}) from e
