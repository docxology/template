"""Tests for the deterministic graph-world artifact writers.

No mocks — writes real artifacts to ``tmp_path`` and reads them back.
"""

from __future__ import annotations

import json
from pathlib import Path

from simulation.graph_world import write_graph_world_artifacts, write_graph_world_stub


def test_write_graph_world_artifacts_creates_both_files(tmp_path: Path) -> None:
    """Both summary and trace JSON files must be created under tmp_path/output/data/."""
    paths = write_graph_world_artifacts(tmp_path)
    assert paths["summary"].exists()
    assert paths["trace"].exists()


def test_graph_world_summary_schema(tmp_path: Path) -> None:
    """The summary must carry the required metadata fields."""
    paths = write_graph_world_artifacts(tmp_path)
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    assert summary["status"] == "ok"
    assert summary["node_count"] == 4
    assert summary["edge_count"] == 4
    assert summary["steps"] == 4
    assert summary["start"] == "start"
    assert summary["goal"] == "goal"
    assert summary["goal_reached"] is True
    assert "mean_belief_entropy" in summary
    assert isinstance(summary["policy"], list)
    assert len(summary["policy"]) == 4


def test_graph_world_trace_schema(tmp_path: Path) -> None:
    """The trace must contain four step records with the required fields."""
    paths = write_graph_world_artifacts(tmp_path)
    payload = json.loads(paths["trace"].read_text(encoding="utf-8"))
    steps = payload["steps"]
    assert len(steps) == 4
    for step in steps:
        assert "step" in step
        assert "node" in step
        assert "action" in step
        assert "belief_entropy" in step
        assert "goal_probability" in step
    # The trace must start at START and end at GOAL.
    assert steps[0]["node"] == "start"
    assert steps[-1]["node"] == "goal"


def test_graph_world_belief_entropy_decreases(tmp_path: Path) -> None:
    """Entropy must be non-negative and monotonically non-increasing along the trace."""
    paths = write_graph_world_artifacts(tmp_path)
    steps = json.loads(paths["trace"].read_text(encoding="utf-8"))["steps"]
    entropies = [step["belief_entropy"] for step in steps]
    assert all(e >= 0.0 for e in entropies)
    # Final entropy is 0 (goal reached — perfectly certain).
    assert entropies[-1] == 0.0
    # Entropy is non-increasing.
    for prev, cur in zip(entropies, entropies[1:], strict=False):
        assert cur <= prev + 1e-12


def test_graph_world_goal_probability_increases(tmp_path: Path) -> None:
    """Goal probability must start at 0 and end at 1 (exact at start and goal)."""
    paths = write_graph_world_artifacts(tmp_path)
    steps = json.loads(paths["trace"].read_text(encoding="utf-8"))["steps"]
    probs = [step["goal_probability"] for step in steps]
    assert probs[0] == 0.0
    assert probs[-1] == 1.0
    for prev, cur in zip(probs, probs[1:], strict=False):
        assert cur >= prev


def test_write_graph_world_stub_returns_summary_path(tmp_path: Path) -> None:
    """write_graph_world_stub is a backward-compatible wrapper returning the summary path."""
    summary_path = write_graph_world_stub(tmp_path)
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "ok"


def test_write_graph_world_artifacts_is_byte_deterministic(tmp_path: Path) -> None:
    """Two writes to separate directories must produce byte-identical JSON payloads."""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    paths_a = write_graph_world_artifacts(dir_a)
    paths_b = write_graph_world_artifacts(dir_b)
    assert paths_a["summary"].read_text(encoding="utf-8") == paths_b["summary"].read_text(encoding="utf-8")
    assert paths_a["trace"].read_text(encoding="utf-8") == paths_b["trace"].read_text(encoding="utf-8")
