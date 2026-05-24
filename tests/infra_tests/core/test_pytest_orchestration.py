"""Tests for ``infrastructure.core.pytest_orchestration``.

Real subprocess and filesystem fixtures — no mocks.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from infrastructure.core.pytest_orchestration import (
    enforce_project_suite_guards,
    parse_discovery_count,
    project_declared_coverage_floor,
    project_has_test_files,
    resolve_coverage_file,
    resolve_infrastructure_test_paths,
)


def test_project_declared_coverage_floor_reads_pyproject(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        dedent(
            """
            [tool.coverage.report]
            fail_under = 88
            """
        ).lstrip(),
        encoding="utf-8",
    )
    assert project_declared_coverage_floor(project) == 88


def test_project_declared_coverage_floor_missing_file_returns_none(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    assert project_declared_coverage_floor(project) is None


def test_resolve_coverage_file_honours_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COVERAGE_FILE", "/tmp/custom.coverage")
    assert resolve_coverage_file(".coverage.project") == "/tmp/custom.coverage"


def test_resolve_coverage_file_default_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COVERAGE_FILE", raising=False)
    assert resolve_coverage_file(".coverage.union") == ".coverage.union"


def test_parse_discovery_count_variants() -> None:
    assert parse_discovery_count("collected 42 items") == 42
    assert parse_discovery_count("============== 7 tests collected ==============") == 7
    assert parse_discovery_count("no tests here") is None


def test_resolve_infrastructure_test_paths_smoke_is_fast_subset(tmp_path: Path) -> None:
    paths = resolve_infrastructure_test_paths(tmp_path, "pipeline-smoke")
    assert len(paths) == 9
    assert all(str(tmp_path) in p for p in paths)


def test_enforce_project_suite_guards_fails_low_coverage_with_zero_test_failures(
    tmp_path: Path,
) -> None:
    """cov-fail-under can exit non-zero while failed==0; guard must still fail strict runs."""
    project = tmp_path / "projects" / "demo"
    tests = project / "tests"
    tests.mkdir(parents=True)
    (tests / "test_x.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    exit_code = 0
    results = {"passed": 1, "failed": 0, "total": 1, "coverage_percent": 50.0}
    exit_code, results = enforce_project_suite_guards(
        exit_code,
        results,
        project_name="demo",
        project_root=project,
        project_threshold=90.0,
        strict=True,
    )
    assert exit_code == 1
    assert results["exit_code"] == 1


def test_enforce_project_suite_guards_zero_collected_with_test_files_fails(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    tests = project / "tests"
    tests.mkdir(parents=True)
    (tests / "test_x.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    exit_code, results = enforce_project_suite_guards(
        0,
        {"passed": 0, "failed": 0, "total": 0},
        project_name="demo",
        project_root=project,
        project_threshold=90.0,
        strict=True,
    )
    assert exit_code == 1


def test_project_has_test_files_detects_modules(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    tests = project / "tests"
    tests.mkdir(parents=True)
    assert not project_has_test_files(project)
    (tests / "test_a.py").write_text("def test_a(): pass\n", encoding="utf-8")
    assert project_has_test_files(project)
