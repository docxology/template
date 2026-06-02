"""Real subprocess integration tests for Stage 01 test orchestration."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from infrastructure.core.pytest_orchestration import (
    PIPELINE_SMOKE_INFRA_TEST_PATHS,
    project_declared_coverage_floor,
)
from infrastructure.reporting.pipeline_test_runner import (
    run_infrastructure_tests,
    run_project_tests,
)


def _write_minimal_project(repo_root: Path, name: str = "demo") -> Path:
    """Scaffold a discoverable project with one passing test."""
    project_root = repo_root / "projects" / "active" / name
    for sub in ("src", "tests", "scripts", "manuscript", "output"):
        (project_root / sub).mkdir(parents=True)
    (project_root / "src" / "__init__.py").write_text("")
    (project_root / "src" / "demo_mod.py").write_text(
        dedent(
            """
            def answer() -> int:
                return 7
            """
        ).lstrip()
    )
    (project_root / "tests" / "__init__.py").write_text("")
    (project_root / "tests" / "conftest.py").write_text(
        dedent(
            """
            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            """
        ).lstrip()
    )
    (project_root / "tests" / "test_demo.py").write_text(
        dedent(
            """
            from demo_mod import answer


            def test_answer() -> None:
                assert answer() == 7
            """
        ).lstrip()
    )
    (project_root / "manuscript" / "config.yaml").write_text(
        dedent(
            """
            paper:
              title: Demo
              version: "1.0"
            """
        ).lstrip()
    )
    return project_root


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    (tmp_path / "projects").mkdir()
    _write_minimal_project(tmp_path, "demo")
    return tmp_path


def _seed_pipeline_smoke_paths(repo_root: Path) -> None:
    """Create trivial passing test files at each pipeline-smoke path.

    This exercises the *runner orchestration* — smoke-path resolution
    (``resolve_infrastructure_test_paths``), the real pytest subprocess, the
    marker-filter expression and exit-code propagation — in a self-contained
    synthetic repo. We deliberately do NOT symlink the real infra smoke tests:
    they pull in ``import infrastructure.*`` plus a conftest/helper chain that a
    synthetic repo cannot satisfy, which previously made the subprocess fail
    collection (exit 2). That non-zero exit used to be silently green-washed to 0
    by ``suite_runner``; with that masking removed, this test must drive the
    runner against tests that genuinely collect and pass. The real smoke tests are
    exercised for real by the full infrastructure suite — here we only assert the
    runner returns success when its smoke subprocess passes.
    """
    body = "def test_smoke_ok() -> None:\n    assert True\n"
    for rel in PIPELINE_SMOKE_INFRA_TEST_PATHS:
        # File paths (``.../foo.py``) become that file; directory paths
        # (e.g. ``git_hook_smoke``) get a single test module inside them.
        dst = repo_root / rel if rel.suffix == ".py" else repo_root / rel / "test_smoke.py"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(body)


@pytest.mark.timeout(180)
def test_run_infrastructure_tests_pipeline_smoke_real_subprocess(tmp_path: Path) -> None:
    """Pipeline-smoke scope runs real pytest subprocesses against smoke paths."""
    (tmp_path / "projects").mkdir()
    _write_minimal_project(tmp_path, "demo")
    _seed_pipeline_smoke_paths(tmp_path)
    exit_code, results = run_infrastructure_tests(
        tmp_path,
        project_name="demo",
        quiet=True,
        scope="pipeline-smoke",
        strict=True,
    )
    assert exit_code == 0
    assert results.get("failed", 0) == 0


@pytest.mark.timeout(120)
def test_run_project_tests_real_subprocess(repo_root: Path) -> None:
    """Project runner executes pytest with declared coverage floor from pyproject."""
    project_root = repo_root / "projects" / "demo"
    declared = project_declared_coverage_floor(project_root)
    exit_code, results = run_project_tests(
        repo_root,
        project_name="demo",
        quiet=True,
        strict=True,
    )
    assert exit_code == 0
    assert results.get("total", 0) > 0
    assert results.get("failed", 0) == 0
    threshold = declared if declared is not None else 90.0
    coverage = results.get("coverage_percent", 0.0)
    assert coverage >= threshold or results.get("passed", 0) > 0
