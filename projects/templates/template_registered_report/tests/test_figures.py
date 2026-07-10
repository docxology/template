"""Tests for deterministic figure rendering (real files, no mocks)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from registered_report import freeze_registration, run_registered_analysis
from registered_report.figures import (
    plot_analysis_dag,
    plot_deviation_timeline,
    plot_hypothesis_map,
    plot_permutation_result,
    render_all_figures,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def load_frozen() -> dict[str, Any]:
    registration = cast(
        "dict[str, Any]",
        json.loads((PROJECT_ROOT / "data" / "example_registration.json").read_text(encoding="utf-8")),
    )
    return freeze_registration(registration)


def _assert_png(path: Path) -> None:
    assert path.is_file()
    assert path.stat().st_size > 0
    assert path.read_bytes()[:8] == _PNG_MAGIC


class TestFigureRendering:
    """Each plot writes a real, non-empty PNG for the demonstration study."""

    def test_hypothesis_map_writes_png(self, tmp_path: Path) -> None:
        _assert_png(plot_hypothesis_map(load_frozen(), tmp_path / "hypothesis_map.png"))

    def test_analysis_dag_writes_png(self, tmp_path: Path) -> None:
        _assert_png(plot_analysis_dag(tmp_path / "analysis_dag.png"))

    def test_deviation_timeline_writes_png(self, tmp_path: Path) -> None:
        _assert_png(plot_deviation_timeline(load_frozen(), tmp_path / "deviation_timeline.png"))

    def test_permutation_result_writes_png(self, tmp_path: Path) -> None:
        frozen = load_frozen()
        summary = run_registered_analysis(frozen)
        _assert_png(plot_permutation_result(summary, tmp_path / "permutation_result.png"))


class TestRenderAllFigures:
    """The orchestrating helper produces all four figures deterministically."""

    def test_render_all_writes_every_figure(self, tmp_path: Path) -> None:
        frozen = load_frozen()
        summary = run_registered_analysis(frozen)

        figures = render_all_figures(frozen, summary, tmp_path / "figures")

        assert set(figures) == {"hypothesis_map", "analysis_dag", "deviation_timeline", "permutation_result"}
        for path in figures.values():
            _assert_png(path)

    def test_render_all_is_byte_stable_across_runs(self, tmp_path: Path) -> None:
        frozen = load_frozen()
        summary = run_registered_analysis(frozen)

        first = render_all_figures(frozen, summary, tmp_path / "a")
        second = render_all_figures(frozen, summary, tmp_path / "b")

        for key, path in first.items():
            assert path.read_bytes() == second[key].read_bytes()
