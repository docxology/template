"""Tests for idempotent coverage orchestration."""

from __future__ import annotations

from pathlib import Path

from manuscript.sheaf import compose_all_sections
from orchestration.coverage_pipeline import ensure_coverage_artifacts
from visualizations.figures import generate_all_figures


def test_compose_then_figures_does_not_reemit_fresh_json(project_root: Path) -> None:
    compose_all_sections(project_root)
    json_path = project_root / "output" / "data" / "sheaf_coverage_matrix.json"
    assert json_path.is_file()
    json_mtime_before = json_path.stat().st_mtime

    generate_all_figures(project_root)

    assert json_path.stat().st_mtime == json_mtime_before


def test_ensure_coverage_json_only_skips_png_and_page(project_root: Path) -> None:
    json_out, png_out, page_out = ensure_coverage_artifacts(project_root, json_only=True)
    assert json_out.exists()
    assert png_out is None
    assert page_out is None
