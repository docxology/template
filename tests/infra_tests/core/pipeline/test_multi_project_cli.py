"""Real CLI completion, reporting and invocation-error controls."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.pipeline.multi_project_cli import build_arg_parser, main
from infrastructure.core.pipeline.multi_project import MultiProjectResult


class TestBuildArgParser:
    def test_no_flags_defaults(self) -> None:
        """With no arguments, all flags default to False/None."""
        args = build_arg_parser().parse_args([])
        assert args.no_infra_tests is False
        assert args.mode == "core"
        assert args.skip_infra is False
        assert args.parallel is False
        assert args.max_workers is None
        assert args.resume is False

    def test_no_infra_tests_flag(self) -> None:
        args = build_arg_parser().parse_args(["--no-infra-tests"])
        assert args.no_infra_tests is True

    def test_live_mode(self) -> None:
        args = build_arg_parser().parse_args(["--mode", "core"])
        assert args.mode == "core"

    def test_removed_report_flag_is_rejected(self) -> None:
        with pytest.raises(SystemExit) as caught:
            build_arg_parser().parse_args(["--no-executive-report"])
        assert caught.value.code == 2

    def test_skip_infra_flag(self) -> None:
        args = build_arg_parser().parse_args(["--skip-infra"])
        assert args.skip_infra is True

    def test_parallel_flag(self) -> None:
        args = build_arg_parser().parse_args(["--parallel"])
        assert args.parallel is True

    def test_max_workers_flag(self) -> None:
        args = build_arg_parser().parse_args(["--max-workers", "4"])
        assert args.max_workers == 4

    def test_resume_flag(self) -> None:
        args = build_arg_parser().parse_args(["--resume"])
        assert args.resume is True

    def test_all_flags_combined(self) -> None:
        """All flags can be combined and parsed together."""
        args = build_arg_parser().parse_args(
            [
                "--no-infra-tests",
                "--mode",
                "core",
                "--skip-infra",
                "--parallel",
                "--max-workers",
                "8",
                "--resume",
            ]
        )
        assert args.no_infra_tests is True
        assert args.mode == "core"
        assert args.skip_infra is True
        assert args.parallel is True
        assert args.max_workers == 8
        assert args.resume is True


# ---------------------------------------------------------------------------
# main — real execution against synthetic project trees
# ---------------------------------------------------------------------------


@pytest.mark.timeout(120)
class TestMain:
    def test_empty_repo_returns_one(self, tmp_path: Path) -> None:
        """A repo with no ``projects/`` directory returns exit code 1."""
        # tmp_path has no projects/ dir → discover_projects returns []
        rc = main(["--no-infra-tests", "--mode", "core"], repo_root=tmp_path)
        assert rc == 1

    def test_empty_projects_dir_returns_one(self, tmp_path: Path) -> None:
        """A repo with an empty ``projects/`` directory returns exit code 1."""
        (tmp_path / "projects").mkdir()
        rc = main(["--no-infra-tests", "--mode", "core"], repo_root=tmp_path)
        assert rc == 1

    def test_removed_report_flag_is_invocation_error(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as caught:
            main(["--no-executive-report"], repo_root=tmp_path)
        assert caught.value.code == 2

    def test_parallel_empty_repo_returns_one(self, tmp_path: Path) -> None:
        """``--parallel`` with no projects returns 1."""
        rc = main(
            ["--parallel", "--mode", "core"],
            repo_root=tmp_path,
        )
        assert rc == 1


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf"])
def test_invalid_run_budget_before_discovery(tmp_path: Path, value: str) -> None:
    assert main(["--run-timeout", value], repo_root=tmp_path) == 2
    assert not (tmp_path / "output").exists()


@pytest.mark.timeout(120)
def test_cli_actual_qualified_completion_and_summary(tmp_path: Path) -> None:
    import json
    from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

    scaffold_pipeline(tmp_path, ("templates/alpha",))
    assert main(["--no-infra-tests", "--run-timeout", "90"], repo_root=tmp_path) == 0
    path = tmp_path / "output/multi_project_summary/multi_project_summary.json"
    summary = json.loads(path.read_text())
    assert summary["complete"] is True and summary["exit_code"] == 0
    project = summary["projects"]["templates/alpha"]
    assert project["success"] is True and project["expected_stage_keys"] == ["analysis"]
    assert project["outcomes"][0]["status"] == "succeeded"
    assert (tmp_path / "output/multi_project_summary/last-run-summary.md").is_file()


def test_expired_aggregate_reporting_refuses_before_launch(tmp_path: Path) -> None:
    import time
    from infrastructure.core.pipeline.multi_project_cli import _write_summary_reports

    assert _write_summary_reports(MultiProjectResult({}), [], tmp_path, deadline=time.monotonic() - 1) == 124
    assert not (tmp_path / "output").exists()


@pytest.mark.timeout(90)
@pytest.mark.parametrize("entry_point", ["runner", "serial", "parallel", "matrix"])
def test_frozen_shared_custody_refusal_preserves_original_diagnostic(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, entry_point: str
) -> None:
    """Real post-resolution drift remains pending at every public consumer."""
    import io
    import json
    import sys

    from infrastructure.core.pipeline.outcomes import StageStatus
    from infrastructure.core.pipeline.run_matrix import (
        execute_run_plan,
        format_report,
        parse_run_config,
        resolve_run_plan,
        run_plan_exit_code,
    )
    from infrastructure.core.pipeline.runtime_namespace import SharedRuntimeCustodyError, validate_shared_runtime
    from infrastructure.orchestration.pipeline_runner import MultiProjectInvocation, PipelineRunner
    from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline

    names = ("templates/alpha", "templates/beta")
    scaffold_pipeline(tmp_path, names)
    evidence = {}
    for name in names:
        historical = tmp_path / "projects" / name / "output/.pipeline/execution.json"
        historical.parent.mkdir()
        historical.write_bytes(b'{"historical_control_evidence":true}\n')
        evidence[historical] = historical.read_bytes()
    declaration = tmp_path / "infrastructure/core/pipeline/pipeline.yaml"
    original = declaration.read_bytes()
    admitted_plans = []
    refusals = []

    def mutate_at_real_admission(frame, event, arg):
        if frame.f_code is not validate_shared_runtime.__code__:
            return None
        config = frame.f_locals["config"]
        if config.repo_root != tmp_path or not config.shared_infrastructure:
            return None
        if event == "call":
            admitted_plans.append(frame.f_locals["plan"])
            declaration.write_bytes(original + b"\n# Actual post-resolution Source mutation.\n")
        elif event == "exception" and isinstance(arg[1], SharedRuntimeCustodyError):
            refusals.append(str(arg[1]))
            # Repair after the real refusal, before the consumer catches it.
            # Reobservation must not replace the already captured diagnostic.
            declaration.write_bytes(original)
        return mutate_at_real_admission

    matrix_results = None
    previous_trace = sys.gettrace()
    try:
        sys.settrace(mutate_at_real_admission)
        if entry_point == "runner":
            runner = PipelineRunner(tmp_path, stream=io.StringIO())
            exit_code = runner.run_multi(MultiProjectInvocation())
            emitted = runner.stream.getvalue()
        elif entry_point == "matrix":
            plan = resolve_run_plan(
                parse_run_config(
                    "run_timeout_seconds: 90\ndefaults:\n  stages: [infra_tests, analysis]\n"
                    "runs:\n  - project: templates/alpha\n  - project: templates/beta\n"
                ),
                tmp_path,
            )
            matrix_results = execute_run_plan(plan, tmp_path)
            exit_code = run_plan_exit_code(plan, matrix_results)
            emitted = format_report(matrix_results)
            assert [(row.project, row.stage) for row in matrix_results] == [
                (step.project, step.stage) for step in plan.steps
            ]
        else:
            options = ["--run-timeout", "90"]
            if entry_point == "parallel":
                options += ["--parallel", "--max-workers", "1"]
            exit_code = main(options, repo_root=tmp_path)
            emitted = caplog.text
    finally:
        sys.settrace(previous_trace)
        declaration.write_bytes(original)

    assert exit_code == 75
    assert len(admitted_plans) == len(refusals) == 1
    assert refusals[0] in emitted
    encoded = refusals[0].split("fingerprint_diagnostics=", 1)[1]
    diagnostic, _ = json.JSONDecoder().raw_decode(encoded)
    assert diagnostic["expected_total"] == admitted_plans[0].source_identity
    assert diagnostic["observed_total"] != diagnostic["expected_total"]
    assert set(diagnostic["components"]) == {"source", "python", "tools"}
    assert all(
        len(digest) == 64 and set(digest) <= set("0123456789abcdef")
        for digest in (diagnostic["observed_total"], *diagnostic["components"].values())
    )
    assert not (tmp_path / "process_order.log").exists()
    assert all(path.read_bytes() == content for path, content in evidence.items())
    assert not any((tmp_path / "projects" / name / "output/data/analysis.json").exists() for name in names)
    if matrix_results is not None:
        assert all(not row.ok and row.outcome.status is StageStatus.BLOCKED for row in matrix_results)
        assert all(row.outcome.child_exit_code is None for row in matrix_results)
        shared = matrix_results[0].shared_result
        assert shared is not None and shared.exit_code == 75
        assert shared.run_result.expected_stage_keys == ("infra_tests",) and not shared.run_result.complete
        assert len(shared.stage_results) == len(shared.run_result.outcomes) == 1
        refusal = shared.stage_results[0]
        assert refusal.stage_key == "execution" and refusal.error_message == refusals[0]
        assert refusal.outcome.status is StageStatus.BLOCKED and refusal.outcome.child_exit_code is None
        assert refusal.outcome.diagnostic == refusals[0]
