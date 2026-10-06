"""Shared helpers for advanced plot modules."""

from template_literature_meta_analysis.visualization.style import SUBFIELD_NAMES


def format_subfield_label(sf: str) -> str:
    """Format subfield label."""
    return str(SUBFIELD_NAMES.get(sf, sf.replace("_", " ").title()))
