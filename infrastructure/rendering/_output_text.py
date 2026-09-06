"""Shared subprocess-output text normalization for pandoc diagnostics.

``docx_renderer``, ``epub_renderer``, and ``mobi_renderer`` each normalize
``subprocess.run`` stdout/stderr values (``bytes``, ``str``, or ``None``) to a
``str`` for ``RenderingError`` messages and diagnostics. This single helper is
the canonical implementation; the three renderers import it by name so the
errror-message behavior stays byte-identical across formats.
"""

from __future__ import annotations

_ERROR_CONTEXT_LIMIT = 500


def _process_output_text(value: bytes | str | None) -> str:
    """Normalize subprocess stdout/stderr values to text for diagnostics."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    return ""


def _truncate_error_context(stderr_text: str) -> str:
    """Return bounded stderr/stdout context for ``RenderingError`` messages.

    Shared by the DOCX, EPUB, and MOBI renderers so the bounded-context
    contract stays byte-identical across formats.
    """
    stripped = stderr_text.strip()
    if not stripped:
        return "no stderr captured"
    return stripped[:_ERROR_CONTEXT_LIMIT]
