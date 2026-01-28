"""Manuscript discovery module - Discover and order manuscript files.

This module provides utilities for discovering manuscript files with proper
ordering and filtering. Part of the infrastructure layer (Layer 1) -
reusable across all projects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from infrastructure.core.logging_utils import get_logger, log_success

logger = get_logger(__name__)


def verify_figures_exist(project_root: Path, manuscript_dir: Path) -> Dict[str, Any]:
    """Verify expected figures exist, return status.

    Args:
        project_root: Path to project root
        manuscript_dir: Path to manuscript directory

    Returns:
        Dictionary with figure verification status:
        - figures_dir_exists: Whether figures directory exists
        - found_figures: List of found figure filenames
        - missing_figures: List of missing figure filenames (currently empty)
        - total_expected: Total expected figures (currently 0)
    """
    figures_dir = project_root / "output" / "figures"
    result: Dict[str, Any] = {
        "figures_dir_exists": figures_dir.exists(),
        "found_figures": [],
        "missing_figures": [],
        "total_expected": 0,
    }

    if not figures_dir.exists():
        logger.warning(f"ℹ️  Figures directory not found: {figures_dir}")
        return result

    # Find all PNG files in figures directory
    figures = sorted(list(figures_dir.glob("*.png")))
    result["found_figures"] = [f.name for f in figures]

    if figures:
        log_success(f"Found {len(figures)} figure(s) in {figures_dir.name}/", logger)
    else:
        logger.warning(f"⚠️  Figures directory exists but is empty: {figures_dir}")

    return result


def discover_manuscript_files(manuscript_dir: Path) -> List[Path]:
    """Discover manuscript files with proper ordering and filtering.

    Filters out non-manuscript files and orders files for proper document structure:
    1. Main sections: 01_*.md through 09_*.md
    2. Supplemental: S01_*.md through S0N_*.md
    3. Glossary: 98_*.md
    4. References: 99_*.md (always last)
    5. LaTeX files: *.tex (appended after markdown)

    Args:
        manuscript_dir: Path to manuscript directory

    Returns:
        List of ordered manuscript file paths (markdown and LaTeX)
    """
    if not manuscript_dir.exists():
        logger.warning(f"Manuscript directory not found: {manuscript_dir}")
        return []

    # Files to exclude (metadata, infrastructure) - case-sensitive matching
    exclude_names = {
        "preamble.md",
        "AGENTS.md",
        "README.md",
        "config.yaml",
        "config.yaml.example",
        "references.bib",
    }

    # Discover all markdown files
    # On case-insensitive filesystems, we need to check all files manually
    # because glob patterns are case-sensitive
    all_md_files = []
    seen_keys = set()  # Track (stem_lower, suffix_lower) to detect duplicates

    # Check all files in directory for markdown extensions
    for f in manuscript_dir.iterdir():
        if not f.is_file():
            continue
        # Check if it's a markdown file (case-insensitive check)
        if f.suffix.lower() == ".md":
            # Check if it's excluded (case-sensitive)
            if f.name not in exclude_names:
                key = (f.stem.lower(), f.suffix.lower())
                # On case-insensitive filesystems, skip duplicates
                # Preserve the original case as returned by the filesystem
                if key not in seen_keys:
                    seen_keys.add(key)
                    all_md_files.append(f)

    # Organize files by category for proper ordering
    main_sections: List[Path] = []  # 01_*.md - 09_*.md
    supplemental: List[Path] = []  # S01_*.md - S0N_*.md
    glossary: List[Path] = []  # 98_*.md
    references: List[Path] = []  # 99_*.md
    other: List[Path] = []  # Everything else

    for md_file in all_md_files:
        stem = md_file.stem

        if stem.startswith("99_"):
            references.append(md_file)
        elif stem.startswith("98_"):
            glossary.append(md_file)
        elif stem.startswith("S"):
            supplemental.append(md_file)
        elif stem[0].isdigit():
            main_sections.append(md_file)
        else:
            other.append(md_file)

    # Sort within each category
    main_sections.sort(key=lambda x: x.stem)
    supplemental.sort(key=lambda x: x.stem)
    glossary.sort(key=lambda x: x.stem)
    references.sort(key=lambda x: x.stem)
    other.sort(key=lambda x: x.stem)

    # Combine in order: main -> supplemental -> glossary -> other -> references
    # References must always be last
    ordered_files = main_sections + supplemental + glossary + other + references

    # Log discovery with full details - ALWAYS show filenames
    logger.info(f"Discovered {len(ordered_files)} manuscript file(s):")

    if main_sections:
        logger.info(f"  Main sections ({len(main_sections)}):")
        for f in main_sections:
            logger.info(f"    • {f.name}")

    if supplemental:
        logger.info(f"  Supplemental ({len(supplemental)}):")
        for f in supplemental:
            logger.info(f"    • {f.name}")

    if glossary:
        logger.info(f"  Glossary ({len(glossary)}):")
        for f in glossary:
            logger.info(f"    • {f.name}")

    if references:
        logger.info(f"  References ({len(references)}):")
        for f in references:
            logger.info(f"    • {f.name}")

    if other:
        logger.info(f"  Other ({len(other)}):")
        for f in other:
            logger.info(f"    • {f.name}")

    # Find LaTeX files for direct compilation
    tex_files = sorted(manuscript_dir.glob("*.tex"))
    if tex_files:
        logger.info(f"  LaTeX files ({len(tex_files)}):")
        for f in tex_files:
            logger.info(f"    • {f.name}")

    return ordered_files + tex_files
