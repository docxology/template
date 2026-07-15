"""Tests for ``infrastructure.core.pytest_orchestration``.

Real subprocess and filesystem fixtures — no mocks.
"""

from __future__ import annotations

import os
import sys
from importlib.metadata import version
from pathlib import Path
from textwrap import dedent

import pytest

from infrastructure.core.pytest_orchestration import (
    ENV_XDIST_WORKERS,
    PIPELINE_SMOKE_INFRA_TEST_PATHS,
    build_project_pytest_command,
    build_union_pytest_command,
    enforce_project_suite_guards,
    log_discovered_tests,
    parse_discovery_count,
    project_declared_coverage_floor,
    project_has_test_files,
    resolve_coverage_file,
    resolve_project_cov_config,
    resolve_infrastructure_test_paths,
    resolve_xdist_args,
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


def test_discovery_with_parallel_execution_command_does_not_run_tests(tmp_path: Path) -> None:
    """The count preflight must not execute a suite when xdist is enabled."""
    sentinel = tmp_path / "executed"
    test_file = tmp_path / "test_probe.py"
    test_file.write_text(
        "from pathlib import Path\n"
        "def test_probe():\n"
        f"    Path({str(sentinel)!r}).write_text('ran', encoding='utf-8')\n",
        encoding="utf-8",
    )
    command = [
        sys.executable,
        "-m",
        "pytest",
        str(test_file),
        "-n",
        "2",
        "--dist",
        "worksteal",
    ]

    log_discovered_tests(command, tmp_path, os.environ.copy(), "regression", timeout_seconds=30.0)

    assert not sentinel.exists()


def test_resolve_infrastructure_test_paths_smoke_is_fast_subset(tmp_path: Path) -> None:
    for relative in PIPELINE_SMOKE_INFRA_TEST_PATHS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix == ".py":
            target.write_text("", encoding="utf-8")
        else:
            target.mkdir(exist_ok=True)
    paths = resolve_infrastructure_test_paths(tmp_path, "pipeline-smoke")
    assert len(paths) == 9
    assert all(str(tmp_path) in p for p in paths)


def test_resolve_infrastructure_test_paths_smoke_manifest_exists_at_repo_root() -> None:
    """Every pinned smoke path must exist in THIS repo — catches renames like bench/ → benchmark/."""
    repo_root = Path(__file__).resolve().parents[3]
    paths = resolve_infrastructure_test_paths(repo_root, "pipeline-smoke")
    assert all(Path(p).exists() for p in paths)


def test_resolve_infrastructure_test_paths_smoke_fails_closed_on_missing_path(tmp_path: Path) -> None:
    """A manifest entry pointing nowhere must raise, never silently collect 0 tests."""
    with pytest.raises(FileNotFoundError, match="PIPELINE_SMOKE_INFRA_TEST_PATHS"):
        resolve_infrastructure_test_paths(tmp_path, "pipeline-smoke")


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
        '[project]\nname = "demo"\n\n[project.optional-dependencies]\ndev = ["pytest"]\n',
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


def test_build_project_pytest_command_injects_test_runner_deps(tmp_path: Path) -> None:
    """Test-runner packages are injected via --with so projects without pytest in their
    deps still work — specifically so --timeout=120 doesn't fail with exit=4 on CI where
    ``uv run --directory`` creates a project venv from the project's own pyproject.toml
    (which typically only declares scientific runtime deps, not test infrastructure).
    """
    project = tmp_path / "projects" / "thin"
    project.mkdir(parents=True)
    (project / "pyproject.toml").write_text(
        '[project]\nname = "thin"\ndependencies = ["numpy>=1.26"]\n',
        encoding="utf-8",
    )

    cmd = build_project_pytest_command(project, ["tests/", "--timeout=120"])
    # The base test-runner packages plus the workspace-pinned coverage package
    # must appear as --with arguments.
    assert "--with" in cmd
    with_values = [cmd[i + 1] for i, c in enumerate(cmd) if c == "--with"]
    assert "pytest" in with_values
    assert "pytest-cov" in with_values
    assert "pytest-timeout" in with_values
    assert "pytest-xdist" in with_values
    assert "pytest-benchmark" in with_values
    assert f"coverage=={version('coverage')}" in with_values


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
    # cov path is now ABSOLUTE so pytest resolves it correctly when
    # ``uv run --directory`` sets the subprocess CWD to the project directory.
    assert f"--cov={src.resolve()}" in joined
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


# ── pytest-xdist parallelism (opt-in) ───────────────────────────────────────


def test_resolve_xdist_args_defaults_to_serial(monkeypatch: pytest.MonkeyPatch) -> None:
    """No arg and no env var ⇒ serial (empty), preserving current behavior."""
    monkeypatch.delenv(ENV_XDIST_WORKERS, raising=False)
    assert resolve_xdist_args() == []
    assert resolve_xdist_args(None) == []


def test_resolve_xdist_args_auto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_XDIST_WORKERS, raising=False)
    assert resolve_xdist_args("auto") == [
        "-n",
        "auto",
        "--dist",
        "worksteal",
        "--benchmark-disable",
    ]


