"""Tests for the analysis-figure helpers (no mocks; real PNG output).

The figure functions live in ``src`` so the analysis scripts stay thin. These
tests render each figure with real data and a real ``SearchResult`` (computed by
the deterministic loop) and assert a non-empty PNG is written. Coverage of the
matplotlib drawing code is incidental; correctness here means "produces a valid,
non-empty image file from honest inputs."
"""

from __future__ import annotations

from pathlib import Path

from src.agents import DeterministicProposer
from src.figures import (
    AblationRow,
    write_ablation_figure,
    write_comparison_figure,
    write_efficiency_figure,
)
from src.objective import SyntheticObjective
from src.search import SearchConfig, run_search

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _rows() -> list[AblationRow]:
    return [
        {
            "configuration": "full coordination",
            "reported_metric": 0.91,
            "clean_metric": 0.90,
            "noise_inflation": 0.01,
            "confirmed_improvements": 7,
            "experiments_used": 60,
            "experiments_to_target": 41,
            "redundant_experiments": 0,
        },
        {
            "configuration": "no dead-end registry",
            "reported_metric": 0.93,
            "clean_metric": 0.88,
            "noise_inflation": 0.05,
            "confirmed_improvements": 6,
            "experiments_used": 60,
            "experiments_to_target": None,
            "redundant_experiments": 12,
        },
    ]


def _assert_png(path: Path) -> None:
    assert path.exists(), f"figure not written: {path}"
    data = path.read_bytes()
    assert data.startswith(_PNG_MAGIC), "output is not a PNG"
    assert len(data) > 1000, "PNG is implausibly small"


def test_write_ablation_figure(tmp_path: Path) -> None:
    path = tmp_path / "ablation.png"
    write_ablation_figure(_rows(), path)
    _assert_png(path)


def test_write_efficiency_figure(tmp_path: Path) -> None:
    path = tmp_path / "efficiency.png"
    write_efficiency_figure(_rows(), path)
    _assert_png(path)


def test_write_comparison_figure(tmp_path: Path) -> None:
    objective = SyntheticObjective(dimensions=4, noise_scale=0.02)
    proposer = DeterministicProposer()
    coordinated = run_search(objective, proposer, SearchConfig(budget=30))
    baseline = run_search(objective, proposer, SearchConfig.single_thread_baseline(budget=30))

    path = tmp_path / "comparison.png"
    write_comparison_figure(coordinated, baseline, path)
    _assert_png(path)
