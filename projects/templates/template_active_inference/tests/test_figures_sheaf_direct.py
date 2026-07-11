"""Direct branch tests for ``visualizations.figures_sheaf``.

``test_figures`` already renders both sheaf figures on the shared project root.
This file covers the surrounding guard branches that render never reaches on a
clean tracked tree: the ``None`` early returns (missing matrix, empty payload),
the ``_has_explicit_panel_tracks`` false path, the freshness short-circuit that
returns the existing overview without re-rendering, and the ``output_path``
override on the coverage heatmap. MPLBACKEND=Agg is set by conftest and every
figure write targets a throwaway copy or a tmp path, never the tracked tree.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from visualizations.figures_sheaf import (
    _figure_inputs,
    _has_explicit_panel_tracks,
    _layers_output_is_fresh,
    coverage_heatmap_payload,
    figure_sheaf_coverage_heatmap,
    figure_sheaf_layers_overview,
)

from direct_recompute_support import copy_project_tree


# ---------------------------------------------------------------------------
# pure / tmp guard branches
# ---------------------------------------------------------------------------


def test_figure_inputs_lists_the_four_dependencies() -> None:
    assert _figure_inputs() == [
        "manuscript/sheaf/manifest.yaml",
        "manuscript/sheaf/tracks.yaml",
        "output/data/sheaf_coverage_matrix.json",
        "figures.yaml",
    ]


def test_layers_output_is_fresh_false_when_output_absent(tmp_path: Path) -> None:
    assert _layers_output_is_fresh(tmp_path, tmp_path / "nonexistent.png") is False


def test_has_explicit_panel_tracks_false_without_manifest(tmp_path: Path) -> None:
    assert _has_explicit_panel_tracks(tmp_path) is False


def test_coverage_heatmap_payload_none_branches(tmp_path: Path) -> None:
    # missing matrix file
    assert coverage_heatmap_payload(tmp_path) is None
    matrix = tmp_path / "output" / "data" / "sheaf_coverage_matrix.json"
    matrix.parent.mkdir(parents=True, exist_ok=True)
    # present but no tracks
    matrix.write_text(json.dumps({"tracks": [], "sections": [{"id": "s"}]}), encoding="utf-8")
    assert coverage_heatmap_payload(tmp_path) is None
    # present but no sections
    matrix.write_text(json.dumps({"tracks": ["prose"], "sections": []}), encoding="utf-8")
    assert coverage_heatmap_payload(tmp_path) is None


def test_coverage_heatmap_returns_none_without_payload(tmp_path: Path) -> None:
    assert figure_sheaf_coverage_heatmap(tmp_path) is None


# ---------------------------------------------------------------------------
# copy-backed branches: freshness short-circuit and output_path override
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def copied_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return copy_project_tree(tmp_path_factory.mktemp("figures_sheaf_tree"))


def test_has_explicit_panel_tracks_true_on_real_tree(copied_root: Path) -> None:
    # paired True control for the tmp-path False assertion above
    assert _has_explicit_panel_tracks(copied_root) is True


@pytest.mark.timeout(300)
def test_layers_overview_returns_fresh_output_without_rerender(copied_root: Path) -> None:
    out = copied_root / "output" / "figures" / "sheaf_layers_overview.png"
    assert out.is_file()
    # force the output strictly newer than every figure input
    past = 1_000_000.0
    for rel in _figure_inputs():
        os.utime(copied_root / rel, (past, past))
    future = time.time() + 10_000
    os.utime(out, (future, future))
    before_mtime = out.stat().st_mtime

    result = figure_sheaf_layers_overview(copied_root)
    assert result == out
    # fresh short-circuit returns the existing file untouched (no re-render)
    assert out.stat().st_mtime == before_mtime


@pytest.mark.timeout(300)
def test_coverage_heatmap_honors_output_path(copied_root: Path, tmp_path: Path) -> None:
    out = tmp_path / "custom_heatmap.png"
    result = figure_sheaf_coverage_heatmap(copied_root, output_path=out)
    assert result == out
    assert out.is_file()
    assert out.stat().st_size > 0
