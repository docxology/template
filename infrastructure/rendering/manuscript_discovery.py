"""Manuscript discovery module - Discover and order manuscript files.

This module provides utilities for discovering manuscript files with proper
ordering and filtering. Part of the infrastructure layer (Layer 1) -
reusable across all projects.
"""

from pathlib import Path
from typing import Any

import yaml

from infrastructure.core.logging.utils import get_logger, log_success

logger = get_logger(__name__)


EXCLUDE_NAMES = {
    "preamble.md",
    "AGENTS.md",
    "README.md",
    "SYNTAX.md",
    "config.yaml",
    "config.yaml.example",
    "references.bib",
}


def verify_figures_exist(project_root: Path, manuscript_dir: Path) -> dict[str, Any]:
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
    result: dict[str, Any] = {
        "figures_dir_exists": figures_dir.exists(),
        "found_figures": [],
        "missing_figures": [],
        "total_expected": 0,
    }

    if not figures_dir.exists():
        logger.warning(f"ℹ️  Figures directory not found: {figures_dir}")
        return result

    # Figures are commonly grouped into experiment-family subdirectories.
    # Report paths relative to output/figures so preflight logging reflects
    # the same recursive figure layout used by the combined PDF renderer.
    figures = sorted(figures_dir.rglob("*.png"))
    result["found_figures"] = [str(f.relative_to(figures_dir)) for f in figures]

    if figures:
        log_success(f"Found {len(figures)} figure(s) in {figures_dir.name}/", logger)
    else:
        logger.warning(f"⚠️  Figures directory exists but is empty: {figures_dir}")

    return result


def _entry_enabled(entry: Any) -> bool:
    return not (isinstance(entry, dict) and entry.get("enabled") is False)


def _entry_file(entry: Any) -> str | None:
    if isinstance(entry, dict):
        value = entry.get("file")
        return value if isinstance(value, str) and value else None
    return entry if isinstance(entry, str) and entry else None


def _append_existing(
    ordered_files: list[Path],
    seen: set[Path],
    candidates: list[Path],
    label: str,
) -> None:
    for candidate in candidates:
        if candidate.is_file():
            resolved = candidate.resolve()
            if resolved not in seen:
                ordered_files.append(candidate)
                seen.add(resolved)
            return

    if candidates:
        logger.warning("Configured manuscript file not found (%s): %s", label, candidates[0])


def _configured_manuscript_files(manuscript_dir: Path) -> list[Path] | None:
    """Read config.yaml ordering for nested textbook manuscripts when present."""
    config_path = manuscript_dir / "config.yaml"
    if not config_path.is_file():
        return None

    try:
        loaded: Any = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        logger.warning("Could not parse manuscript config for ordered discovery: %s", exc)
        return None

    if not isinstance(loaded, dict):
        return None

    has_layout = any(key in loaded for key in ("front_matter", "units", "appendices"))
    if not has_layout:
        return None

    ordered_files: list[Path] = []
    seen: set[Path] = set()

    front_matter = loaded.get("front_matter")
    if isinstance(front_matter, dict) and front_matter.get("include_front_matter", True):
        include_preface = front_matter.get("include_preface", True)
        files = front_matter.get("files", [])
        if isinstance(files, list):
            for entry in files:
                file_name = _entry_file(entry)
                if not file_name or not _entry_enabled(entry):
                    continue
                if file_name == "preface.md" and not include_preface:
                    continue
                _append_existing(
                    ordered_files,
                    seen,
                    [manuscript_dir / file_name],
                    f"front matter {file_name}",
                )

    units = loaded.get("units", [])
    if isinstance(units, list):
        for unit in units:
            if not isinstance(unit, dict) or not _entry_enabled(unit):
                continue
            directory = unit.get("directory") or unit.get("id")
            if not isinstance(directory, str) or not directory:
                continue
            unit_dir = manuscript_dir / directory
            unit_intro = unit_dir / "unit_intro.md"
            if unit_intro.is_file():
                _append_existing(ordered_files, seen, [unit_intro], f"{directory}/unit_intro.md")
            chapters = unit.get("chapters", [])
            if isinstance(chapters, list):
                for chapter in chapters:
                    file_name = _entry_file(chapter)
                    if not file_name or not _entry_enabled(chapter):
                        continue
                    _append_existing(
                        ordered_files,
                        seen,
                        [unit_dir / file_name],
                        f"{directory}/{file_name}",
                    )

    appendices = loaded.get("appendices")
    if isinstance(appendices, dict):
        if appendices.get("include_labs", False):
            _append_grouped_appendix_files(ordered_files, seen, manuscript_dir, appendices, "labs")
        if appendices.get("include_questions", False):
            _append_grouped_appendix_files(ordered_files, seen, manuscript_dir, appendices, "questions")
        if appendices.get("include_reference", False):
            references = appendices.get("reference", [])
            if isinstance(references, list):
                for entry in references:
                    file_name = _entry_file(entry)
                    if not file_name or not _entry_enabled(entry):
                        continue
                    _append_existing(
                        ordered_files,
                        seen,
                        [
                            manuscript_dir / "appendices" / file_name,
                            manuscript_dir / file_name,
                        ],
                        f"reference appendix {file_name}",
                    )

    return ordered_files


