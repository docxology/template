"""Zenodo URL helpers without rendering dependencies."""

from __future__ import annotations

import re


def zenodo_record_url_from_doi(doi: str) -> str:
    """Return a Zenodo records page URL from a DOI suffix."""
    match = re.fullmatch(r"10\.5281/zenodo\.(\d+)", doi.strip())
    if match:
        return f"https://zenodo.org/records/{match.group(1)}"
    return f"https://doi.org/{doi}"
