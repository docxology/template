#!/usr/bin/env python3
"""Tests for infrastructure.core.pipeline.run_matrix.

No mocks: selected stages execute real child processes against scaffolded
project trees under ``tmp_path``.
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import replace
import os
import time

import pytest

from infrastructure.core.pipeline.run_matrix import (
    RunConfig,
    RunConfigError,
    execute_run_plan,
    find_run_config,
    format_report,
    parse_run_config,
    resolve_run_plan,
)


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


def test_parse_explicit_resume_and_whole_matrix_budget() -> None:
    cfg = parse_run_config("resume: true\nrun_timeout_seconds: 90\nruns:\n  - project: x\n    stages: [render_pdf]\n")
    assert cfg.resume is True and cfg.run_timeout_seconds == 90


@pytest.mark.parametrize("policy", ["resume: 'true'", "run_timeout_seconds: 0", "run_timeout_seconds: .inf"])
def test_parse_rejects_invalid_execution_policy(policy: str) -> None:
    with pytest.raises(RunConfigError):
        parse_run_config(policy + "\nruns:\n  - project: x\n    stages: [render_pdf]\n")


@pytest.mark.parametrize("stage", ["  Render_PDF ", "ANALYSIS", "render/pdf", ""])
def test_parse_rejects_unstable_stage_keys(stage: str) -> None:
    with pytest.raises(RunConfigError, match="stable lowercase key"):
        parse_run_config(f"runs:\n  - project: x\n    stages: ['{stage}']\n")


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
    import yaml
    from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

    scaffold_pipeline(root, ("templates/template_code_project", "templates/template_prose_project"))
    path = root / "infrastructure/core/pipeline/pipeline.yaml"
    payload = yaml.safe_load(path.read_text())
    analysis = next(stage for stage in payload["stages"] if stage["key"] == "analysis")
    stages = []
    for key in ("setup", "analysis", "render_pdf", "copy"):
        stages.append({**analysis, "name": key.replace("_", " ").title(), "key": key, "args": [key]})
    payload["stages"] = stages
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")


def test_resolve_orders_stages_canonically(tmp_path: Path) -> None:
    """Stages run in canonical pipeline order regardless of listing order."""
    _scaffold(tmp_path)
    cfg = parse_run_config(
        "runs:\n  - project: templates/template_code_project\n    stages: [render_pdf, analysis, setup]\n"
    )
    plan = resolve_run_plan(cfg, tmp_path)
    stages = [s.stage for s in plan.steps]
    assert stages == ["setup", "analysis", "render_pdf"]  # not the listed order


def test_parse_rejects_duplicate_stage_keys() -> None:
    with pytest.raises(RunConfigError, match="duplicate stage"):
        parse_run_config("runs:\n  - project: x\n    stages: [analysis, analysis, render_pdf]\n")


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
    with pytest.raises(RunConfigError, match="Unknown stage"):
        resolve_run_plan(cfg, tmp_path)


def test_resolve_rejects_no_stages_no_defaults(tmp_path: Path) -> None:
    _scaffold(tmp_path)
    cfg = parse_run_config("runs:\n  - project: templates/template_code_project\n")
    with pytest.raises(RunConfigError, match="no stages and no 'defaults"):
        resolve_run_plan(cfg, tmp_path)


# --------------------------------------------------------------------------- #
# execute_run_plan (canonical executor and real children)
# --------------------------------------------------------------------------- #


def test_execute_runs_real_selected_stages_in_order(tmp_path: Path) -> None:
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code

    _scaffold(tmp_path)
    config = parse_run_config(
        "runs:\n  - project: templates/template_code_project\n    stages: [render_pdf, analysis]\n"
    )
    plan = resolve_run_plan(config, tmp_path)
    results = execute_run_plan(plan, tmp_path)
    assert run_plan_exit_code(plan, results) == 0
    assert [result.stage for result in results] == ["analysis", "render_pdf"]
    assert (tmp_path / "process_order.log").read_text().splitlines() == [
        "templates/template_code_project:analysis",
        "templates/template_code_project:render_pdf",
    ]


def test_fail_fast_aborts_remaining_project_without_success(tmp_path: Path) -> None:
    from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code

    scaffold_pipeline(tmp_path, ("fail", "other"))
    plan = resolve_run_plan(
        parse_run_config(
            "runs:\n  - project: fail\n    stages: [analysis]\n  - project: other\n    stages: [analysis]\n"
        ),
        tmp_path,
    )
    results = execute_run_plan(plan, tmp_path, fail_fast=True)
    assert run_plan_exit_code(plan, results) == 1
    assert results[1].skipped and not results[1].ok
    assert (tmp_path / "process_order.log").read_text().splitlines() == ["fail:analysis"]
    assert "ABORTED" in format_report(results)


def test_continue_after_failure_runs_next_project(tmp_path: Path) -> None:
    from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code

    scaffold_pipeline(tmp_path, ("fail", "other"))
    plan = resolve_run_plan(
        parse_run_config(
            "runs:\n  - project: fail\n    stages: [analysis]\n  - project: other\n    stages: [analysis]\n"
        ),
        tmp_path,
    )
    results = execute_run_plan(plan, tmp_path)
    assert run_plan_exit_code(plan, results) == 1
    assert not results[0].ok and results[1].ok
    assert (tmp_path / "process_order.log").read_text().splitlines() == ["fail:analysis", "other:analysis"]


def _shared_matrix(root: Path, *, infra_exit: int = 0, resume: bool = False):
    import yaml
    from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

    scaffold_pipeline(root, ("first", "second"), infra_exit=infra_exit)
    source = root / "infrastructure/core/pipeline/pipeline.yaml"
    definition = yaml.safe_load(source.read_text())
    child = next(stage for stage in definition["stages"] if stage["key"] == "analysis")
    child.update(name="Project child", key="child", args=["child"], depends_on=["Infrastructure Tests"])
    child["contract"]["output_artifacts"] = ["projects/{project}/output/data/child.json"]
    definition["stages"] = [stage for stage in definition["stages"] if stage["key"] != "llm_reviews"]
    source.write_text(yaml.safe_dump(definition))
    return parse_run_config(
        f"resume: {str(resume).lower()}\nrun_timeout_seconds: 90\ndefaults:\n  stages: [infra_tests, child]\n"
        "runs:\n  - project: first\n  - project: second\n"
    )


@pytest.mark.timeout(180)
def test_matrix_shared_gate_executes_once_before_both_actual_project_children(tmp_path: Path) -> None:
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code

    plan = resolve_run_plan(_shared_matrix(tmp_path), tmp_path)
    assert [(step.project, step.stage) for step in plan.steps] == [
        ("root", "infra_tests"),
        ("first", "child"),
        ("second", "child"),
    ]
    assert all(item.expected_stage_keys == ("child",) for item in plan.execution_plans)
    results = execute_run_plan(plan, tmp_path)
    assert run_plan_exit_code(plan, results) == 0
    assert results[0].shared_result is not None and results[0].shared_result.exit_code == 0
    assert (tmp_path / "process_order.log").read_text().splitlines() == ["first:infra", "first:child", "second:child"]


@pytest.mark.timeout(180)
@pytest.mark.parametrize("fail_fast", [False, True])
def test_matrix_failed_shared_gate_prevents_every_project_even_without_fail_fast(
    tmp_path: Path, fail_fast: bool
) -> None:
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code
    from infrastructure.core.pipeline.outcomes import StageStatus

    plan = resolve_run_plan(_shared_matrix(tmp_path, infra_exit=7), tmp_path)
    results = execute_run_plan(plan, tmp_path, fail_fast=fail_fast)
    assert run_plan_exit_code(plan, results) == 1
    assert results[0].outcome.child_exit_code == 7
    assert all(result.outcome.status is StageStatus.ABORTED for result in results[1:])
    assert not any(result.ok for result in results)
    assert (tmp_path / "process_order.log").read_text().splitlines() == ["first:infra"]
    assert not any((tmp_path / "projects" / name / "output/data/child.json").exists() for name in ("first", "second"))


@pytest.mark.timeout(180)
def test_matrix_explicit_project_only_selection_does_not_admit_shared_execution(tmp_path: Path) -> None:
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code

    cfg = _shared_matrix(tmp_path, infra_exit=7)
    cfg = replace(cfg, default_stages=("child",))
    plan = resolve_run_plan(cfg, tmp_path)
    assert plan.shared_infrastructure is None
    results = execute_run_plan(plan, tmp_path)
    assert run_plan_exit_code(plan, results) == 0
    assert (tmp_path / "process_order.log").read_text().splitlines() == ["first:child", "second:child"]


@pytest.mark.timeout(180)
def test_matrix_infrastructure_only_selection_executes_one_shared_contract(tmp_path: Path) -> None:
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code

    cfg = replace(_shared_matrix(tmp_path), default_stages=("infra_tests",))
    plan = resolve_run_plan(cfg, tmp_path)
    assert not plan.execution_plans and len(plan.steps) == 1
    results = execute_run_plan(plan, tmp_path)
    assert run_plan_exit_code(plan, results) == 0
    assert (tmp_path / "process_order.log").read_text().splitlines() == ["first:infra"]


@pytest.mark.timeout(240)
def test_matrix_preserves_each_effective_project_dag_after_shared_verification(tmp_path: Path) -> None:
    import yaml
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code

    cfg = _shared_matrix(tmp_path)
    source = yaml.safe_load((tmp_path / "infrastructure/core/pipeline/pipeline.yaml").read_text())
    infra, child = source["stages"]
    for project, first, second in (("first", "alpha", "beta"), ("second", "beta", "alpha")):
        stages = [infra]
        for key, dependency in ((first, "Infrastructure Tests"), (second, first.title())):
            contract = {**child["contract"], "output_artifacts": [f"projects/{{project}}/output/data/{key}.json"]}
            stages.append(
                {
                    **child,
                    "name": key.title(),
                    "key": key,
                    "args": [key],
                    "depends_on": [dependency],
                    "contract": contract,
                }
            )
        (tmp_path / "projects" / project / "pipeline.yaml").write_text(yaml.safe_dump({**source, "stages": stages}))
    plan = resolve_run_plan(
        replace(cfg, default_stages=("infra_tests", "beta", "alpha"), run_timeout_seconds=180), tmp_path
    )
    assert [item.expected_stage_keys for item in plan.execution_plans] == [("alpha", "beta"), ("beta", "alpha")]
    results = execute_run_plan(plan, tmp_path)
    assert run_plan_exit_code(plan, results) == 0
    assert plan.deadline_monotonic is not None
    assert time.monotonic() <= plan.deadline_monotonic + 15
    assert (tmp_path / "process_order.log").read_text().splitlines() == [
        "first:infra",
        "first:alpha",
        "first:beta",
        "second:beta",
        "second:alpha",
    ]
    # The same-process serial matrix must close each project's owned log sinks.
    for project, other, own_order, other_order in (
        ("first", "second", ("Alpha", "Beta"), ("Beta", "Alpha")),
        ("second", "first", ("Beta", "Alpha"), ("Alpha", "Beta")),
    ):
        log = tmp_path / "projects" / project / "output/logs/pipeline.log"
        other_log = tmp_path / "projects" / other / "output/logs/pipeline.log"
        content = log.read_text(encoding="utf-8")
        assert content.count(f"Set up log file handler: {log}") == 1
        assert str(other_log) not in content
        for number, stage in enumerate(own_order, start=1):
            assert content.count(f"[{number}/2] {stage} (") == 1
        for number, stage in enumerate(other_order, start=1):
            assert f"[{number}/2] {stage} (" not in content


def test_matrix_refuses_project_shared_override_before_any_execution(tmp_path: Path) -> None:
    import yaml

    cfg = _shared_matrix(tmp_path)
    definition = yaml.safe_load((tmp_path / "infrastructure/core/pipeline/pipeline.yaml").read_text())
    definition["stages"][0]["args"] = ["distinct-project-infrastructure"]
    (tmp_path / "projects/second/pipeline.yaml").write_text(yaml.safe_dump(definition))
    with pytest.raises(RunConfigError, match="canonical once-only gate"):
        resolve_run_plan(cfg, tmp_path)
    assert not (tmp_path / "process_order.log").exists()


@pytest.mark.timeout(240)
def test_matrix_resume_keeps_fresh_shared_gate_and_reuses_exact_project_checkpoints(tmp_path: Path) -> None:
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code
    from infrastructure.core.pipeline.outcomes import StageStatus

    cfg = _shared_matrix(tmp_path)
    first_plan = resolve_run_plan(cfg, tmp_path)
    first = execute_run_plan(first_plan, tmp_path)
    assert run_plan_exit_code(first_plan, first) == 0
    resumed_plan = resolve_run_plan(replace(cfg, resume=True), tmp_path)
    resumed = execute_run_plan(resumed_plan, tmp_path)
    assert run_plan_exit_code(resumed_plan, resumed) == 0
    assert resumed[0].outcome.status is StageStatus.SUCCEEDED
    assert all(result.outcome.status is StageStatus.CACHED for result in resumed[1:])
    assert (tmp_path / "process_order.log").read_text().splitlines() == [
        "first:infra",
        "first:child",
        "second:child",
        "first:infra",
    ]


@pytest.mark.timeout(180)
def test_matrix_resume_without_exact_checkpoints_is_pending_and_never_starts_projects(tmp_path: Path) -> None:
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code
    from infrastructure.core.pipeline.outcomes import StageStatus

    plan = resolve_run_plan(_shared_matrix(tmp_path, resume=True), tmp_path)
    results = execute_run_plan(plan, tmp_path)
    assert run_plan_exit_code(plan, results) == 75
    assert results[0].ok
    assert all(result.outcome.status is StageStatus.BLOCKED for result in results[1:])
    assert (tmp_path / "process_order.log").read_text().splitlines() == ["first:infra"]


@pytest.mark.timeout(90)
def test_matrix_original_deadline_stops_current_and_later_projects(tmp_path: Path) -> None:
    """An exhausted shared budget prevents every project from entering."""
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code
    from infrastructure.core.pipeline.outcomes import StageStatus

    cfg = _shared_matrix(tmp_path)
    script = tmp_path / "scripts/stage.py"
    source = script.read_text().replace(
        "if step == 'infra': sys.exit(0)",
        "if step == 'infra':\n    import time\n    time.sleep(60)\n    sys.exit(0)",
    )
    source = source.replace(
        "if project.endswith('fail'):",
        "if step == 'child':\n    import time\n    time.sleep(60)\nif project.endswith('fail'):",
    )
    script.write_text(source)
    plan = resolve_run_plan(replace(cfg, run_timeout_seconds=20), tmp_path)
    results = execute_run_plan(plan, tmp_path)
    assert run_plan_exit_code(plan, results) == 124
    assert plan.deadline_monotonic is not None
    assert time.monotonic() <= plan.deadline_monotonic + 15  # Finite, healthy supervisor cleanup allowance.
    order = tmp_path / "process_order.log"
    observed = order.read_text().splitlines() if order.exists() else []
    assert observed in ([], ["first:infra"])
    shared = results[0].shared_result
    assert shared is not None and shared.exit_code == 124
    shared_run = shared.validated_run()
    assert shared_run is not None and shared_run.exit_code == 124 and not shared_run.complete
    assert shared_run.expected_stage_keys == ("infra_tests",)
    assert any(outcome.status is StageStatus.TIMED_OUT for outcome in shared_run.outcomes)
    assert [result.project for result in results[1:]] == ["first", "second"]
    assert all(result.outcome.status is StageStatus.ABORTED for result in results[1:])
    assert all(result.outcome.child_exit_code is None for result in results[1:])
    assert not any((tmp_path / "projects" / name / "output/data/child.json").exists() for name in ("first", "second"))


@pytest.mark.timeout(180)
@pytest.mark.skipif(os.name != "posix", reason="POSIX detached descendant cleanup")
def test_matrix_original_deadline_kills_started_child_and_detached_descendant(tmp_path: Path) -> None:
    """The original deadline includes shared work and kills actual project processes."""
    import contextlib
    import json

    import psutil
    import yaml

    from infrastructure.core.pipeline.outcomes import StageStatus
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code
    from tests.helpers.owned_process import assert_process_exited

    budget, shared_delay, cleanup_allowance = 90, 20, 15
    cfg = _shared_matrix(tmp_path)
    declaration = tmp_path / "infrastructure/core/pipeline/pipeline.yaml"
    payload = yaml.safe_load(declaration.read_text())
    payload["control"] = {"stage_policies": {1: {"timeout_seconds": 180}, 2: {"timeout_seconds": 180}}}
    declaration.write_text(yaml.safe_dump(payload))
    script = tmp_path / "scripts/stage.py"
    source = script.read_text().replace(
        "if step == 'infra': sys.exit(0)",
        f"if step == 'infra':\n    import time\n    time.sleep({shared_delay})\n    sys.exit(0)",
    )
    source = source.replace(
        "if project.endswith('fail'):",
        "if step == 'child':\n"
        "    import subprocess, time, psutil\n"
        '    program = "import json, os, time; from pathlib import Path; '
        "Path('detached_process.json.part').write_text(json.dumps({'pid': os.getpid(), "
        "'entered_monotonic': time.monotonic()})); "
        "Path('detached_process.json.part').replace('detached_process.json'); time.sleep(180)\"\n"
        "    child = subprocess.Popen([sys.executable, '-I', '-c', program], "
        "start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
        "    Path('spawned_processes.json.part').write_text(json.dumps({\n"
        "        'stage_pid': os.getpid(), 'stage_birth': psutil.Process().create_time(),\n"
        "        'descendant_pid': child.pid, 'descendant_birth': psutil.Process(child.pid).create_time()}))\n"
        "    Path('spawned_processes.json.part').replace('spawned_processes.json')\n"
        "    ready_deadline = time.monotonic() + 5\n"
        "    while not Path('detached_process.json').exists():\n"
        "        if time.monotonic() >= ready_deadline or child.poll() is not None:\n"
        "            raise RuntimeError('Detached child did not enter')\n"
        "        time.sleep(.01)\n"
        "    detached = json.loads(Path('detached_process.json').read_text())\n"
        "    assert detached['pid'] == child.pid\n"
        "    Path('first_child_entry.json').write_text(json.dumps({\n"
        "        'stage_pid': os.getpid(), 'stage_birth': psutil.Process().create_time(),\n"
        "        'descendant_pid': child.pid, 'descendant_birth': psutil.Process(child.pid).create_time(),\n"
        "        'entered_monotonic': time.monotonic()}))\n"
        "    time.sleep(180)\n"
        "if project.endswith('fail'):",
    )
    script.write_text(source)
    plan = resolve_run_plan(replace(cfg, run_timeout_seconds=budget), tmp_path)
    assert plan.deadline_monotonic is not None
    assert all(
        stage.policy.timeout_seconds > budget for selection in plan.execution_plans for stage in selection.stages
    )
    marker = tmp_path / "first_child_entry.json"
    cleanup_marker = tmp_path / "spawned_processes.json"
    try:
        results = execute_run_plan(plan, tmp_path)
        finished = time.monotonic()
        assert run_plan_exit_code(plan, results) == 124
        assert results[0].ok  # The genuine shared gate finished before project execution.
        assert marker.exists(), "First project child must really enter for this timeout experiment"
        entry = json.loads(marker.read_text())
        # Shared work exceeds cleanup allowance, so resetting a project/stage
        # budget cannot satisfy this original-deadline bound, even on a fast host.
        assert plan.deadline_monotonic - budget + shared_delay <= entry["entered_monotonic"] < plan.deadline_monotonic
        assert finished <= plan.deadline_monotonic + cleanup_allowance
        first = next(result for result in results if result.project == "first")
        assert first.outcome.status is StageStatus.TIMED_OUT
        assert first.outcome.child_exit_code is not None
        assert all(result.outcome.status is StageStatus.TIMED_OUT for result in results if result.project == "second")
        assert all(result.outcome.child_exit_code is None for result in results if result.project == "second")
        assert (tmp_path / "process_order.log").read_text().splitlines() == ["first:infra", "first:child"]
        assert not any(
            (tmp_path / "projects" / name / "output/data/child.json").exists() for name in ("first", "second")
        )
        assert entry["stage_pid"] != entry["descendant_pid"]
        # Absent or an unreapable zombie: hosts whose PID 1 never reaps orphans
        # keep a killed detached descendant's process-table entry.
        assert_process_exited(entry["stage_pid"])
        assert_process_exited(entry["descendant_pid"])
    finally:
        # A failing negative control must not leave its owned sleeping processes.
        # This cleanup runs only after the assertions and cannot grant a pass.
        if cleanup_marker.exists():
            spawned = json.loads(cleanup_marker.read_text())
            for kind in ("descendant", "stage"):
                with contextlib.suppress(psutil.Error):
                    process = psutil.Process(spawned[f"{kind}_pid"])
                    if process.create_time() == spawned[f"{kind}_birth"]:
                        process.kill()
                        process.wait(timeout=5)


@pytest.mark.timeout(180)
def test_matrix_targeted_selection_validates_prerequisites_without_running_other_stages(tmp_path: Path) -> None:
    import yaml
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code
    from infrastructure.core.pipeline.outcomes import StageStatus

    cfg = _shared_matrix(tmp_path)
    source = tmp_path / "infrastructure/core/pipeline/pipeline.yaml"
    definition = yaml.safe_load(source.read_text())
    definition["stages"][1]["contract"]["input_artifacts"] = ["projects/{project}/output/data/required.json"]
    source.write_text(yaml.safe_dump(definition))
    plan = resolve_run_plan(replace(cfg, default_stages=("child",)), tmp_path)
    results = execute_run_plan(plan, tmp_path)
    assert run_plan_exit_code(plan, results) == 75
    assert all(result.outcome.status is StageStatus.BLOCKED for result in results)
    assert all("Required input artifact is missing" in result.outcome.diagnostic for result in results)
    assert all(result.outcome.child_exit_code is None for result in results)
    assert not (tmp_path / "process_order.log").exists()


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


def test_matrix_pause_preserves_pending_exit_for_unexecuted_dependencies(tmp_path: Path) -> None:
    import yaml
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code
    from infrastructure.core.pipeline.outcomes import StageStatus

    _scaffold(tmp_path)
    source = tmp_path / "infrastructure/core/pipeline/pipeline.yaml"
    payload = yaml.safe_load(source.read_text())
    payload["control"] = {"hitl_mode": "checkpoint"}
    source.write_text(yaml.safe_dump(payload))
    plan = resolve_run_plan(
        parse_run_config("runs:\n  - project: templates/template_code_project\n    stages: [analysis, render_pdf]\n"),
        tmp_path,
    )
    results = execute_run_plan(plan, tmp_path, fail_fast=True)
    assert run_plan_exit_code(plan, results) == 75
    assert results[0].outcome.status is StageStatus.PAUSED
    assert results[1].outcome.status is StageStatus.BLOCKED
    assert not any(result.ok for result in results)


@pytest.mark.timeout(150)
def test_matrix_report_refusal_retains_successful_children_and_fails_run(tmp_path: Path) -> None:
    """A real final-report refusal cannot disappear during matrix projection."""
    from infrastructure.core.pipeline.run_matrix import run_plan_exit_code
    from infrastructure.core.pipeline.outcomes import StageStatus

    _scaffold(tmp_path)
    plan = resolve_run_plan(
        parse_run_config("runs:\n  - project: templates/template_code_project\n    stages: [analysis, render_pdf]\n"),
        tmp_path,
    )
    plan.execution_plans = tuple(replace(selection, run_timeout_seconds=90) for selection in plan.execution_plans)
    output = tmp_path / "projects/templates/template_code_project/output"
    sentinel = tmp_path / "external-report.json"
    sentinel.write_text("Unapproved external report must remain intact.\n")
    receipt = output / ".pipeline/report_finalization.json"
    receipt.parent.mkdir(parents=True)
    receipt.symlink_to(sentinel)

    results = execute_run_plan(plan, tmp_path)

    assert run_plan_exit_code(plan, results) == 1
    assert all(result.outcome is not None and result.outcome.complete for result in results)
    assert all(result.outcome.child_exit_code == 0 for result in results)
    assert results[0].ok and not results[-1].ok
    assert results[-1].run_result is not None and results[-1].run_result.exit_code == 1
    failure = results[-1].run_result.outcomes[-1]
    assert failure.stage_key == "report_finalization" and failure.status is StageStatus.FAILED
    assert failure.child_exit_code == 1 and failure.diagnostic
    report = format_report(results)
    assert "FAILED" in report and "report_finalization:" in report
    assert sentinel.read_text() == "Unapproved external report must remain intact.\n"
    assert (tmp_path / "process_order.log").read_text().splitlines() == [
        "templates/template_code_project:analysis",
        "templates/template_code_project:render_pdf",
    ]


@pytest.mark.timeout(150)
@pytest.mark.parametrize("refusal", ["source", "deadline"])
def test_matrix_retains_actual_post_stage_custody_and_deadline_outcomes(tmp_path: Path, refusal: str) -> None:
    """Project rows retain genuine successful children and later completion guards."""
    from infrastructure.core.pipeline.executor import PipelineExecutor
    from infrastructure.core.pipeline.types import PipelineConfig
    from infrastructure.core.pipeline.outcomes import StageStatus
    from infrastructure.core.pipeline.report_finalization import finalize_execution_reports
    from infrastructure.core.pipeline.run_matrix import _project_steps, run_plan_exit_code

    _scaffold(tmp_path)
    plan = resolve_run_plan(
        parse_run_config("runs:\n  - project: templates/template_code_project\n    stages: [analysis]\n"), tmp_path
    )
    selection = replace(plan.execution_plans[0], run_timeout_seconds=90)
    plan.execution_plans = (selection,)
    executor = PipelineExecutor(PipelineConfig(selection.project, tmp_path, mode=selection.mode, clean=False))
    actual = executor.execute_plan(selection)
    assert executor.run_result(actual).complete
    receipt = executor.config.project_dir / "output/.pipeline/report_finalization.json"
    original_receipt = receipt.read_bytes()
    if refusal == "source":
        (executor.config.project_dir / "src/new_model.py").write_text("SCIENTIFIC_CHANGE = 1\n")
        state, expected_code = StageStatus.BLOCKED, 75
    else:
        executor._run_deadline = time.monotonic() - 1
        state, expected_code = StageStatus.TIMED_OUT, 124
    refused = finalize_execution_reports(executor, actual)
    run = executor.run_result(refused)
    assert run.exit_code == expected_code

    results = _project_steps(selection, run, StageStatus.ABORTED)

    assert run_plan_exit_code(plan, results) == expected_code
    assert results[0].outcome is actual[0].outcome
    assert results[0].outcome is not None and results[0].outcome.child_exit_code == 0
    assert results[0].outcome.complete and not results[0].ok
    assert results[0].run_result is run
    guard = results[0].run_result.outcomes[-1]
    assert guard.status is state and guard.child_exit_code is None and guard.diagnostic
    assert state.value.upper() in format_report(results)
    assert "report_finalization:" in format_report(results)
    assert receipt.read_bytes() == original_receipt