def _append_grouped_appendix_files(
    ordered_files: list[Path],
    seen: set[Path],
    manuscript_dir: Path,
    appendices: dict[str, Any],
    group_name: str,
) -> None:
    bundles = appendices.get(group_name, [])
    if not isinstance(bundles, list):
        return

    for bundle in bundles:
        if not isinstance(bundle, dict) or not _entry_enabled(bundle):
            continue
        unit = bundle.get("unit")
        if not isinstance(unit, str) or not unit:
            continue
        files = bundle.get("files", [])
        if not isinstance(files, list):
            continue
        for entry in files:
            file_name = _entry_file(entry)
            if not file_name or not _entry_enabled(entry):
                continue
            _append_existing(
                ordered_files,
                seen,
                [manuscript_dir / group_name / unit / file_name],
                f"{group_name}/{unit}/{file_name}",
            )


def _top_level_markdown_files(manuscript_dir: Path) -> list[Path]:
    all_md_files: list[Path] = []
    seen_keys = set()

    for f in manuscript_dir.iterdir():
        if not f.is_file():
            continue
        if f.suffix.lower() == ".md" and f.name not in EXCLUDE_NAMES:
            key = (f.stem.lower(), f.suffix.lower())
            if key not in seen_keys:
                seen_keys.add(key)
                all_md_files.append(f)

    return all_md_files


def _log_configured_discovery(ordered_files: list[Path], tex_files: list[Path], manuscript_dir: Path) -> None:
    logger.info(f"Discovered {len(ordered_files)} manuscript file(s) from config.yaml:")
    if ordered_files:
        logger.info(f"  Configured order ({len(ordered_files)}):")
        for path in ordered_files:
            logger.info(f"    • {path.relative_to(manuscript_dir)}")

    if tex_files:
        logger.info(f"  LaTeX files ({len(tex_files)}):")
        for f in tex_files:
            logger.info(f"    • {f.name}")


def discover_manuscript_files(manuscript_dir: Path) -> list[Path]:
    """Discover manuscript files with proper ordering and filtering.

    Filters out non-manuscript files and orders files for proper document structure:
    1. Main sections: digit-prefixed ``00_*.md`` through ``09_*.md`` (lexicographic stem order)
    2. Supplemental: S01_*.md through S0N_*.md
    3. Glossary: 98_*.md
    4. References: 99_*.md (always last)
    5. LaTeX files: *.tex (appended after markdown)

    When any digit-prefixed ``NN_*.md`` section exists, ``complete.md`` is omitted — it is an
    assembled copy of section files and would duplicate figure labels in combined PDF/HTML.

    Args:
        manuscript_dir: Path to manuscript directory

    Returns:
        List of ordered manuscript file paths (markdown and LaTeX)
    """
    if not manuscript_dir.exists():
        logger.warning(f"Manuscript directory not found: {manuscript_dir}")
        return []

    all_md_files = _top_level_markdown_files(manuscript_dir)

    # ``complete.md`` is an assembled concatenation of numbered sections (some projects
    # emit it under output/manuscript/). Rendering it alongside ``00_*.md`` duplicates
    # figures and breaks pandoc-crossref (duplicate \\label{}). Omit when sections exist.
    numbered_present = any(
        p.stem[0].isdigit()
        for p in all_md_files
        if p.stem and not p.stem.startswith("99_") and not p.stem.startswith("98_")
    )
    if numbered_present:
        all_md_files = [p for p in all_md_files if p.name != "complete.md"]
    else:
        configured_files = _configured_manuscript_files(manuscript_dir)
        if configured_files is not None:
            tex_files = sorted(manuscript_dir.glob("*.tex"))
            _log_configured_discovery(configured_files, tex_files, manuscript_dir)
            return configured_files + tex_files

    # Organize files by category for proper ordering
    main_sections: list[Path] = []  # 01_*.md - 09_*.md
    supplemental: list[Path] = []  # S01_*.md - S0N_*.md
    glossary: list[Path] = []  # 98_*.md
    references: list[Path] = []  # 99_*.md
    other: list[Path] = []  # Everything else

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
