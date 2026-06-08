"""Live SIA loop tests (opt-in)."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

import pytest

from infrastructure.sia import RunConfig, run_sia_loop

PROJECT_ROOT = Path(__file__).resolve().parent.parent

Copy = Callable[[Path], Path]


def test_live_single_generation(tmp_path: Path, copy_project_sandbox: Copy):
    """Live mode runs reference agent and evaluates without fixtures."""
    project = tmp_path / "proj"
    copy_project_sandbox(project)
    if (project / "output").exists():
        shutil.rmtree(project / "output")
    config = RunConfig(
        task_dir=project / "tasks" / "mini_classify",
        output_dir=project / "output",
        run_id=99,
        max_generations=1,
        live=True,
        fixtures_dir=None,
        target_timeout_sec=60,
        llm_model="",
    )
    artifacts = run_sia_loop(config)
    assert len(artifacts) == 1
    assert artifacts[0].evaluation is not None
    assert artifacts[0].evaluation.metric_name == "accuracy"
    assert artifacts[0].evaluation.n_samples == 6


@pytest.mark.requires_ollama
def test_live_feedback_with_ollama(tmp_path: Path, copy_project_sandbox: Copy):
    """Two live generations; feedback may use Ollama when configured."""
    project = tmp_path / "proj"
    copy_project_sandbox(project)
    if (project / "output").exists():
        shutil.rmtree(project / "output")
    config = RunConfig(
        task_dir=project / "tasks" / "mini_classify",
        output_dir=project / "output",
        run_id=100,
        max_generations=2,
        live=True,
        fixtures_dir=None,
        target_timeout_sec=60,
        llm_model="gemma3:4b",
    )
    artifacts = run_sia_loop(config)
    assert len(artifacts) == 2
    improvement = artifacts[1].improvement
    assert improvement is not None
    assert improvement.is_file()
    assert improvement.read_text(encoding="utf-8").strip()
