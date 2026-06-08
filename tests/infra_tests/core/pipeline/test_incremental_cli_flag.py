"""PIPELINE-INCR-FLAG-1: ``--incremental`` CLI flag wiring.

These tests prove the opt-in incremental feature is reachable from the two
documented entrypoints (``scripts/execute_pipeline.py`` and
``python -m infrastructure.orchestration pipeline``) and that
``PipelineConfig.incremental.enabled`` is ``True`` only when the flag is passed.

No mocks: the executor stand-in is a real hand-written class that records the
config it receives; ``monkeypatch.setattr`` is plain attribute substitution,
not a mocking framework.
"""

from __future__ import annotations

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


def _capture_config(monkeypatch, *, incremental: bool):
    """Run ``execute_pipeline`` with a real capture-executor; return the config."""
    import scripts.execute_pipeline as ep

    captured: dict[str, object] = {}

    class _CaptureExecutor:
        def __init__(self, config: object) -> None:
            captured["config"] = config

        def execute_full_pipeline(self) -> list:
            return []

        def execute_core_pipeline(self) -> list:
            return []

    monkeypatch.setattr(ep, "PipelineExecutor", _CaptureExecutor)
    monkeypatch.setattr(ep, "validate_interpreter", lambda: None)
    monkeypatch.setattr(
        "infrastructure.core.pipeline.post_run_reporting.write_pipeline_post_run_reports",
        lambda **kwargs: None,
    )
    rc = ep.execute_pipeline(
        project_name="demo",
        repo_root=REPO_ROOT,
        incremental=incremental,
    )
    assert rc == 0
    return captured["config"]


def test_execute_pipeline_enables_incremental_only_with_flag(monkeypatch) -> None:
    enabled_cfg = _capture_config(monkeypatch, incremental=True)
    assert enabled_cfg.incremental.enabled is True


def test_execute_pipeline_incremental_disabled_by_default(monkeypatch) -> None:
    default_cfg = _capture_config(monkeypatch, incremental=False)
    assert default_cfg.incremental.enabled is False


def test_execute_pipeline_help_advertises_incremental() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/execute_pipeline.py", "--help"],
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
