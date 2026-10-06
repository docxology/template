"""Real guardian execution and source-owned review policy negative controls."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import signal
import shutil
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from infrastructure.core.subprocess_policy import BoundedSubprocessResult
from template_search_project.analysis.review_execution import (
    ReviewPlan,
    _finalize_execution,
    _read_record,
    child_observation,
    execute_plan,
    launch_plan,
    positive_timeout,
    resolve_plan,
    review_cli,
    run_review_child,
)

PROJECT = Path(__file__).resolve().parents[2]
POSIX = os.name == "posix"
pytestmark = pytest.mark.timeout(240)


def _project(tmp_path: Path, stages: list[dict] | None = None) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    (project / "src").mkdir()
    (project / "review_config.yaml").write_text(
        yaml.safe_dump(
            {
                "review": {
                    "stages": stages
                    if stages is not None
                    else [{"name": "infrastructure_usage", "stage_type": "custom"}],
                    "output": {"dir": "output/.pipeline/review", "summary_json": "summary.json"},
                }
            }
        )
    )
    return project


def _plan(
    project: Path, *, timeout: float = 150, stage_timeout: float = 60, selected: list[str] | None = None
) -> ReviewPlan:
    return resolve_plan(
        project,
        PROJECT / "src",
        selected=selected,
        fail_fast=False,
        stage_timeout=stage_timeout,
        deadline_monotonic=time.monotonic() + timeout,
    )


def _summary(plan: ReviewPlan) -> dict:
    return json.loads((Path(plan.project_root) / plan.output_dir / plan.summary_json).read_text())


@pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan"), True, "bad"])
def test_invalid_timeouts_are_rejected_before_execution(value):
    with pytest.raises(argparse.ArgumentTypeError, match="positive and finite"):
        positive_timeout(value)


@pytest.mark.parametrize("value", [1, 0.1, "300"])
def test_positive_finite_timeouts_are_admitted(value):
    assert positive_timeout(value) == float(value)


@pytest.mark.parametrize(
    "stages",
    [
        [],
        [{}],
        [None],
        [{"name": "../escape", "stage_type": "custom"}],
        [{"name": "infrastructure_usage", "stage_type": "custom", "enabled": "yes"}],
        [{"name": "infrastructure_usage", "stage_type": "custom", "args": [1]}],
        [{"name": "infrastructure_usage", "stage_type": "custom", "description": 1}],
        [{"name": "infrastructure_usage", "stage_type": "custom", "module": "retired.module"}],
        [{"name": "infrastructure_usage", "stage_type": "custom", "function": "wrong_function"}],
        [{"name": "infrastructure_usage", "stage_type": "custom", "args": ["--ignored"]}],
        [{"name": "infrastructure_usage", "stage_type": "custom", "infra_module": "infrastructure.validation.cli"}],
        [{"name": "infrastructure_usage"}],
        [{"name": "unknown", "stage_type": "custom"}],
        [{"name": "check", "infra_module": "foreign.cli", "command": "run"}],
        [{"name": "check", "infra_module": "infrastructure.validation.cli"}],
        [{"name": "infrastructure_usage", "stage_type": "custom"}] * 2,
    ],
)
def test_invalid_declarations_do_not_execute_workers(tmp_path, stages):
    project = _project(tmp_path, stages)
    with pytest.raises(ValueError):
        _plan(project)
    assert not (project / "output").exists()


def test_selection_and_serialization_share_exact_resolved_plan(tmp_path):
    project = _project(
        tmp_path,
        [
            {"name": "bibliography_completeness", "stage_type": "custom", "enabled": False},
            {"name": "infrastructure_usage", "stage_type": "custom"},
        ],
    )
    plan = _plan(project, selected=["infrastructure_usage"])
    decoded = ReviewPlan.decode(plan.encode())
    assert decoded == plan and decoded.plan_sha256 == plan.plan_sha256
    assert [stage.name for stage in plan.stages] == ["infrastructure_usage"]
    retired = json.loads(plan.encode())
    retired["schema_version"] = 0
    with pytest.raises(ValueError, match="unsupported review plan schema"):
        ReviewPlan.decode(json.dumps(retired))
    with pytest.raises(ValueError, match="Unknown stage"):
        _plan(project, selected=["absent"])


@pytest.mark.parametrize(
    "output",
    [
        None,
        {"dir": "../outside"},
        {"dir": "/outside"},
        {"summary_json": "nested/summary.json"},
        {"summary_json": "stage_infrastructure_usage.json"},
    ],
)
def test_output_configuration_cannot_escape_own_project(tmp_path, output):
    project = _project(tmp_path)
    payload = yaml.safe_load((project / "review_config.yaml").read_text())
    payload["review"]["output"] = output
    (project / "review_config.yaml").write_text(yaml.safe_dump(payload))
    with pytest.raises(ValueError):
        _plan(project)


def test_cli_list_and_invalid_selection_never_execute_a_worker(tmp_path, capsys):
    project = _project(tmp_path)
    assert review_cli(PROJECT / "src", ["--project-root", str(project), "--list"]) == 0
    assert "infrastructure_usage" in capsys.readouterr().out
    with pytest.raises(SystemExit) as error:
        review_cli(PROJECT / "src", ["--project-root", str(project), "--stage", "absent"])
    assert error.value.code == 2 and not (project / "output").exists()


def test_disabled_stage_skip_is_bound_to_current_plan_without_execution(tmp_path):
    project = _project(tmp_path, [{"name": "infrastructure_usage", "stage_type": "custom", "enabled": False}])
    plan = _plan(project)
    assert execute_plan(plan) == 0
    summary = _summary(plan)
    assert summary["skipped"] == 1 and summary["passed"] == 0 and summary["complete"]
    assert summary["run_id"] == plan.run_id and summary["plan_sha256"] == plan.plan_sha256
    assert not list((project / "output/.pipeline/review").glob("stage_*.json"))


def test_expired_budget_does_not_launch_a_stage_or_report_success(tmp_path):
    project = _project(tmp_path)
    plan = replace(_plan(project), deadline_monotonic=time.monotonic() - 1)
    assert execute_plan(plan) == 124
    summary = _summary(plan)
    assert summary["overall_exit_code"] == 1 and not summary["complete"]
    result = json.loads((project / "output/.pipeline/review/stage_infrastructure_usage.json").read_text())
    assert result["timed_out"] and result["original_exit_code"] is None
    assert "before stage launch" in result["command_error"]


@pytest.mark.parametrize("exit_code", [0, 2, 7])
def test_real_child_exit_codes_are_retained_exactly(tmp_path, exit_code):
    result = run_review_child(
        [sys.executable, "-I", "-c", "import sys;print('owned child');sys.exit(int(sys.argv[1]))", str(exit_code)],
        cwd=tmp_path,
        timeout=60,
    )
    assert result.returncode == result.original_returncode == exit_code, result
    assert result.stdout.strip() == "owned child"
    assert not result.timed_out and not result.custody_refused
    assert child_observation(result)["original_exit_code"] == exit_code


def test_actual_launch_refusal_is_failure_not_success(tmp_path):
    result = run_review_child([str(tmp_path / "missing-executable")], cwd=tmp_path, timeout=60)
    assert result.returncode == 1 and result.original_returncode is None
    assert "failed to launch" in result.command_error and not result.timed_out


def test_real_infra_custom_failure_and_fail_fast_keep_stage_classification(tmp_path):
    project = _project(
        tmp_path,
        [
            {
                "name": "invalid_infra",
                "infra_module": "infrastructure.reference.citation.cli",
                "command": "invalid-command",
            },
            {"name": "infrastructure_usage", "stage_type": "custom"},
        ],
    )
    plan = replace(_plan(project), fail_fast=True)
    result = launch_plan(plan)
    assert result.returncode == 1, result
    summary = _summary(plan)
    assert summary["expected_stages"] == ["invalid_infra", "infrastructure_usage"]
    assert summary["total"] == 1 and summary["failed"] == 1 and not summary["complete"]
    stage = json.loads((project / "output/.pipeline/review/stage_invalid_infra.json").read_text())
    assert stage["type"] == "infra" and stage["exit_code"] == stage["original_exit_code"] == 2
    assert not (project / "output/.pipeline/review/stage_infrastructure_usage.json").exists()


def test_finalization_refuses_wrong_run_incomplete_or_malformed_summary(tmp_path):
    project = _project(tmp_path)
    plan = _plan(project)
    directory = project / "output/.pipeline/review"
    directory.mkdir(parents=True)
    for payload in ('{"run_id":"wrong"}', '{"complete":true}', "malformed", "{}"):
        (directory / "summary.json").write_text(payload)
        observation = BoundedSubprocessResult(("owned-observation",), 0, False, original_returncode=0)
        result = _finalize_execution(plan, observation)
        assert result.returncode == 1 and result.original_returncode == 0
        assert not _summary(plan)["complete"] and _summary(plan)["overall_exit_code"] == 1


def _assert_not_alive(pid: int) -> None:
    state = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(pid)],
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    assert not state or state.startswith("Z"), f"owned PID {pid} survived guardian cleanup in state {state}"


def _sleeping_tree(directory: Path) -> tuple[str, str]:
    root_pid = directory / "root.pid"
    child_pid = directory / "child.pid"
    marker = directory / "detached-write"
    child = f"import pathlib,time;time.sleep(300);pathlib.Path({str(marker)!r}).write_text('leaked')"
    root = (
        "import os,pathlib,subprocess,sys,time;"
        f"pathlib.Path({str(root_pid)!r}).write_text(str(os.getpid()));"
        "child=subprocess.Popen([sys.executable,'-I','-c',sys.argv[1]],start_new_session=True,"
        "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
        f"pathlib.Path({str(child_pid)!r}).write_text(str(child.pid));"
        "time.sleep(300)"
    )
    return root, child


def _blocking_pytest_project(tmp_path: Path) -> Path:
    project = _project(tmp_path, [{"name": "test_suite_health", "stage_type": "custom"}])
    tests = project / "tests"
    tests.mkdir()
    root, child = _sleeping_tree(project)
    (tests / "test_blocking.py").write_text(
        "import subprocess,sys\n"
        "def test_real_blocking_child():\n"
        f"    process = subprocess.Popen([sys.executable,'-I','-c',{root!r},{child!r}])\n"
        "    assert process.wait(timeout=300) == 0\n"
    )
    (project / "pyproject.toml").write_text("[tool.pytest.ini_options]\nminversion='7.0'\n")
    return project


@pytest.mark.skipif(not POSIX, reason="actual detached POSIX session cleanup acceptance")
@pytest.mark.timeout(100)
def test_timeout_kills_real_started_detached_descendant(tmp_path):
    root, child = _sleeping_tree(tmp_path)
    result = run_review_child([sys.executable, "-I", "-c", root, child], cwd=tmp_path, timeout=60)
    assert (tmp_path / "root.pid").is_file() and (tmp_path / "child.pid").is_file(), (
        "deadline expired before actual tree launch"
    )
    assert result.returncode == 124 and result.timed_out and result.original_returncode is not None
    for path in (tmp_path / "root.pid", tmp_path / "child.pid"):
        _assert_not_alive(int(path.read_text()))
    assert not (tmp_path / "detached-write").exists()


@pytest.mark.skipif(not POSIX, reason="actual POSIX interruption and detached session cleanup acceptance")
@pytest.mark.timeout(160)
def test_interruption_cleans_actual_cli_tree_before_130(tmp_path):
    project = _blocking_pytest_project(tmp_path)
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            str(PROJECT / "scripts/review"),
            "--project-root",
            str(project),
            "--timeout",
            "120",
            "--stage-timeout",
            "300",
        ],
        cwd=tmp_path,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    pids: list[int] = []
    try:
        deadline = time.monotonic() + 100
        while not (project / "child.pid").is_file():
            assert process.poll() is None, "CLI exited before actual detached tree launch"
            assert time.monotonic() < deadline, "CLI did not launch the actual process tree"
            time.sleep(0.02)
        pids = [int((project / filename).read_text()) for filename in ("root.pid", "child.pid")]
        os.kill(process.pid, signal.SIGINT)
        assert process.wait(timeout=30) == 130
        summary = json.loads((project / "output/.pipeline/review/summary.json").read_text())
        assert summary["execution_exit_code"] == 130 and summary["execution"]["interrupted"]
        assert summary["overall_exit_code"] == 1 and not summary["complete"]
        for pid in pids:
            _assert_not_alive(pid)
        assert not (project / "detached-write").exists()
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        for pid in pids:
            with contextlib.suppress(ProcessLookupError):
                os.kill(pid, signal.SIGKILL)


@pytest.mark.skipif(not POSIX, reason="actual POSIX whole-review nested-process acceptance")
@pytest.mark.timeout(180)
def test_whole_deadline_covers_actual_worker_nested_pytest_and_detached_descendant(tmp_path):
    project = _blocking_pytest_project(tmp_path)
    plan = _plan(project, timeout=120, stage_timeout=300)
    result = launch_plan(plan)
    assert (project / "root.pid").is_file() and (project / "child.pid").is_file(), (
        "deadline expired before actual nested execution"
    )
    assert result.returncode == 124 and result.timed_out
    assert not _summary(plan)["complete"] and _summary(plan)["overall_exit_code"] == 1
    assert _summary(plan)["execution"]["timed_out"]
    for filename in ("root.pid", "child.pid"):
        _assert_not_alive(int((project / filename).read_text()))
    assert not (project / "detached-write").exists()


def test_actual_zero_exit_corrupted_custom_producer_fails_domain_validation(tmp_path):
    project = _project(tmp_path)
    (project / "src/valid.py").write_text("import infrastructure.core.logging.utils\n")
    source = tmp_path / "own-source"
    shutil.copytree(PROJECT / "src", source, ignore=shutil.ignore_patterns("__pycache__"))
    producer = source / "template_search_project/analysis/analysis.py"
    original = producer.read_text()
    statement = "    print(json.dumps(result.as_dict(), indent=2))"
    assert original.count(statement) == 1
    producer.write_text(original.replace(statement, "    print('owned invalid domain JSON')", 1))
    plan = replace(_plan(project), own_source_root=str(source))
    result = launch_plan(plan)
    assert result.returncode == 1, result
    record = json.loads((project / "output/.pipeline/review/stage_infrastructure_usage.json").read_text())
    assert record["exit_code"] == record["original_exit_code"] == 0
    assert not record["success"] and "valid matching domain result" in record["domain_error"]
    assert _summary(plan)["overall_exit_code"] == 1 and not _summary(plan)["complete"]


def test_actual_current_stage_record_tampering_cannot_authorize_final_success(tmp_path):
    project = _project(tmp_path)
    (project / "src/valid.py").write_text("import infrastructure.core.logging.utils\n")
    plan = _plan(project)
    observed = launch_plan(plan)
    assert observed.returncode == 0, observed
    directory = project / "output/.pipeline/review"
    original_summary = (directory / "summary.json").read_bytes()
    stage = directory / "stage_infrastructure_usage.json"
    original_record = json.loads(stage.read_text())
    for mutation in (
        {"run_id": "wrong"},
        {"schema_version": 0},
        {"original_exit_code": 7},
        {"success": False},
        {"exit_code": False},
        {"interrupted": True},
        {"result": {"name": "wrong", "status": "passed", "exit_code": 0, "details": {}}},
    ):
        (directory / "summary.json").write_bytes(original_summary)
        stage.write_text(json.dumps({**original_record, **mutation}))
        result = _finalize_execution(plan, observed)
        assert result.returncode == 1 and result.original_returncode == 0
        assert _summary(plan)["overall_exit_code"] == 1 and not _summary(plan)["complete"]
    for mutation in ({"complete": "true"}, {"overall_exit_code": False}, {"execution_exit_code": False}):
        stage.write_text(json.dumps(original_record))
        original_payload = json.loads(original_summary)
        (directory / "summary.json").write_text(json.dumps({**original_payload, **mutation}))
        assert _finalize_execution(plan, observed).returncode == 1
        assert not _summary(plan)["complete"]
    (directory / "summary.json").write_bytes(original_summary)
    stage.unlink()
    assert _finalize_execution(plan, observed).returncode == 1


def test_actual_interrupted_child_code_wins_over_late_final_reporting(tmp_path):
    project = _project(tmp_path)
    plan = _plan(project)
    observed = run_review_child([sys.executable, "-I", "-c", "raise SystemExit(130)"], cwd=tmp_path, timeout=60)
    assert observed.returncode == observed.original_returncode == 130
    expired = replace(plan, deadline_monotonic=time.monotonic() - 1)
    directory = project / "output/.pipeline/review"
    directory.mkdir(parents=True)
    (directory / "summary.json").write_text("{}")
    finalized = _finalize_execution(expired, observed)
    assert finalized.returncode == finalized.original_returncode == 130
    assert _summary(expired)["execution"]["interrupted"] and not _summary(expired)["complete"]


@pytest.mark.parametrize("filename", ["summary.json", "stage_infrastructure_usage.json"])
def test_output_file_symlink_is_refused_before_worker_and_preserves_target(tmp_path, filename):
    project = _project(tmp_path)
    output = project / "output/.pipeline/review"
    output.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    original = b"owned external marker remains unchanged"
    outside.write_bytes(original)
    (output / filename).symlink_to(outside)
    with pytest.raises(SystemExit) as error:
        review_cli(PROJECT / "src", ["--project-root", str(project)])
    assert error.value.code == 2
    assert outside.read_bytes() == original and (output / filename).is_symlink()
    assert not (output / "provider-observations").exists()


@pytest.mark.parametrize("filename", ["summary.json", "stage_infrastructure_usage.json"])
def test_post_resolution_file_symlink_is_refused_by_confined_writer(tmp_path, filename):
    project = _project(tmp_path)
    plan = replace(_plan(project), deadline_monotonic=time.monotonic() - 1)
    output = project / "output/.pipeline/review"
    output.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    original = b"external target cannot be overwritten"
    outside.write_bytes(original)
    (output / filename).symlink_to(outside)
    with pytest.raises(ValueError, match="symlink write target"):
        execute_plan(plan)
    assert outside.read_bytes() == original and (output / filename).is_symlink()


def test_replaced_project_directory_cannot_redirect_resolved_review(tmp_path):
    project = _project(tmp_path)
    plan = _plan(project)
    project.rename(tmp_path / "original-project")
    project.mkdir()
    with pytest.raises(ValueError, match="root changed"):
        launch_plan(plan)
    assert not (project / "output").exists()


def test_summary_stage_filename_collision_is_invocation_error_before_worker(tmp_path):
    project = _project(tmp_path)
    path = project / "review_config.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["review"]["output"]["summary_json"] = "stage_infrastructure_usage.json"
    path.write_text(yaml.safe_dump(payload))
    with pytest.raises(SystemExit) as error:
        review_cli(PROJECT / "src", ["--project-root", str(project)])
    assert error.value.code == 2 and not (project / "output").exists()


def test_unselected_configured_stage_summary_collision_is_invocation_error_before_worker(tmp_path):
    project = _project(
        tmp_path,
        [
            {"name": "bibliography_completeness", "stage_type": "custom"},
            {"name": "infrastructure_usage", "stage_type": "custom"},
        ],
    )
    path = project / "review_config.yaml"
    payload = yaml.safe_load(path.read_text())
    payload["review"]["output"]["summary_json"] = "stage_bibliography_completeness.json"
    path.write_text(yaml.safe_dump(payload))
    with pytest.raises(SystemExit) as error:
        review_cli(PROJECT / "src", ["--project-root", str(project), "--stage", "infrastructure_usage"])
    assert error.value.code == 2 and not (project / "output").exists()


def test_post_resolution_ancestor_symlink_cannot_redirect_reads_or_writes(tmp_path):
    project = _project(tmp_path)
    plan = _plan(project)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / ".pipeline/review").mkdir(parents=True)
    outside_marker = outside / ".pipeline/review/summary.json"
    original = b'{"invented_private_fixture":"must not be read through symlink"}'
    outside_marker.write_bytes(original)
    (project / "output").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        launch_plan(plan)
    assert outside_marker.read_bytes() == original
    with pytest.raises(ValueError, match="symlink"):
        _read_record(plan, project / "output/.pipeline/review/summary.json")
    assert outside_marker.read_bytes() == original
    assert not (outside / ".pipeline/review/stage_infrastructure_usage.json").exists()


@pytest.mark.parametrize("filename", ["summary.json", "stage_infrastructure_usage.json"])
def test_existing_leaf_symlink_cannot_supply_review_reader_input(tmp_path, filename):
    project = _project(tmp_path)
    plan = _plan(project)
    output = project / "output/.pipeline/review"
    output.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    original = b'{"invented_external_fixture":"must not become current evidence"}'
    outside.write_bytes(original)
    (output / filename).symlink_to(outside)
    with pytest.raises((OSError, ValueError)):
        _read_record(plan, output / filename)
    assert outside.read_bytes() == original
