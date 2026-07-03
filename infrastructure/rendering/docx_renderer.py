"""DOCX rendering via pandoc.

This module renders a combined-markdown manuscript to Microsoft Word DOCX
format using the pandoc engine that already powers HTML and combined-PDF
output. Pandoc is invoked as a subprocess; no Python DOCX library is
introduced.

The function returns structured render metadata on success and raises
RenderingError on failure.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

_TIMEOUT_SECONDS = 120
_ERROR_CONTEXT_LIMIT = 500


@dataclass(frozen=True)
class DocxRenderResult:
    """Outcome of a DOCX render."""

    output_path: Path
    size_bytes: int
    duration_seconds: float


def _truncate_error_context(stderr_text: str) -> str:
    """Return bounded stderr/stdout context for RenderingError messages."""
    stripped = stderr_text.strip()
    if not stripped:
        return "no stderr captured"
    return stripped[:_ERROR_CONTEXT_LIMIT]


def _process_output_text(value: bytes | str | None) -> str:
    """Normalize subprocess stdout/stderr values to text for diagnostics."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    return ""


def render_docx(
    combined_md: Path,
    output_path: Path,
    *,
    bibliography: Path | None = None,
    reference_doc: Path | None = None,
    title: str | None = None,
    author: str | None = None,
    pandoc_path: str = "pandoc",
    extra_args: list[str] | None = None,
) -> DocxRenderResult:
    """Render *combined_md* to a DOCX at *output_path*.

    Args:
        combined_md: Combined-manuscript markdown file (already preprocessed).
        output_path: Target .docx path; parent created if missing.
        bibliography: Optional `.bib` file. When given, --citeproc is enabled.
        reference_doc: Optional .docx template for styling.
        title: Book title, passed via ``--metadata title=`` (populates the
            Word document's Title core property).
        author: Author name, passed via ``--metadata author=`` (populates
            the Word document's Author core property).
        pandoc_path: pandoc binary (default "pandoc").
        extra_args: Extra args appended to the pandoc command.

    Returns:
        DocxRenderResult with the output path, byte size, and duration.

    Raises:
        RenderingError: pandoc missing, timed out, non-zero exit, or empty output.
        FileNotFoundError: input files do not exist.
    """
    if not combined_md.is_file():
        raise FileNotFoundError(f"Combined markdown not found: {combined_md}")
    if bibliography is not None and not bibliography.is_file():
        raise FileNotFoundError(f"Bibliography not found: {bibliography}")
    if reference_doc is not None and not reference_doc.is_file():
        raise FileNotFoundError(f"Reference DOCX not found: {reference_doc}")
    if shutil.which(pandoc_path) is None:
        raise RenderingError(f"pandoc binary not found: {pandoc_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [
        pandoc_path,
        "-f",
        "markdown+yaml_metadata_block",
        "-t",
        "docx",
        str(combined_md),
        "-o",
        str(output_path),
        "--standalone",
    ]
    if title is not None:
        cmd.append(f"--metadata=title:{title}")
    if author is not None:
        cmd.append(f"--metadata=author:{author}")
    if bibliography is not None:
        cmd.extend(["--citeproc", f"--bibliography={bibliography}"])
    if reference_doc is not None:
        cmd.append(f"--reference-doc={reference_doc}")
    if extra_args:
        cmd.extend(extra_args)

    logger.debug("Invoking pandoc for DOCX: %s", " ".join(cmd))
    start = time.monotonic()
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        stderr_text = _process_output_text(exc.stderr) or _process_output_text(exc.stdout) or str(exc)
        raise RenderingError(
            f"pandoc DOCX render timed out after 120s: {_truncate_error_context(stderr_text)}"
        ) from exc

    duration = time.monotonic() - start

    if result.returncode != 0:
        stderr_text = result.stderr or result.stdout or ""
        raise RenderingError(
            f"pandoc DOCX render failed (exit {result.returncode}): {_truncate_error_context(stderr_text)}"
        )
    if not output_path.exists():
        raise RenderingError(f"pandoc reported success but DOCX was not created: {output_path}")

    size = output_path.stat().st_size
    if size == 0:
        raise RenderingError(f"pandoc reported success but DOCX is empty: {output_path}")

    logger.info("  Generated DOCX: %s (%.1f KB, %.1fs)", output_path.name, size / 1024, duration)
    return DocxRenderResult(
        output_path=output_path,
        size_bytes=size,
        duration_seconds=duration,
    )


__all__ = ["DocxRenderResult", "render_docx"]
