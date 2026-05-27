"""Subprocess tests for opt-in extension track scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_script(project_root: Path, script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(project_root / "scripts" / script), *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )


def test_simulate_si_graph_world_writes_not_implemented_stub(project_root: Path) -> None:
    result = _run_script(project_root, "simulate_si_graph_world.py")
    assert result.returncode == 0, result.stderr
    out = project_root / "output" / "data" / "si_graph_world_summary.json"
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload.get("status") == "not_implemented"


def test_render_animation_skip_exits_clean(project_root: Path) -> None:
    result = _run_script(project_root, "render_animation.py", "--skip")
    assert result.returncode == 0, result.stderr
    assert "skipped" in result.stdout.lower()


def test_render_animation_writes_gif_when_si_figure_present(project_root: Path) -> None:
    from analysis import run_analysis

    run_analysis(project_root)
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
