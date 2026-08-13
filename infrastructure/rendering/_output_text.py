"""Shared subprocess-output text normalization for pandoc diagnostics.

``docx_renderer``, ``epub_renderer``, and ``mobi_renderer`` each normalize
``subprocess.run`` stdout/stderr values (``bytes``, ``str``, or ``None``) to a
``str`` for ``RenderingError`` messages and diagnostics. This single helper is
the canonical implementation; the three renderers import it by name so the
errror-message behavior stays byte-identical across formats.
"""

from __future__ import annotations


def _process_output_text(value: bytes | str | None) -> str:
    """Normalize subprocess stdout/stderr values to text for diagnostics."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    return ""