"""Tests for ``infrastructure.core.pytest_orchestration``.

Real subprocess and filesystem fixtures — no mocks.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from infrastructure.core.pytest_orchestration import (
    build_project_pytest_command,
    build_union_pytest_command,
    enforce_project_suite_guards,
    parse_discovery_count,
    project_declared_coverage_floor,
    project_has_test_files,
    resolve_coverage_file,
    resolve_project_cov_config,
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


def test_resolve_project_cov_config_reads_run_section(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    pyproject = project / "pyproject.toml"
    pyproject.write_text(
        dedent(
            """
            [tool.coverage.run]
            branch = true
            """
        ).lstrip(),
        encoding="utf-8",
    )
    assert resolve_project_cov_config(project) == pyproject


def test_resolve_project_cov_config_missing_run_section_returns_none(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        dedent(
            """
            [tool.coverage.report]
            fail_under = 90
            """
        ).lstrip(),
        encoding="utf-8",
    )
    assert resolve_project_cov_config(project) is None


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


def test_enforce_project_suite_guards_does_not_recheck_coverage_threshold(
    tmp_path: Path,
) -> None:
    """Coverage gates are owned by pytest ``--cov-fail-under``, not this guard."""
    project = tmp_path / "projects" / "demo"
    tests = project / "tests"
    tests.mkdir(parents=True)
    (tests / "test_x.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    exit_code, results = enforce_project_suite_guards(
        0,
        {"passed": 1, "failed": 0, "total": 1, "coverage_percent": 50.0},
        project_name="demo",
        project_root=project,
        project_threshold=90.0,
        strict=True,
    )
    assert exit_code == 0
    assert results.get("exit_code", 0) == 0


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


def test_build_project_pytest_command_uses_uv_for_pyproject_projects(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "demo"
    project.mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        "[project]\nname = \"demo\"\n\n[project.optional-dependencies]\ndev = [\"pytest\"]\n",
        encoding="utf-8",
    )

    cmd = build_project_pytest_command(project, ["tests/", "--cov=src"])
    assert cmd[0].endswith("uv") or cmd[0] == "uv"
    assert "run" in cmd
    assert "--directory" in cmd
    assert str(project.resolve()) in cmd
    assert "--extra" in cmd and "dev" in cmd
    assert "tests/" in cmd
    assert "-m" in cmd and "pytest" in cmd


def test_build_union_pytest_command_uses_qualified_cov_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    project = repo / "projects" / "templates" / "demo"
    src = project / "src"
    tests = project / "tests"
    src.mkdir(parents=True)
    tests.mkdir(parents=True)
    (src / "__init__.py").write_text("", encoding="utf-8")
    (tests / "test_a.py").write_text("def test_a(): pass\n", encoding="utf-8")

    cmd = build_union_pytest_command(
        repo,
        project,
        tests,
        is_first=True,
        marker_expr="not slow",
        timeout=30,
    )
    joined = " ".join(cmd)
    assert "--cov=projects/templates/demo/src" in joined
    assert "--cov-append" not in joined

    cmd_append = build_union_pytest_command(
        repo,
        project,
        tests,
        is_first=False,
        marker_expr=None,
        timeout=30,
    )
    assert "--cov-append" in cmd_append
