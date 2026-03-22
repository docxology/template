"""Canonical ordering of the sixteen newspaper page slices."""

from __future__ import annotations

from pathlib import Path

# (file stem without .md, section title for prose)
PAGE_SLICES: tuple[tuple[str, str], ...] = (
    ("01_front_page", "Front Page"),
    ("02_national", "National"),
    ("03_world", "World"),
    ("04_business", "Business"),
    ("05_technology", "Technology"),
    ("06_sports", "Sports"),
    ("07_arts", "Arts & Culture"),
    ("08_editorial", "Editorial"),
    ("09_opinion", "Opinion"),
    ("10_letters", "Letters"),
    ("11_local", "Local"),
    ("12_features", "Features"),
    ("13_health", "Health"),
    ("14_science", "Science"),
    ("15_obituaries", "Obituaries"),
    ("16_classifieds", "Classifieds"),
)

SLICE_BY_STEM: dict[str, tuple[str, str]] = {stem: (stem, title) for stem, title in PAGE_SLICES}


def slice_count() -> int:
    """Number of core edition folios (main slices)."""
    return len(PAGE_SLICES)


def manuscript_stems_ordered() -> tuple[str, ...]:
    """Ordered stems; same order as :data:`PAGE_SLICES`."""
    return slice_stems()


def get_slice(stem: str) -> tuple[str, str] | None:
    """Return ``(stem, section_title)`` or ``None`` if unknown."""
    return SLICE_BY_STEM.get(stem)


def slice_stems() -> tuple[str, ...]:
    """Return ordered manuscript stems (``01_front_page``, …)."""
    return tuple(s for s, _ in PAGE_SLICES)


def manuscript_filenames() -> tuple[str, ...]:
    """Return ordered markdown basenames (``01_front_page.md``, …)."""
    return tuple(f"{s}.md" for s in slice_stems())


def validate_inventory(manuscript_dir: Path) -> list[str]:
    """Return a list of expected filenames missing from ``manuscript_dir``."""
    missing: list[str] = []
    for name in manuscript_filenames():
        if not (manuscript_dir / name).is_file():
            missing.append(name)
    return missing


# Supplemental / glossary slices (optional for inventory; included in stats when present)
MANUSCRIPT_OPTIONAL_FILENAMES: tuple[str, ...] = (
    "S01_layout_and_pipeline.md",
    "S02_typography_and_measure.md",
    "S03_validation_and_outputs.md",
    "98_newspaper_and_pipeline_terms.md",
)


def all_tracked_manuscript_basenames() -> tuple[str, ...]:
    """Core folios plus optional supplemental/glossary names."""
    return manuscript_filenames() + MANUSCRIPT_OPTIONAL_FILENAMES
