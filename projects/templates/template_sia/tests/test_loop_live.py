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


def test_live_two_generations_writes_feedback_but_does_not_mutate_target(
    tmp_path: Path, copy_project_sandbox: Copy
):
    """Honest-stub invariant, pinned at the project layer too (offline, no Ollama).

    `improvement.md` is written for generation 2 with real prior-metric content,
    but the mirrored infra-level tripwire
    (`tests/infra_tests/sia/test_loop_runner.py::test_live_mode_does_not_mutate_target_code_across_generations`)
    is what actually enforces non-mutation; this test closes the matching gap at
    the project layer, which previously only asserted the improvement note was
    non-empty and never checked that generation 2's `target_agent.py` is the
    reference scaffold verbatim (i.e. that live mode cannot yet produce a real
    generation-over-generation code delta). See `infrastructure/sia/loop_runner.py`
    `_live_feedback` for why the copy stays unconditional today.
    """
    project = tmp_path / "proj"
    copy_project_sandbox(project)
    if (project / "output").exists():
        shutil.rmtree(project / "output")
    config = RunConfig(
        task_dir=project / "tasks" / "mini_classify",
        output_dir=project / "output",
        run_id=101,
        max_generations=2,
        live=True,
        fixtures_dir=None,
        target_timeout_sec=60,
        llm_model="",  # offline: deterministic stub feedback, no Ollama
    )
    artifacts = run_sia_loop(config)
    assert len(artifacts) == 2

    improvement = artifacts[1].improvement
    assert improvement is not None
    assert improvement.is_file()
    improvement_text = improvement.read_text(encoding="utf-8").strip()
    assert improvement_text
    assert "threshold" in improvement_text.lower()

    reference = (project / "tasks" / "mini_classify" / "reference" / "reference_target_agent.py").read_text(
        encoding="utf-8"
    )
    gen1_target = artifacts[0].target_agent.read_text(encoding="utf-8")
    gen2_target = artifacts[1].target_agent.read_text(encoding="utf-8")
    assert gen1_target == reference
    assert gen2_target == reference
    assert gen1_target == gen2_target, "live mode must not silently start mutating target code"


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
