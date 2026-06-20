"""Tests for registry-backed figures."""

from __future__ import annotations

import hashlib
from pathlib import Path

from infrastructure.validation.content.figure_validator import validate_figure_registry
from src.figures import write_all_figures
from src.figures.figure_registry import FIGURE_SPECS
from src.loop import run_sia_loop_project

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Markdown sections that reference each figure (single source of truth for captions).
_MANUSCRIPT_SECTIONS = (
    PROJECT_ROOT / "manuscript" / "02_methodology.md",
    PROJECT_ROOT / "manuscript" / "03_results.md",
)


def test_figures_are_deterministic_pngs():
    run_sia_loop_project(PROJECT_ROOT, live=False)
    first = write_all_figures(PROJECT_ROOT)
    first_pngs = [path for path in first if path.suffix == ".png"]
    hashes_first = [hashlib.sha256(path.read_bytes()).hexdigest() for path in first_pngs]
    second = write_all_figures(PROJECT_ROOT)
    second_pngs = [path for path in second if path.suffix == ".png"]
    hashes_second = [hashlib.sha256(path.read_bytes()).hexdigest() for path in second_pngs]
    assert hashes_first == hashes_second
    for path in first_pngs:
        assert path.is_file()
        assert path.stat().st_size > 0
        assert path.suffix == ".png"
    assert PROJECT_ROOT / "output" / "figures" / "figure_registry.json" in first


def test_figure_specs_match_manuscript():
    """Each registered caption and filename must appear in the manuscript markdown.

    The figure registry NOTE asks captions to mirror the canonical manuscript
    captions; this enforces that contract so the two cannot silently drift.
    Markdown inline-code backticks are stripped before comparison because the
    manuscript wraps symbol names (e.g. ``write_sia_loop_topology``) in code spans.
    """
    combined = "".join(path.read_text(encoding="utf-8") for path in _MANUSCRIPT_SECTIONS).replace("`", "")
    for spec in FIGURE_SPECS:
        assert spec.filename in combined, f"figure file {spec.filename} not referenced"
        assert spec.caption in combined, f"caption drift for {spec.figure_id}"


def test_figure_registry_validates_manuscript_references():
    run_sia_loop_project(PROJECT_ROOT, live=False)
    paths = write_all_figures(PROJECT_ROOT)
    registry = PROJECT_ROOT / "output" / "figures" / "figure_registry.json"

    ok, issues = validate_figure_registry(registry, PROJECT_ROOT / "manuscript")

    assert registry in paths
    assert ok, issues
