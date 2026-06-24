"""Shared helpers for advanced plot modules."""

from visualization.style import SUBFIELD_NAMES


def format_subfield_label(sf: str) -> str:
    return SUBFIELD_NAMES.get(sf, sf.replace("_", " ").title())
