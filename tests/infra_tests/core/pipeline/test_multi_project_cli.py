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
