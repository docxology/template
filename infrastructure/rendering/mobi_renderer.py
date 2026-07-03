"""MOBI rendering via pandoc (EPUB intermediate) + calibre ebook-convert.

kindlegen is deprecated; this module uses calibre's ``ebook-convert`` CLI to
produce MOBI output.  The pipeline is:

    combined.md  →  (pandoc)  →  intermediate.epub  →  (ebook-convert)  →  output.mobi

The function returns structured render metadata on success and raises
RenderingError on failure.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from infrastructure.core.exceptions import RenderingError
from infrastructure.core.logging.utils import get_logger

logger = get_logger(__name__)

_TIMEOUT_SECONDS = 180  # calibre conversion can be slower than pure pandoc
_ERROR_CONTEXT_LIMIT = 500


@dataclass(frozen=True)
class MobiRenderResult:
    """Outcome of a MOBI render."""

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


def render_mobi(
    combined_md: Path,
    output_path: Path,
    *,
    bibliography: Path | None = None,
    cover_image: Path | None = None,
    title: str | None = None,
    author: str | None = None,
    language: str = "en",
    pandoc_path: str = "pandoc",
    calibre_path: str = "ebook-convert",
    extra_args: list[str] | None = None,
    pandoc_extra_args: list[str] | None = None,
) -> MobiRenderResult:
    """Render *combined_md* to a MOBI at *output_path*.

    The two-step pipeline first produces a temporary EPUB via pandoc and then
    converts it to MOBI via calibre's ``ebook-convert`` CLI.

    Args:
        combined_md: Combined-manuscript markdown file (already preprocessed).
        output_path: Target .mobi path; parent created if missing.
        bibliography: Optional `.bib` file. When given, --citeproc is enabled.
        cover_image: Optional cover image path (passed via --epub-cover-image
            and then forwarded to ebook-convert).
        title: Book title for the intermediate EPUB's ``--metadata title=``.
            See ``epub_renderer.render_epub`` for why this matters.
        author: Author name for the intermediate EPUB's ``--metadata author=``.
        language: BCP-47 language tag for the intermediate EPUB's
            ``--metadata lang=``. Defaults to "en".
        pandoc_path: pandoc binary (default "pandoc").
        calibre_path: calibre ebook-convert binary (default "ebook-convert").
        extra_args: Extra args appended to the **ebook-convert** (calibre) command.
        pandoc_extra_args: Extra args appended to the **pandoc** command that
            builds the intermediate EPUB (e.g. ``--resource-path=``). Distinct
            from *extra_args* — passing pandoc-only flags like
            ``--resource-path`` via *extra_args* would send them to calibre
            instead, where they are meaningless.

    Returns:
        MobiRenderResult with the output path, byte size, and duration.

    Raises:
        RenderingError: pandoc or ebook-convert missing, timed out, non-zero
            exit, or empty output.
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
    if shutil.which(calibre_path) is None:
        raise RenderingError(
            f"calibre ebook-convert binary not found: {calibre_path}. "
            "Install calibre (https://calibre-ebook.com/) to enable MOBI output."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()

    # ── Step 1: pandoc → intermediate EPUB ───────────────────────────────────
    with tempfile.TemporaryDirectory(prefix="mobi_render_") as tmp_dir:
        epub_path = Path(tmp_dir) / "intermediate.epub"

        pandoc_cmd: list[str] = [
            pandoc_path,
            "-f",
            "markdown+yaml_metadata_block",
            "-t",
            "epub",
            str(combined_md),
            "-o",
            str(epub_path),
            "--standalone",
            f"--metadata=lang:{language}",
        ]
        if title is not None:
            pandoc_cmd.append(f"--metadata=title:{title}")
        if author is not None:
            pandoc_cmd.append(f"--metadata=author:{author}")
        if bibliography is not None:
            pandoc_cmd.extend(["--citeproc", f"--bibliography={bibliography}"])
        if cover_image is not None:
            pandoc_cmd.append(f"--epub-cover-image={cover_image}")
        if pandoc_extra_args:
            pandoc_cmd.extend(pandoc_extra_args)

        logger.debug("Invoking pandoc for MOBI intermediate EPUB: %s", " ".join(pandoc_cmd))
        try:
            pandoc_result = subprocess.run(
                pandoc_cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            stderr_text = _process_output_text(exc.stderr) or _process_output_text(exc.stdout) or str(exc)
            raise RenderingError(
                f"pandoc EPUB (for MOBI) render timed out after {_TIMEOUT_SECONDS}s: "
                f"{_truncate_error_context(stderr_text)}"
            ) from exc

        if pandoc_result.returncode != 0:
            stderr_text = pandoc_result.stderr or pandoc_result.stdout or ""
            raise RenderingError(
                f"pandoc EPUB (for MOBI) render failed (exit {pandoc_result.returncode}): "
                f"{_truncate_error_context(stderr_text)}"
            )
        if not epub_path.exists() or epub_path.stat().st_size == 0:
            raise RenderingError(f"pandoc reported success but intermediate EPUB is missing or empty: {epub_path}")

        # ── Step 2: ebook-convert → MOBI ─────────────────────────────────────
        calibre_cmd: list[str] = [
            calibre_path,
            str(epub_path),
            str(output_path),
        ]
        if cover_image is not None:
            calibre_cmd.extend(["--cover", str(cover_image)])
        if extra_args:
            calibre_cmd.extend(extra_args)

        logger.debug("Invoking ebook-convert for MOBI: %s", " ".join(calibre_cmd))
        try:
            calibre_result = subprocess.run(
                calibre_cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            stderr_text = _process_output_text(exc.stderr) or _process_output_text(exc.stdout) or str(exc)
            raise RenderingError(
                f"ebook-convert MOBI render timed out after {_TIMEOUT_SECONDS}s: {_truncate_error_context(stderr_text)}"
            ) from exc

    duration = time.monotonic() - start

    if calibre_result.returncode != 0:
        stderr_text = calibre_result.stderr or calibre_result.stdout or ""
        raise RenderingError(
            f"ebook-convert MOBI render failed (exit {calibre_result.returncode}): "
            f"{_truncate_error_context(stderr_text)}"
        )
    if not output_path.exists():
        raise RenderingError(f"ebook-convert reported success but MOBI was not created: {output_path}")

    size = output_path.stat().st_size
    if size == 0:
        raise RenderingError(f"ebook-convert reported success but MOBI is empty: {output_path}")

    logger.info("  Generated MOBI: %s (%.1f KB, %.1fs)", output_path.name, size / 1024, duration)
    return MobiRenderResult(
        output_path=output_path,
        size_bytes=size,
        duration_seconds=duration,
    )


__all__ = ["MobiRenderResult", "render_mobi"]
