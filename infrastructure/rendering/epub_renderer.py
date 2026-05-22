"""EPUB rendering via pandoc.

Mirror of docx_renderer for EPUB output. Pandoc supports EPUB natively;
this module is a thin, typed wrapper around the subprocess invocation.
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
class EpubRenderResult:
    """Outcome of an EPUB render."""

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


def render_epub(
    combined_md: Path,
    output_path: Path,
    *,
    bibliography: Path | None = None,
    cover_image: Path | None = None,
    pandoc_path: str = "pandoc",
    extra_args: list[str] | None = None,
) -> EpubRenderResult:
    """Render *combined_md* to an EPUB at *output_path*.

    Args:
        combined_md: Combined-manuscript markdown file.
        output_path: Target .epub path; parent created if missing.
        bibliography: Optional `.bib` file. When given, --citeproc is enabled.
        cover_image: Optional cover image path (passed via --epub-cover-image).
        pandoc_path: pandoc binary (default "pandoc").
        extra_args: Extra args appended to the pandoc command.

    Returns:
        EpubRenderResult with the output path, byte size, and duration.

    Raises:
        RenderingError: pandoc missing, timed out, non-zero exit, or empty output.
        FileNotFoundError: input files do not exist.
    """
    if not combined_md.is_file():
        raise FileNotFoundError(f"Combined markdown not found: {combined_md}")
    if bibliography is not None and not bibliography.is_file():
        raise FileNotFoundError(f"Bibliography not found: {bibliography}")
    if cover_image is not None and not cover_image.is_file():
        raise FileNotFoundError(f"Cover image not found: {cover_image}")
    if shutil.which(pandoc_path) is None:
        raise RenderingError(f"pandoc binary not found: {pandoc_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [
        pandoc_path,
        "-f",
        "markdown+yaml_metadata_block",
        "-t",
        "epub",
        str(combined_md),
        "-o",
        str(output_path),
        "--standalone",
    ]
    if bibliography is not None:
        cmd.extend(["--citeproc", f"--bibliography={bibliography}"])
    if cover_image is not None:
        cmd.append(f"--epub-cover-image={cover_image}")
    if extra_args:
        cmd.extend(extra_args)

    logger.debug("Invoking pandoc for EPUB: %s", " ".join(cmd))
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
            f"pandoc EPUB render timed out after 120s: {_truncate_error_context(stderr_text)}"
        ) from exc

    duration = time.monotonic() - start

    if result.returncode != 0:
        stderr_text = result.stderr or result.stdout or ""
        raise RenderingError(
            f"pandoc EPUB render failed (exit {result.returncode}): {_truncate_error_context(stderr_text)}"
        )
    if not output_path.exists():
        raise RenderingError(f"pandoc reported success but EPUB was not created: {output_path}")

    size = output_path.stat().st_size
    if size == 0:
        raise RenderingError(f"pandoc reported success but EPUB is empty: {output_path}")

    logger.info("  Generated EPUB: %s (%.1f KB, %.1fs)", output_path.name, size / 1024, duration)
    return EpubRenderResult(
        output_path=output_path,
        size_bytes=size,
        duration_seconds=duration,
    )


__all__ = ["EpubRenderResult", "render_epub"]