def test_resolve_xdist_args_positive_int(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_XDIST_WORKERS, raising=False)
    assert resolve_xdist_args(6) == [
        "-n",
        "6",
        "--dist",
        "worksteal",
        "--benchmark-disable",
    ]
    assert resolve_xdist_args("4") == [
        "-n",
        "4",
        "--dist",
        "worksteal",
        "--benchmark-disable",
    ]


def test_resolve_xdist_args_env_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """PYTEST_XDIST_WORKERS is honoured only when no explicit arg is passed."""
    monkeypatch.setenv(ENV_XDIST_WORKERS, "auto")
    assert resolve_xdist_args() == [
        "-n",
        "auto",
        "--dist",
        "worksteal",
        "--benchmark-disable",
    ]
    monkeypatch.setenv(ENV_XDIST_WORKERS, "3")
    assert resolve_xdist_args() == [
        "-n",
        "3",
        "--dist",
        "worksteal",
        "--benchmark-disable",
    ]


def test_resolve_xdist_args_explicit_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_XDIST_WORKERS, "auto")
    # Explicit serial request wins over an env var that would parallelize.
    assert resolve_xdist_args(1) == []
    assert resolve_xdist_args(8) == [
        "-n",
        "8",
        "--dist",
        "worksteal",
        "--benchmark-disable",
    ]


def test_resolve_xdist_args_one_worker_is_serial(monkeypatch: pytest.MonkeyPatch) -> None:
    """A single worker is pure xdist overhead — treat as serial."""
    monkeypatch.delenv(ENV_XDIST_WORKERS, raising=False)
    assert resolve_xdist_args(1) == []
    assert resolve_xdist_args("1") == []


def test_resolve_xdist_args_zero_and_invalid_are_serial(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_XDIST_WORKERS, raising=False)
    assert resolve_xdist_args(0) == []
    assert resolve_xdist_args("0") == []
    assert resolve_xdist_args("nonsense") == []
    assert resolve_xdist_args("") == []


def test_build_union_pytest_command_omits_xdist_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Default union command stays serial — no ``-n`` regression."""
    monkeypatch.delenv(ENV_XDIST_WORKERS, raising=False)
    repo = tmp_path / "repo"
    project = repo / "projects" / "templates" / "demo"
    (project / "src").mkdir(parents=True)
    tests = project / "tests"
    tests.mkdir(parents=True)

    cmd = build_union_pytest_command(repo, project, tests, is_first=True, marker_expr=None, timeout=30)
    assert "-n" not in cmd


def test_build_union_pytest_command_injects_xdist_when_parallel(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    project = repo / "projects" / "templates" / "demo"
    (project / "src").mkdir(parents=True)
    tests = project / "tests"
    tests.mkdir(parents=True)

    cmd_auto = build_union_pytest_command(
        repo, project, tests, is_first=True, marker_expr=None, timeout=30, parallel="auto"
    )
    joined = " ".join(cmd_auto)
    assert "-n auto" in joined
    assert "--dist worksteal" in joined
    assert "--benchmark-disable" in cmd_auto

    cmd_n = build_union_pytest_command(repo, project, tests, is_first=True, marker_expr=None, timeout=30, parallel=4)
    assert "-n" in cmd_n and "4" in cmd_n
    assert "--dist" in cmd_n and "worksteal" in cmd_n
    assert "--benchmark-disable" in cmd_n
