"""Tests for ``infrastructure.core.test_runner.run_per_project_pytest``.

These tests build a synthetic two-project tree under ``tmp_path`` and exercise
``run_per_project_pytest`` end-to-end with real ``pytest`` subprocesses — no
mocks. They cover the contract documented in the docstring: per-project loop,
combined coverage gate, ``--cov-append`` accumulation, and a single
``COVERAGE_FILE`` traced across every project.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from infrastructure.core.test_runner import (
    DEFAULT_COVERAGE_FILE,
    DEFAULT_FAIL_UNDER,
    run_per_project_pytest,
)


def _write_project(
    repo_root: Path,
    name: str,
    *,
    fail: bool = False,
    extra_module: str | None = None,
) -> None:
    """Create ``projects/<name>/`` with ``src/`` and ``tests/`` directories.

    The module under ``src/`` exposes a single function whose value is
    asserted by a test in ``tests/test_basic.py``. When ``fail=True`` the
    assertion is intentionally wrong so the project's pytest run fails.
    """
    project_root = repo_root / "projects" / name
    src_dir = project_root / "src"
    tests_dir = project_root / "tests"
    src_dir.mkdir(parents=True)
    tests_dir.mkdir()

    module_name = extra_module or f"mod_{name}"
    (src_dir / "__init__.py").write_text("")
    (src_dir / f"{module_name}.py").write_text(
        dedent(
            f"""
            \"\"\"Tiny module under test for project '{name}'.\"\"\"


            def value() -> int:
                return 42
            """
        ).lstrip()
    )

    (tests_dir / "__init__.py").write_text("")
    expected = "42" if not fail else "999"
    (tests_dir / "conftest.py").write_text(
        dedent(
            f"""
            \"\"\"Project-local conftest for '{name}'.

            Both projects deliberately ship a conftest.py here so the test
            asserts that ``run_per_project_pytest`` invokes one pytest
            process per project (otherwise pytest refuses to register two
            conftest plugins with the same basename).
            \"\"\"

            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            """
        ).lstrip()
    )
    (tests_dir / "test_basic.py").write_text(
        dedent(
            f"""
            from {module_name} import value


            def test_value() -> None:
                assert value() == {expected}
            """
        ).lstrip()
    )


def _write_template_repo_skeleton(repo_root: Path) -> None:
    """Create the minimal ``infrastructure/`` and ``projects/`` skeleton.

    ``run_per_project_pytest`` calls
    :func:`infrastructure.project.discovery.discover_projects` with the
    synthetic ``repo_root`` when no explicit ``projects=`` argument is
    given; that helper requires ``projects/`` to exist. The infrastructure
    package itself is imported from the real installation, not from
    ``tmp_path``.
    """
    (repo_root / "projects").mkdir()


def _coverage_lines_recorded(coverage_file: Path) -> int:
    """Return the number of lines recorded in a ``.coverage`` SQLite file.

    Uses the public ``coverage.CoverageData`` API rather than poking the
    SQLite file directly so the test stays robust across coverage versions.
    """
    from coverage import CoverageData

    data = CoverageData(basename=str(coverage_file))
    data.read()
    total = 0
    for filename in data.measured_files():
        executed = data.lines(filename) or []
        total += len(executed)
    return total


@pytest.fixture()
def synthetic_repo(tmp_path: Path) -> Path:
    _write_template_repo_skeleton(tmp_path)
    return tmp_path


def test_run_per_project_pytest_all_passing(synthetic_repo: Path) -> None:
    """Both projects pass → exit 0; combined coverage file is created."""
    _write_project(synthetic_repo, "alpha", fail=False, extra_module="mod_alpha")
    _write_project(synthetic_repo, "beta", fail=False, extra_module="mod_beta")

    # Use a low fail-under so the synthetic <100% coverage still passes the gate.
    rc = run_per_project_pytest(
        synthetic_repo,
        projects=["alpha", "beta"],
        fail_under=1,
        timeout=60,
    )
    assert rc == 0

    coverage_file = synthetic_repo / DEFAULT_COVERAGE_FILE
    assert coverage_file.exists(), "Combined coverage data file should be created"


def test_run_per_project_pytest_one_failing(synthetic_repo: Path) -> None:
    """A failing project → non-zero exit code from the orchestrator."""
    _write_project(synthetic_repo, "alpha", fail=False, extra_module="mod_alpha")
    _write_project(synthetic_repo, "beta", fail=True, extra_module="mod_beta")

    rc = run_per_project_pytest(
        synthetic_repo,
        projects=["alpha", "beta"],
        fail_under=1,
        timeout=60,
    )
    assert rc != 0


def test_coverage_accumulates_across_projects(synthetic_repo: Path) -> None:
    """``--cov-append`` should make the second project add to the first's traces.

    We run the suite once with both projects and verify that the combined
    coverage file references files from *both* projects' ``src/`` trees —
    proving ``--cov-append`` was honoured for the second project.
    """
    _write_project(synthetic_repo, "alpha", fail=False, extra_module="mod_alpha")
    _write_project(synthetic_repo, "beta", fail=False, extra_module="mod_beta")

    rc = run_per_project_pytest(
        synthetic_repo,
        projects=["alpha", "beta"],
        fail_under=1,
        timeout=60,
    )
    assert rc == 0

    coverage_file = synthetic_repo / DEFAULT_COVERAGE_FILE
    assert coverage_file.exists()

    from coverage import CoverageData

    data = CoverageData(basename=str(coverage_file))
    data.read()
    measured = list(data.measured_files())
    assert any("mod_alpha" in f for f in measured), f"Coverage missing alpha traces; measured={measured}"
    assert any("mod_beta" in f for f in measured), (
        f"Coverage missing beta traces (--cov-append did not accumulate); measured={measured}"
    )


def test_skip_projects_excludes_named_project(synthetic_repo: Path) -> None:
    """A project listed in ``skip_projects`` should not be invoked at all."""
    _write_project(synthetic_repo, "alpha", fail=False, extra_module="mod_alpha")
    # 'gamma' is intentionally written to fail; if it were *not* skipped the
    # orchestrator would return non-zero. We expect skip_projects to drop it.
    _write_project(synthetic_repo, "gamma", fail=True, extra_module="mod_gamma")

    rc = run_per_project_pytest(
        synthetic_repo,
        projects=["alpha", "gamma"],
        skip_projects=("gamma",),
        fail_under=1,
        timeout=60,
    )
    assert rc == 0

    coverage_file = synthetic_repo / DEFAULT_COVERAGE_FILE
    from coverage import CoverageData

    data = CoverageData(basename=str(coverage_file))
    data.read()
    measured = list(data.measured_files())
    assert not any("mod_gamma" in f for f in measured), (
        f"Skipped project should not appear in coverage; measured={measured}"
    )


def test_default_fail_under_constant_matches_repo_threshold() -> None:
    """The default fail-under should match the repo-wide 90% project gate."""
    assert DEFAULT_FAIL_UNDER == 90
