#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.run_matrix.

No mocks: the executor's ``runner`` seam is exercised with a real recording
callable (dependency injection), and project resolution runs against a real
scaffolded project tree under ``tmp_path``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.pipeline.run_matrix import (
    RunConfig,
    RunConfigError,
    RunStep,
    execute_run_plan,
    find_run_config,
    format_report,
    parse_run_config,
    resolve_run_plan,
)
from tests._support.projects import make_project


# --------------------------------------------------------------------------- #
# parse_run_config (pure)
# --------------------------------------------------------------------------- #


def test_parse_minimal_config() -> None:
    cfg = parse_run_config(
        "version: 1\ndefaults:\n  stages: [setup, analysis]\nruns:\n  - project: templates/template_code_project\n"
    )
    assert cfg.default_stages == ("setup", "analysis")
    assert len(cfg.runs) == 1
    assert cfg.runs[0].project == "templates/template_code_project"
    assert cfg.runs[0].stages == ()


def test_parse_per_run_stage_override() -> None:
    cfg = parse_run_config("runs:\n  - project: x\n    stages: [render_pdf, validate]\n")
    assert cfg.runs[0].stages == ("render_pdf", "validate")


def test_parse_normalizes_stage_case_and_whitespace() -> None:
    cfg = parse_run_config("runs:\n  - project: x\n    stages: ['  Render_PDF ', 'ANALYSIS']\n")
    assert cfg.runs[0].stages == ("render_pdf", "analysis")


def test_parse_rejects_empty() -> None:
    with pytest.raises(RunConfigError, match="empty"):
        parse_run_config("")


def test_parse_rejects_non_mapping_top_level() -> None:
    with pytest.raises(RunConfigError, match="mapping at the top level"):
        parse_run_config("- just\n- a\n- list\n")


def test_parse_rejects_missing_runs() -> None:
    with pytest.raises(RunConfigError, match="non-empty 'runs'"):
        parse_run_config("defaults:\n  stages: [setup]\n")


def test_parse_rejects_run_without_project() -> None:
    with pytest.raises(RunConfigError, match="'project' must be a non-empty string"):
        parse_run_config("runs:\n  - stages: [setup]\n")


def test_parse_rejects_non_list_stages() -> None:
    with pytest.raises(RunConfigError, match="'stages' must be a list"):
        parse_run_config("runs:\n  - project: x\n    stages: setup\n")


def test_parse_rejects_bad_yaml() -> None:
    with pytest.raises(RunConfigError, match="not valid YAML"):
        parse_run_config("runs: [unbalanced\n")


# --------------------------------------------------------------------------- #
# resolve_run_plan (real project tree)
# --------------------------------------------------------------------------- #


def _scaffold(root: Path) -> None:
    make_project(root, "template_code_project", program="templates")
    make_project(root, "template_prose_project", program="templates")


def test_resolve_orders_stages_canonically(tmp_path: Path) -> None:
    """Stages run in canonical pipeline order regardless of listing order."""
    _scaffold(tmp_path)
    cfg = parse_run_config(
        "runs:\n  - project: templates/template_code_project\n    stages: [render_pdf, analysis, setup]\n"
    )
    plan = resolve_run_plan(cfg, tmp_path)
    stages = [s.stage for s in plan.steps]
    assert stages == ["setup", "analysis", "render_pdf"]  # not the listed order


