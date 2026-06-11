"""Tests for idempotent coverage orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest

from manuscript.sheaf import compose_all_sections
from orchestration.coverage_pipeline import ensure_coverage_artifacts
from visualizations.figures import generate_all_figures

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
# generate_all_figures() consumes the simulation traces produced by Stage 4
# analysis (which needs pymdp). In pipeline order, Stage 3 tests run before
# Stage 4 and Stage 0 cleans outputs, so these may legitimately be absent when
# the suite runs standalone — skip rather than crash on the missing artifact.
_FIGURE_INPUT = _PROJECT_ROOT / "output" / "data" / "si_tmaze_trace.json"


@pytest.mark.skipif(
    not _FIGURE_INPUT.is_file(),
    reason="figure-input analysis artifacts absent (Stage 4 analysis / pymdp not run)",
)
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
