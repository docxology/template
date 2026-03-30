"""Helpers for log lines that may touch user- or model-generated text."""

from __future__ import annotations


def preview_for_log(text: str, max_chars: int = 48) -> str:
    """Return a single-line, length-bounded snippet for structured logs."""
    if not text:
        return ""
    collapsed = " ".join(str(text).split())
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[: max_chars - 1] + "…"