def test_resolve_dedupes_stages(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    cfg = parse_run_config(
        "runs:\n  - project: templates/template_code_project\n    stages: [analysis, analysis, render_pdf]\n"
    )
    plan = resolve_run_plan(cfg, tmp_path)
    assert [s.stage for s in plan.steps] == ["analysis", "render_pdf"]


def test_resolve_uses_default_stages_when_run_omits_them(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    cfg = parse_run_config("defaults:\n  stages: [setup, copy]\nruns:\n  - project: templates/template_code_project\n")
    plan = resolve_run_plan(cfg, tmp_path)
    assert [s.stage for s in plan.steps] == ["setup", "copy"]


def test_resolve_bare_name_to_qualified(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    cfg = parse_run_config("runs:\n  - project: template_code_project\n    stages: [setup]\n")
    plan = resolve_run_plan(cfg, tmp_path)
    assert plan.steps[0].project == "templates/template_code_project"


def test_resolve_rejects_unknown_project(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    cfg = parse_run_config("runs:\n  - project: nonexistent_project\n    stages: [setup]\n")
    with pytest.raises(RunConfigError, match="not found"):
        resolve_run_plan(cfg, tmp_path)


def test_resolve_rejects_path_traversal(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    cfg = parse_run_config("runs:\n  - project: ../etc/passwd\n    stages: [setup]\n")
    with pytest.raises(RunConfigError, match=r"\.\."):
        resolve_run_plan(cfg, tmp_path)


def test_resolve_rejects_unknown_stage(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    cfg = parse_run_config("runs:\n  - project: templates/template_code_project\n    stages: [not_a_stage]\n")
    with pytest.raises(RunConfigError, match="unknown stage"):
        resolve_run_plan(cfg, tmp_path)


def test_resolve_rejects_no_stages_no_defaults(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    cfg = parse_run_config("runs:\n  - project: templates/template_code_project\n")
    with pytest.raises(RunConfigError, match="no stages and no 'defaults"):
        resolve_run_plan(cfg, tmp_path)


# --------------------------------------------------------------------------- #
# execute_run_plan (injected real recording runner — no mocks)
# --------------------------------------------------------------------------- #


class _RecordingRunner:
    """A real callable that records calls and returns scripted exit codes."""

    def __init__(self, codes: dict[tuple[str, str], int] | None = None) -> None:
        self.calls: list[tuple[str, str]] = []
        self._codes = codes or {}

    def __call__(self, stage: str, project: str, repo_root: Path) -> int:
        self.calls.append((stage, project))
        return self._codes.get((stage, project), 0)


def _plan(*steps: tuple[str, str]) -> "object":
    from infrastructure.core.pipeline.run_matrix import RunPlan

    return RunPlan(steps=tuple(RunStep(project=p, stage=s) for p, s in steps))


def test_execute_runs_every_step_in_order(tmp_path: Path) -> None:
    runner = _RecordingRunner()
    plan = _plan(("proj", "setup"), ("proj", "analysis"))
    results = execute_run_plan(plan, tmp_path, runner=runner)
    assert runner.calls == [("setup", "proj"), ("analysis", "proj")]
    assert all(r.ok for r in results)


def test_execute_fail_fast_skips_remaining(tmp_path: Path) -> None:
    runner = _RecordingRunner({("analysis", "proj"): 1})
    plan = _plan(("proj", "setup"), ("proj", "analysis"), ("proj", "render_pdf"))
    results = execute_run_plan(plan, tmp_path, fail_fast=True, runner=runner)
    assert runner.calls == [("setup", "proj"), ("analysis", "proj")]  # render_pdf never ran
    assert results[0].ok and not results[1].ok and results[2].skipped


def test_execute_continue_on_failure_runs_all(tmp_path: Path) -> None:
    runner = _RecordingRunner({("setup", "proj"): 1})
    plan = _plan(("proj", "setup"), ("proj", "analysis"))
    results = execute_run_plan(plan, tmp_path, fail_fast=False, runner=runner)
    assert len(runner.calls) == 2  # both ran despite the first failure
    assert not results[0].ok and results[1].ok


def test_format_report_marks_failures_and_skips(tmp_path: Path) -> None:
    runner = _RecordingRunner({("analysis", "proj"): 2})
    plan = _plan(("proj", "setup"), ("proj", "analysis"), ("proj", "render_pdf"))
    results = execute_run_plan(plan, tmp_path, fail_fast=True, runner=runner)
    report = format_report(results)
    assert "setup" in report and "ok" in report
    assert "FAIL(2)" in report
    assert "SKIP" in report
    assert "1 failed" in report


# --------------------------------------------------------------------------- #
# find_run_config
# --------------------------------------------------------------------------- #


def test_find_run_config_prefers_run_config(tmp_path: Path) -> None:
    (tmp_path / "run.config").write_text("runs:\n  - project: x\n", encoding="utf-8")
    (tmp_path / "run.config.yaml").write_text("runs:\n  - project: y\n", encoding="utf-8")
    assert find_run_config(tmp_path) == tmp_path / "run.config"


def test_find_run_config_none_when_absent(tmp_path: Path) -> None:
    assert find_run_config(tmp_path) is None


def test_runconfig_dataclass_is_constructible() -> None:
    cfg = RunConfig(default_stages=("setup",), runs=())
    assert cfg.default_stages == ("setup",)


def test_shipped_example_config_parses_and_uses_valid_stages() -> None:
    """run.config.example.yaml must stay parseable with valid stage names.

    Resolution against the live project tree is exercised elsewhere; here we
    guard the shipped template against syntax / stage-vocabulary drift.
    """
    repo_root = Path(__file__).resolve().parents[4]
    example = repo_root / "run.config.example.yaml"
    assert example.is_file(), f"missing {example}"
    cfg = parse_run_config(example.read_text(encoding="utf-8"))
    assert cfg.runs, "example must declare at least one run"
    from infrastructure.core.pipeline.stage_registry import known_stage_keys

    valid = known_stage_keys()
    all_stages = set(cfg.default_stages)
    for entry in cfg.runs:
        all_stages.update(entry.stages)
    unknown = all_stages - valid
    assert not unknown, f"example references unknown stages: {unknown}"
