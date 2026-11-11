"""Shared Beamer participation predicates for manuscript rendering and readback."""

from pathlib import Path

from infrastructure.transmission.transmission_bookends import is_transmission_bookend

_SKIP_BEAMER = "<!-- render:skip-beamer -->"
_SKIP_BEAMER_BYTES = _SKIP_BEAMER.encode("ascii")


def skips_beamer(source: str | bytes) -> bool:
    """Apply the same directive to decoded text or retained original bytes."""
    if isinstance(source, bytes):
        return _SKIP_BEAMER_BYTES in source
    return _SKIP_BEAMER in source


def is_beamer_manuscript_section(source: Path) -> bool:
    """Select manuscript Markdown sections eligible for a Beamer derivative."""
    return source.suffix == ".md" and not is_transmission_bookend(source)
