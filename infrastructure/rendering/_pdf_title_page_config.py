"""Config loading and metadata normalization for the title page."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.logging.utils import get_logger

__all__ = [
    "_author_blocks",
    "_front_matter_options",
    "_load_render_config",
    "_metadata_from_config",
    "_rendering_options",
    "_resolve_config_yaml",
    "build_pandoc_metadata",
]

logger = get_logger(__name__)


def _rendering_options(config: dict[str, Any] | None) -> dict[str, Any]:
    """Return validated project-local layout options with safe renderer defaults.

    Projects may tune page flow and figure occupancy without injecting arbitrary LaTeX.  Fractions
    are restricted to ``(0, 1]`` and serialized as short decimal strings before they reach a
    LaTeX dimension; malformed values fall back to the established template defaults.
    """
    rendering = config.get("rendering", {}) if isinstance(config, dict) else {}
    if not isinstance(rendering, dict):
        rendering = {}

    def fraction(name: str, default: float) -> str:
        raw = rendering.get(name, default)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = default
        if not math.isfinite(value) or not 0.0 < value <= 1.0:
            value = default
        return f"{value:g}"

    return {
        "section_breaks": rendering.get("section_breaks", True)
        if isinstance(rendering.get("section_breaks", True), bool)
        else True,
        "figure_height_fraction": fraction("figure_height_fraction", 0.50),
        "cover_height_fraction": fraction("cover_height_fraction", 0.60),
        "front_matter_figure_height_fraction": fraction("front_matter_figure_height_fraction", 0.50),
    }


def _resolve_config_yaml(manuscript_dir: Path) -> Path | None:
    """Locate ``config.yaml`` near a manuscript directory."""
    primary = manuscript_dir / "config.yaml"
    if primary.is_file():
        return primary
    for parent in (manuscript_dir.parent, manuscript_dir.parent.parent):
        try:
            candidate = parent / "manuscript" / "config.yaml"
        except (TypeError, ValueError):
            continue
        if candidate.is_file() and candidate != primary:
            return candidate
    return None


def _load_render_config(manuscript_dir: Path) -> tuple[dict[str, Any] | None, Path | None]:
    """Load the nearest manuscript config file."""
    config_file = _resolve_config_yaml(manuscript_dir)
    if config_file is None:
        logger.debug(f"Config file not found near: {manuscript_dir}")
        return None, None
    try:
        with config_file.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as e:
        logger.warning(f"Error reading config.yaml: {e}")
        return None, None
    if not isinstance(config, dict):
        return None, config_file
    return config, config_file


def build_pandoc_metadata(config: dict[str, Any]) -> dict[str, Any]:
    """Build pandoc YAML metadata from a manuscript config dict."""
    paper = config.get("paper") or {}
    meta: dict[str, Any] = {}
    if paper.get("title"):
        meta["title"] = str(paper["title"])
    if paper.get("subtitle"):
        meta["subtitle"] = str(paper["subtitle"])
    authors: list[str] = []
    for entry in config.get("authors") or []:
        if isinstance(entry, dict) and entry.get("name"):
            name = str(entry["name"])
            affiliations = entry.get("affiliations") or []
            if affiliations:
                name += " (" + "; ".join(str(affiliation) for affiliation in affiliations) + ")"
            authors.append(name)
        elif isinstance(entry, str):
            authors.append(entry)
    if authors:
        meta["author"] = authors
    date = paper.get("date") or (config.get("publication") or {}).get("year")
    if date:
        meta["date"] = str(date)
    return meta


def _front_matter_options(config: dict[str, Any]) -> dict[str, Any]:
    """Return optional front-matter rendering settings."""
    front_matter = config.get("front_matter", {}) or {}
    return front_matter if isinstance(front_matter, dict) else {}


def _metadata_from_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return book/paper metadata with book fields taking precedence."""
    book = config.get("book", {}) or {}
    paper = config.get("paper", {}) or {}
    if not isinstance(book, dict):
        book = {}
    if not isinstance(paper, dict):
        paper = {}
    title = book.get("title") or paper.get("title") or "Research Paper"
    subtitle = book.get("subtitle") or paper.get("subtitle") or ""
    year = book.get("year") or paper.get("year") or ""
    edition = book.get("edition") or ""
    date = paper.get("date") or (str(year) if year else "")
    return {
        "book": book,
        "paper": paper,
        "title": str(title),
        "subtitle": str(subtitle),
        "date": str(date),
        "year": str(year),
        "edition": str(edition),
        "license": str(book.get("license", "")),
        "code_license": str(book.get("code_license", "")),
    }


def _author_blocks(config: dict[str, Any]) -> list[dict[str, str]]:
    """Normalize author metadata from config."""
    raw_authors = config.get("authors", [])
    authors: list[dict[str, str]] = []
    if isinstance(raw_authors, list):
        for author in raw_authors:
            if not isinstance(author, dict) or not author.get("name"):
                continue
            affil = author.get("affiliation", "")
            if not affil and isinstance(author.get("affiliations"), list):
                affil = ", ".join(str(item) for item in author["affiliations"])
            authors.append(
                {
                    "name": str(author.get("name", "")),
                    "affiliation": str(affil),
                    "email": str(author.get("email", "")),
                    "orcid": str(author.get("orcid", "")),
                }
            )
    if authors:
        return authors

    book = config.get("book", {}) or {}
    if isinstance(book, dict) and book.get("author"):
        authors.append(
            {
                "name": str(book.get("author", "")),
                "affiliation": "",
                "email": "",
                "orcid": str(book.get("orcid", "")),
            }
        )
    return authors
