"""Tests for simulation and analysis statistics."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis import run_analysis, summarize_sweep, write_analysis_statistics
from simulation.statistics import summarize_si_trace


def test_summarize_si_trace_from_fixture() -> None:
    trace = {
        "steps": [
            {"step": 0, "belief_entropy": 0.5, "action": 0, "obs": 0},
            {"step": 1, "belief_entropy": 0.2, "action": 0, "obs": 1},
        ]
    }
    summary = {
        "steps": 2,
        "actions": [0, 0],
        "observations": [0, 1],
        "config": {"tmaze": {"num_obs": 2}},
    }
    stats = summarize_si_trace(trace, summary)
    assert stats["steps"] == 2
    assert stats["action_diversity"] == 1
    assert stats["goal_reached"] is True
    assert stats["entropy_min"] == pytest.approx(0.2)
    assert stats["entropy_max"] == pytest.approx(0.5)


def test_summarize_sweep(tmp_path: Path) -> None:
    csv_path = tmp_path / "parameter_sweep.csv"
    csv_path.write_text(
        "lambda,closed_form_mi,empirical_mi\n0.0,0.0,0.01\n1.0,0.5,0.48\n",
        encoding="utf-8",
    )
    stats = summarize_sweep(csv_path)
    assert stats["grid_points"] == 2
    assert stats["max_residual"] == pytest.approx(0.02)
    assert stats["rmse_mi"] > 0.0


def test_write_analysis_statistics(project_root: Path, tmp_path: Path) -> None:
    from analysis import run_analysis
    from simulation.si_runner import pymdp_available, run_and_persist

    run_analysis(project_root)
    if pymdp_available():
        run_and_persist(project_root)
    out = write_analysis_statistics(project_root)
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "sweep" in payload
    assert "si_tmaze" in payload
    assert "pymdp_mode" in payload
