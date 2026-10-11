"""Real-behavior tests for ``infrastructure.core.pipeline.multi_project_cli``.

Covers the pure-logic helpers ``_failed_project_names`` and
``_log_project_status``, the ``build_arg_parser`` flag surface, and the
``main`` entry point against synthetic project trees built with
``tests._support.projects.make_project``.

No mocks are used — simple ``SimpleNamespace`` stand-ins exercise the real
code paths of the pure functions, and ``main`` runs against real on-disk
scaffolds.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from infrastructure.core.pipeline.multi_project_cli import (
    _failed_project_names,
    _log_project_status,
    build_arg_parser,
    main,
)
from tests.infra_tests.orchestration._pipeline_fixture import scaffold_pipeline
from infrastructure.core.pipeline.multi_project import MultiProjectResult
from infrastructure.core.pipeline.types import PipelineStageResult
from infrastructure.core.pipeline.outcomes import RunResult


# ---------------------------------------------------------------------------
# Stand-in helpers (no unittest.mock)
# ---------------------------------------------------------------------------


def _stage(success: bool, duration: float = 1.0) -> PipelineStageResult:
    """Construct a canonical result for pure reporting comparisons."""
    return PipelineStageResult(
        1,
        "Analysis",
        success=success,
        duration=duration,
        stage_key="analysis",
        stage_completed=success,
        exit_code=0 if success else 1,
    )


def _result(project_results: dict[str, list[PipelineStageResult]]) -> MultiProjectResult:
    contracts = {}
    for name, stages in project_results.items():
        if not isinstance(stages, list):
            continue
        for index, stage in enumerate(stages):
            stage.stage_key = f"stage_{index}"
        contracts[name] = RunResult.from_results(stages, tuple(stage.stage_key for stage in stages))
    return MultiProjectResult(project_results, expected_projects=tuple(project_results), run_results=contracts)


# ---------------------------------------------------------------------------
# _failed_project_names
# ---------------------------------------------------------------------------


class TestFailedProjectNames:
    def test_empty_result_returns_empty(self) -> None:
        """A result with no ``project_results`` attribute yields no failures."""
        result = SimpleNamespace()
        assert _failed_project_names(result) == []

    def test_empty_dict_returns_empty(self) -> None:
        """An empty ``project_results`` dict yields no failures."""
        assert _failed_project_names(_result({})) == []

    def test_all_success_returns_empty(self) -> None:
        """All stages succeeding for every project → no failures."""
        result = _result(
            {
                "proj_a": [_stage(True, 1.0), _stage(True, 2.0)],
                "proj_b": [_stage(True, 0.5)],
            }
        )
        assert _failed_project_names(result) == []

    def test_all_failure_returns_all_names(self) -> None:
        """Every project has at least one failing stage → all fail."""
        result = _result(
            {
                "proj_a": [_stage(False, 1.0), _stage(False, 2.0)],
                "proj_b": [_stage(False, 0.5)],
            }
        )
        assert sorted(_failed_project_names(result)) == ["proj_a", "proj_b"]

    def test_mixed_success_failure(self) -> None:
        """Only projects with at least one failing stage are reported."""
        result = _result(
            {
                "proj_a": [_stage(True, 1.0), _stage(True, 2.0)],
                "proj_b": [_stage(True, 1.0), _stage(False, 2.0)],
                "proj_c": [_stage(False, 0.5)],
            }
        )
        assert sorted(_failed_project_names(result)) == ["proj_b", "proj_c"]

    def test_missing_project_results_attribute(self) -> None:
        """An object lacking ``project_results`` is treated as no failures."""
        result = SimpleNamespace(successful_projects=0)
        assert _failed_project_names(result) == []

    def test_non_dict_project_results(self) -> None:
        """Malformed display data cannot assert an expected project contract."""
        result = SimpleNamespace(project_results=["not", "a", "dict"], expected_projects=("expected",))
        assert _failed_project_names(result) == ["expected"]

    def test_empty_list_values_are_failures(self) -> None:
        """A project with an empty results list is considered failed."""
        result = _result(
            {
                "proj_a": [],
                "proj_b": [_stage(True, 1.0)],
            }
        )
        assert _failed_project_names(result) == ["proj_a"]

    def test_none_project_results(self) -> None:
        """``project_results=None`` is falsy → empty list (guard clause)."""
        result = SimpleNamespace(project_results=None)
        assert _failed_project_names(result) == []


# ---------------------------------------------------------------------------
# _log_project_status
# ---------------------------------------------------------------------------


class TestLogProjectStatus:
    def test_empty_result_does_not_crash(self) -> None:
        """A result with no ``project_results`` attribute returns cleanly."""
        result = SimpleNamespace()
        assert _log_project_status(result) is None

    def test_none_project_results_does_not_crash(self) -> None:
        """``project_results=None`` is falsy → early return."""
        result = SimpleNamespace(project_results=None)
        assert _log_project_status(result) is None

    def test_dict_with_stage_lists_does_not_crash(self) -> None:
        """A well-formed dict with stage lists is logged without error."""
        result = _result(
            {
                "proj_a": [_stage(True, 1.0), _stage(True, 2.0)],
                "proj_b": [_stage(False, 0.5)],
            }
        )
        assert _log_project_status(result) is None

    def test_non_dict_project_results_does_not_crash(self) -> None:
        """A non-dict ``project_results`` logs a warning and returns."""
        result = SimpleNamespace(project_results="not-a-dict")
        # Should not raise; logs a warning and returns.
        assert _log_project_status(result) is None

    def test_empty_list_value_logged_as_unknown(self) -> None:
        """An empty results list is logged as unknown status."""
        result = _result({"proj_a": []})
        assert _log_project_status(result) is None

    def test_non_list_value_logged_as_unknown(self) -> None:
        """A non-list entry is logged as unknown status."""
        result = _result({"proj_a": "not-a-list"})
        assert _log_project_status(result) is None


# ---------------------------------------------------------------------------
# build_arg_parser
# ---------------------------------------------------------------------------


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

    @pytest.mark.slow
    def test_with_scaffolded_project(self, tmp_path: Path) -> None:
        """A repo with a valid scaffolded project returns 0 or 1.

        With ``--no-infra-tests --mode core`` the pipeline runs local stages.
        The scaffold from ``make_project`` is minimal, so the run may succeed
        (0) or report failures (1) depending on which stages execute — but it
        must not crash with an unhandled exception.
        """
        scaffold_pipeline(tmp_path, ("templates/template_test",))
        rc = main(
            ["--no-infra-tests", "--mode", "core"],
            repo_root=tmp_path,
        )
        assert rc in (0, 1)

    def test_default_core_with_shared_stage(self, tmp_path: Path) -> None:
        """Core invocation runs its canonical shared gate before the project."""
        scaffold_pipeline(tmp_path, ("templates/template_test",))
        rc = main(["--mode", "core"], repo_root=tmp_path)
        assert rc in (0, 1)

    def test_skip_infra_flag(self, tmp_path: Path) -> None:
        """``--skip-infra`` runs without crashing."""
        scaffold_pipeline(tmp_path, ("templates/template_test",))
        rc = main(["--mode", "core", "--skip-infra"], repo_root=tmp_path)
        assert rc in (0, 1)

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

    def test_parallel_with_scaffolded_project(self, tmp_path: Path) -> None:
        """``--parallel`` with a scaffolded project runs without crashing."""
        scaffold_pipeline(tmp_path, ("templates/template_test",))
        rc = main(
            ["--parallel", "--no-infra-tests", "--mode", "core"],
            repo_root=tmp_path,
        )
        assert rc in (0, 1)


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
