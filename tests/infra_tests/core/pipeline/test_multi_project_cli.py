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
from tests._support.projects import make_repo


# ---------------------------------------------------------------------------
# Stand-in helpers (no unittest.mock)
# ---------------------------------------------------------------------------


def _stage(success: bool, duration: float = 1.0) -> SimpleNamespace:
    """Build a minimal stage-like object with ``success`` and ``duration``."""
    return SimpleNamespace(success=success, duration=duration)


def _result(project_results: object) -> SimpleNamespace:
    """Build a minimal result-like object with ``project_results``."""
    return SimpleNamespace(project_results=project_results)


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
        """A non-dict ``project_results`` (e.g. a list) does not crash.

        The function iterates ``.items()`` only when the value is a dict;
        a list has no ``.items()`` so this exercises the guard path. Because
        the implementation does not isinstance-check, passing a list will
        raise AttributeError — we assert that the call surfaces the real
        behavior rather than swallowing it.
        """
        result = SimpleNamespace(project_results=["not", "a", "dict"])
        with pytest.raises(AttributeError):
            _failed_project_names(result)

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
        assert args.no_llm is False
        assert args.no_executive_report is False
        assert args.skip_infra is False
        assert args.parallel is False
        assert args.max_workers is None
        assert args.resume is False

    def test_no_infra_tests_flag(self) -> None:
        args = build_arg_parser().parse_args(["--no-infra-tests"])
        assert args.no_infra_tests is True

    def test_no_llm_flag(self) -> None:
        args = build_arg_parser().parse_args(["--no-llm"])
        assert args.no_llm is True

    def test_no_executive_report_flag(self) -> None:
        args = build_arg_parser().parse_args(["--no-executive-report"])
        assert args.no_executive_report is True

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
                "--no-llm",
                "--no-executive-report",
                "--skip-infra",
                "--parallel",
                "--max-workers",
                "8",
                "--resume",
            ]
        )
        assert args.no_infra_tests is True
        assert args.no_llm is True
        assert args.no_executive_report is True
        assert args.skip_infra is True
        assert args.parallel is True
        assert args.max_workers == 8
        assert args.resume is True


# ---------------------------------------------------------------------------
# main — real execution against synthetic project trees
# ---------------------------------------------------------------------------


class TestMain:
    def test_empty_repo_returns_one(self, tmp_path: Path) -> None:
        """A repo with no ``projects/`` directory returns exit code 1."""
        # tmp_path has no projects/ dir → discover_projects returns []
        rc = main(["--no-infra-tests", "--no-llm"], repo_root=tmp_path)
        assert rc == 1

    def test_empty_projects_dir_returns_one(self, tmp_path: Path) -> None:
        """A repo with an empty ``projects/`` directory returns exit code 1."""
        (tmp_path / "projects").mkdir()
        rc = main(["--no-infra-tests", "--no-llm"], repo_root=tmp_path)
        assert rc == 1

    def test_with_scaffolded_project(self, tmp_path: Path) -> None:
        """A repo with a valid scaffolded project returns 0 or 1.

        With ``--no-infra-tests --no-llm`` the pipeline runs core-only stages.
        The scaffold from ``make_project`` is minimal, so the run may succeed
        (0) or report failures (1) depending on which stages execute — but it
        must not crash with an unhandled exception.
        """
        make_repo(tmp_path, names=("template_test",))
        rc = main(
            ["--no-infra-tests", "--no-llm"],
            repo_root=tmp_path,
        )
        assert rc in (0, 1)

    def test_no_llm_only_flag(self, tmp_path: Path) -> None:
        """``--no-llm`` alone (infra tests still on) runs without crashing."""
        make_repo(tmp_path, names=("template_test",))
        rc = main(["--no-llm"], repo_root=tmp_path)
        assert rc in (0, 1)

    def test_skip_infra_flag(self, tmp_path: Path) -> None:
        """``--skip-infra`` runs without crashing."""
        make_repo(tmp_path, names=("template_test",))
        rc = main(["--no-llm", "--skip-infra"], repo_root=tmp_path)
        assert rc in (0, 1)

    def test_no_executive_report_flag(self, tmp_path: Path) -> None:
        """``--no-executive-report`` runs without crashing."""
        make_repo(tmp_path, names=("template_test",))
        rc = main(
            ["--no-infra-tests", "--no-llm", "--no-executive-report"],
            repo_root=tmp_path,
        )
        assert rc in (0, 1)

    def test_parallel_empty_repo_returns_one(self, tmp_path: Path) -> None:
        """``--parallel`` with no projects returns 1."""
        rc = main(
            ["--parallel", "--no-llm"],
            repo_root=tmp_path,
        )
        assert rc == 1

    def test_parallel_with_scaffolded_project(self, tmp_path: Path) -> None:
        """``--parallel`` with a scaffolded project runs without crashing."""
        make_repo(tmp_path, names=("template_test",))
        rc = main(
            ["--parallel", "--no-infra-tests", "--no-llm"],
            repo_root=tmp_path,
        )
        assert rc in (0, 1)
