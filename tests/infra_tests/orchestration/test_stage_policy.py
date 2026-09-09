"""Unit tests for the extracted Stage 01/05 CLI policy.

Covers the orchestration policy moved out of ``scripts/pipeline/stage_01_test.py``
into :mod:`infrastructure.orchestration.stage_policy`: mutual-exclusion
validation (including the ``--public-projects requires --project-only
--all-projects`` guard), profile/worker defaulting, and the default-project
placeholder fallback. All fixtures are real files on disk — no mocks.
"""

from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

import pytest

from infrastructure.orchestration.stage_policy import (
    DefaultProjectResolution,
    build_stage_01_parser,
    resolve_default_project,
    resolve_effective_project_workers,
    resolve_test_stage_options,
)
from tests._support.projects import make_project, make_repo


def _stage_options(**overrides: Any) -> dict[str, Any]:
    """Return a valid baseline kwargs dict for ``resolve_test_stage_options``."""
    options: dict[str, Any] = {
        "profile": "quick",
        "include_slow": False,
        "include_long_running": False,
        "include_ollama_tests": False,
        "include_bench": False,
        "infra_only": False,
        "project_only": False,
        "all_projects": False,
        "public_projects": False,
        "infra_scope": "full",
        "quiet": False,
        "strict": True,
        "project_workers": None,
        "parallel": None,
        "receipt_path": None,
    }
    options.update(overrides)
    return options


class TestMutualExclusionValidation:
    """Stage 01 flag conflicts fail closed with the historical CLI messages."""

    def test_public_projects_requires_project_only_all_projects(self) -> None:
        with pytest.raises(ValueError, match=r"--public-projects requires --project-only --all-projects"):
            resolve_test_stage_options(**_stage_options(public_projects=True))

    @pytest.mark.parametrize("missing", ["project_only", "all_projects"])
    def test_public_projects_guard_requires_both_flags(self, missing: str) -> None:
        overrides: dict[str, Any] = _stage_options(public_projects=True, project_only=True, all_projects=True)
        overrides[missing] = False

        with pytest.raises(ValueError, match=r"--public-projects requires --project-only --all-projects"):
            resolve_test_stage_options(**overrides)

    def test_public_projects_allowed_with_project_only_all_projects(self) -> None:
        options = resolve_test_stage_options(
            **_stage_options(project_only=True, all_projects=True, public_projects=True)
        )
        assert options.public_projects is True
        assert options.project_only is True
        assert options.all_projects is True

    def test_infra_only_and_project_only_conflict(self) -> None:
        with pytest.raises(ValueError, match=r"--infra-only and --project-only cannot be used together"):
            resolve_test_stage_options(**_stage_options(infra_only=True, project_only=True))

    def test_project_workers_requires_all_projects_mode(self) -> None:
        with pytest.raises(ValueError, match=r"--project-workers requires --project-only --all-projects"):
            resolve_test_stage_options(**_stage_options(project_workers="2"))

    def test_nested_concurrency_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="Nested test concurrency is not supported"):
            resolve_test_stage_options(
                **_stage_options(project_only=True, all_projects=True, project_workers="2", parallel="2")
            )


class TestProfileWorkerDefaulting:
    """Quick all-projects runs default to bounded auto parallelism."""

    def test_quick_all_projects_defaults_to_auto(self) -> None:
        assert (
            resolve_effective_project_workers(
                project_only=True, all_projects=True, project_workers=None, profile="quick"
            )
            == "auto"
        )

    def test_release_all_projects_stays_serial(self) -> None:
        assert (
            resolve_effective_project_workers(
                project_only=True, all_projects=True, project_workers=None, profile="release"
            )
            is None
        )

    def test_explicit_workers_are_preserved(self) -> None:
        assert (
            resolve_effective_project_workers(
                project_only=True, all_projects=True, project_workers="4", profile="quick"
            )
            == "4"
        )

    def test_default_only_applies_to_all_projects_mode(self) -> None:
        assert (
            resolve_effective_project_workers(
                project_only=True, all_projects=False, project_workers=None, profile="quick"
            )
            is None
        )

    def test_resolved_options_carry_effective_workers(self) -> None:
        options = resolve_test_stage_options(**_stage_options(project_only=True, all_projects=True))
        assert options.project_workers == "auto"

    def test_resolved_options_preserve_strict_flag(self) -> None:
        options = resolve_test_stage_options(**_stage_options(strict=False))
        assert options.strict is False


class TestDefaultProjectFallback:
    """The ``project`` placeholder falls back to the first runnable project."""

    def test_placeholder_falls_back_to_first_runnable_project(self, tmp_path: Path) -> None:
        make_repo(tmp_path, ("alpha", "beta"))
        resolution = resolve_default_project(tmp_path, "project")
        assert resolution.fallback_applied is True
        assert resolution.discovery_error is None
        assert resolution.project in {"alpha", "beta"}

    def test_runnable_placeholder_is_kept(self, tmp_path: Path) -> None:
        make_repo(tmp_path, ("project",))
        resolution = resolve_default_project(tmp_path, "project")
        assert resolution == DefaultProjectResolution(project="project", fallback_applied=False, discovery_error=None)

    def test_non_placeholder_project_is_kept(self, tmp_path: Path) -> None:
        make_repo(tmp_path, ("alpha",))
        resolution = resolve_default_project(tmp_path, "alpha")
        assert resolution == DefaultProjectResolution(project="alpha", fallback_applied=False, discovery_error=None)

    def test_no_runnable_project_keeps_placeholder(self, tmp_path: Path) -> None:
        make_repo(tmp_path, ("alpha",))
        shutil.rmtree(tmp_path / "projects" / "alpha" / "src")
        resolution = resolve_default_project(tmp_path, "project")
        assert resolution == DefaultProjectResolution(project="project", fallback_applied=False, discovery_error=None)

    def test_discovery_failure_degrades_to_error_payload(self, tmp_path: Path) -> None:
        # ``projects`` as a regular file makes iterdir raise NotADirectoryError.
        (tmp_path / "projects").write_text("not a directory", encoding="utf-8")
        resolution = resolve_default_project(tmp_path, "project")
        assert resolution.fallback_applied is False
        assert resolution.discovery_error is not None
        assert "projects" in resolution.discovery_error


class TestStage01Parser:
    """The extracted argparse wiring preserves the historical CLI defaults."""

    def test_default_project_is_placeholder(self) -> None:
        args = build_stage_01_parser().parse_args([])
        assert args.project == "project"

    def test_default_profile_is_quick(self) -> None:
        args = build_stage_01_parser().parse_args([])
        assert args.profile == "quick"

    def test_invalid_profile_is_rejected_by_choices(self) -> None:
        with pytest.raises(SystemExit):
            build_stage_01_parser().parse_args(["--profile", "bogus"])


def test_make_project_fixture_is_runnable(tmp_path: Path) -> None:
    """Guard the fixture contract the fallback tests rely on."""
    project = make_project(tmp_path, "alpha")
    assert (project / "src").exists() and (project / "tests").exists()
