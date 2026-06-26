"""Tests for simulation and analysis statistics."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from analysis import summarize_sweep, write_analysis_statistics
from simulation.statistics import load_si_artifacts, summarize_si_trace


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
    assert stats["entropy_initial"] == pytest.approx(0.5)
    assert stats["entropy_terminal"] == pytest.approx(0.2)
    assert stats["entropy_drop"] == pytest.approx(0.3)
    assert stats["entropy_monotone_nonincreasing"] is True
    assert stats["action_switch_count"] == 0
    assert stats["action_switch_rate"] == pytest.approx(0.0)
    assert stats["observation_diversity"] == 2
    assert stats["trace_summary_steps_match"] is True
    assert stats["finite_trace"] is True


def test_summarize_si_trace_empty_steps_returns_zeroed_entropy() -> None:
    """An empty trace must return the zero-default entropy stats without raising."""
    stats = summarize_si_trace({"steps": []}, {"steps": 0, "actions": [], "observations": []})
    assert stats["entropy_min"] == 0.0
    assert stats["entropy_max"] == 0.0
    assert stats["entropy_monotone_nonincreasing"] is True
    assert stats["goal_reached"] is False


def test_summarize_si_trace_goal_reached_from_summary_override() -> None:
    """When the summary carries 'goal_reached', it overrides the observation check."""
    trace = {"steps": [{"step": 0, "belief_entropy": 0.1, "action": 0, "obs": 0}]}
    summary = {
        "steps": 1,
        "actions": [0],
        "observations": [0],  # normally goal_reached=False
        "config": {"tmaze": {"num_obs": 2}},
        "goal_reached": True,  # explicit override
    }
    stats = summarize_si_trace(trace, summary)
    assert stats["goal_reached"] is True


def test_load_si_artifacts_missing_files_returns_defaults(tmp_path: Path) -> None:
    """When neither artifact file exists the function returns empty defaults."""
    summary, trace = load_si_artifacts(tmp_path)
    assert summary == {}
    assert trace == {"steps": []}


def test_load_si_artifacts_reads_existing_files(tmp_path: Path) -> None:
    """When both artifact files exist they are loaded and returned."""
    data_dir = tmp_path / "output" / "data"
    data_dir.mkdir(parents=True)
    summary_data = {"steps": 2, "goal_reached": True}
    trace_data = {"steps": [{"step": 0, "obs": 1}]}
    (data_dir / "si_tmaze_summary.json").write_text(json.dumps(summary_data), encoding="utf-8")
    (data_dir / "si_tmaze_trace.json").write_text(json.dumps(trace_data), encoding="utf-8")
    summary, trace = load_si_artifacts(tmp_path)
    assert summary["steps"] == 2
    assert trace["steps"][0]["obs"] == 1


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
    assert payload["si_tmaze"]["trace_summary_steps_match"] is True
    assert payload["si_tmaze"]["finite_trace"] is True
