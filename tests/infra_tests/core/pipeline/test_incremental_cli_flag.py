"""PIPELINE-INCR-FLAG-1: ``--incremental`` CLI flag wiring.

These tests prove the opt-in incremental feature is reachable from the two
documented entrypoints (``scripts/runner/execute_pipeline.py`` and
``python -m infrastructure.orchestration pipeline``) and that
``PipelineConfig.incremental.enabled`` is ``True`` only when the flag is passed.

No mocks: the canonical entrypoints run real child processes twice and prove
that reuse occurs only when incremental execution is explicitly enabled.
"""

from __future__ import annotations

import pytest

import subprocess
import sys
from pathlib import Path

from infrastructure.core.pipeline.hitl_cli import PipelineArgs
from infrastructure.orchestration import build_parser
from infrastructure.orchestration.pipeline_runner import PipelineInvocation

REPO_ROOT = Path(__file__).resolve().parents[4]


def test_pipeline_args_default_incremental_is_false() -> None:
    assert PipelineArgs(project="demo").incremental is False


def test_pipeline_invocation_default_incremental_is_false() -> None:
    assert PipelineInvocation(project="demo").incremental is False


def test_orchestration_parser_incremental_absent_defaults_false() -> None:
    ns = build_parser().parse_args(["pipeline", "--project", "demo"])
    assert ns.incremental is False


def test_orchestration_parser_incremental_flag_sets_true() -> None:
    ns = build_parser().parse_args(["pipeline", "--project", "demo", "--incremental"])
    assert ns.incremental is True


@pytest.mark.parametrize("entrypoint", ["runner", "orchestration"])
@pytest.mark.parametrize("incremental", [False, True])
@pytest.mark.timeout(90)
def test_incremental_entrypoints_control_real_child_reuse(tmp_path: Path, entrypoint: str, incremental: bool) -> None:
    import io
    from scripts.runner.execute_pipeline import execute_pipeline
    from infrastructure.orchestration.pipeline_runner import PipelineRunner
    from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

    import yaml

    scaffold_pipeline(tmp_path)
    # Analysis is never content-cached (its producer runtime is always re-admitted),
    # so prove reuse through an ordinary cacheable project stage instead.
    definition = tmp_path / "infrastructure/core/pipeline/pipeline.yaml"
    declaration = yaml.safe_load(definition.read_text())
    for stage in declaration["stages"]:
        if stage["key"] == "analysis":
            stage.update(key="summary", name="Project Summary")
    definition.write_text(yaml.safe_dump(declaration))
    for _ in range(2):
        if entrypoint == "runner":
            code = execute_pipeline("demo", tmp_path, skip_infra=True, incremental=incremental)
        else:
            code = PipelineRunner(tmp_path, stream=io.StringIO()).run(
                PipelineInvocation("demo", skip_infra=True, incremental=incremental)
            )
        assert code == 0
    rows = (tmp_path / "process_order.log").read_text().splitlines()
    assert rows == ["demo:analysis"] * (1 if incremental else 2)
    cache = tmp_path / "projects/demo/output/.pipeline/incremental.json"
    assert cache.is_file() is incremental


def test_execute_pipeline_help_advertises_incremental() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/runner/execute_pipeline.py", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "--incremental" in result.stdout


def test_orchestration_pipeline_help_advertises_incremental() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "infrastructure.orchestration", "pipeline", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert "--incremental" in result.stdout
