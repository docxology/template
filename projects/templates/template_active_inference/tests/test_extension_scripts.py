"""Subprocess tests for deterministic extension track scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _run_script(project_root: Path, script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(project_root / "scripts" / script), *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_write_belief_trajectory_gif_uses_trace_artifact(tmp_path: Path) -> None:
    from visualizations.animation import write_belief_trajectory_gif

    data = tmp_path / "output" / "data"
    data.mkdir(parents=True)
    (data / "si_graph_world_trace.json").write_text(
        json.dumps(
            {
                "steps": [
                    {"step": 0, "node": "start", "action": "observe", "belief_entropy": 1.0},
                    {"step": 1, "node": "goal", "action": "commit", "belief_entropy": 0.0},
                ]
            }
        ),
        encoding="utf-8",
    )
    out = write_belief_trajectory_gif(tmp_path)
    assert out.is_file()
    assert out.suffix == ".gif"


def test_simulate_si_graph_world_writes_deterministic_artifacts(project_root: Path) -> None:
    from simulation.graph_world import write_graph_world_stub

    out = write_graph_world_stub(project_root)
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload.get("status") == "ok"
    assert payload.get("goal_reached") is True

    result = _run_script(project_root, "simulate_si_graph_world.py")
    assert result.returncode == 0, result.stderr
    assert out.is_file()
    assert (project_root / "output" / "data" / "si_graph_world_trace.json").is_file()


def test_render_animation_skip_exits_clean(project_root: Path) -> None:
    result = _run_script(project_root, "render_animation.py", "--skip")
    assert result.returncode == 0, result.stderr
    assert "skipped" in result.stdout.lower()


def test_render_animation_writes_gif_when_si_figure_present(project_root: Path) -> None:
    from analysis import run_analysis
    from simulation.si_runner import pymdp_available, run_and_persist

    run_analysis(project_root)
    if not pymdp_available():
        pytest.skip("pymdp not installed")
    run_and_persist(project_root)
    gen = subprocess.run(
        [sys.executable, str(project_root / "scripts" / "generate_figures.py")],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert gen.returncode == 0, gen.stderr
    result = _run_script(project_root, "render_animation.py")
    assert result.returncode == 0, result.stderr
    gif = project_root / "output" / "figures" / "si_belief_trajectory.gif"
    assert gif.is_file()
    assert gif.stat().st_size > 100
