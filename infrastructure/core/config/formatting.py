"""Author formatting utilities for manuscript metadata.

Functions for formatting author information for LaTeX output and display.

Part of the infrastructure layer (Layer 1) - reusable across all projects.
"""

from __future__ import annotations

from infrastructure.core.config.schema import AuthorConfig


def format_author_details(authors: list[AuthorConfig], doi: str = "") -> str:
    """Format author details string for LaTeX.

    Args:
        authors: List of author dictionaries (name, orcid, email, etc.)
        doi: Optional DOI string to include

    Returns:
        Formatted string with LaTeX line breaks
    """
    if not authors:
        return ""

    # Get primary/corresponding author (first one marked corresponding, or first)
    primary = next((a for a in authors if a.get("corresponding", False)), authors[0])

    parts = []
    if primary.get("orcid"):
        parts.append(f"ORCID: {primary['orcid']}")
    if primary.get("email"):
        parts.append(f"Email: {primary['email']}")
    if doi:
        parts.append(f"DOI: {doi}")

    # Join with "\\\\ " (double backslash + space) for LaTeX line breaks
    return "\\\\ ".join(parts)


def format_author_name(authors: list[AuthorConfig]) -> str:
    """Format author name(s) for display.

    Args:
        authors: List of author dictionaries

    Returns:
        Primary author name or "Project Author" if empty
    """
    if not authors:
        return "Project Author"

    return authors[0].get("name", "Project Author")
