"""Tests for ``infrastructure.core.test_runner.run_per_project_pytest``.

These tests build a synthetic two-project tree under ``tmp_path`` and exercise
``run_per_project_pytest`` end-to-end with real ``pytest`` subprocesses — no
mocks. They cover the contract documented in the docstring: per-project loop,
combined coverage gate, isolated per-project coverage files, and a final
union that cannot inherit the enclosing test process's ``COVERAGE_FILE``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest

from infrastructure.core.test_runner import (
    DEFAULT_COVERAGE_FILE,
    DEFAULT_FAIL_UNDER,
    run_per_project_pytest,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.timeout(120)


def _write_project(
    repo_root: Path,
    name: str,
    *,
    fail: bool = False,
    extra_module: str | None = None,
    sleep_seconds: float = 0.0,
    marker_file: Path | None = None,
    order_log: Path | None = None,
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
    marker_path = str(marker_file) if marker_file is not None else None
    order_log_path = str(order_log) if order_log is not None else None
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
            import time
            from pathlib import Path

            from {module_name} import value

            MARKER_PATH = {marker_path!r}
            ORDER_LOG_PATH = {order_log_path!r}


            def test_value() -> None:
                if {sleep_seconds!r}:
                    time.sleep({sleep_seconds!r})
                if MARKER_PATH:
                    Path(MARKER_PATH).write_text({name!r}, encoding="utf-8")
                if ORDER_LOG_PATH:
                    with Path(ORDER_LOG_PATH).open("a", encoding="utf-8") as handle:
                        handle.write({name!r} + "\\n")
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


def test_run_per_project_pytest_all_passing(synthetic_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Both projects pass → exit 0; combined coverage file is created."""
    # When this test runs inside the larger pipeline, the parent pytest
    # invocation may have set COVERAGE_FILE to a host-filesystem path
    # (e.g. ".coverage.infra"). _resolve_coverage_file honours that env
    # var, which would redirect the synthetic repo's coverage file off
    # tmp_path and break the assertion below. Clear it so the synthetic
    # run uses DEFAULT_COVERAGE_FILE inside ``synthetic_repo``.
    monkeypatch.delenv("COVERAGE_FILE", raising=False)

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


def test_run_per_project_pytest_continues_after_failure(synthetic_repo: Path) -> None:
    order_log = synthetic_repo / "order.log"
    _write_project(synthetic_repo, "alpha", fail=True, extra_module="mod_alpha", order_log=order_log)
    _write_project(synthetic_repo, "beta", fail=False, extra_module="mod_beta", order_log=order_log)

    rc = run_per_project_pytest(
        synthetic_repo,
        projects=["alpha", "beta"],
        fail_under=1,
        timeout=60,
    )

    assert rc != 0
    assert order_log.read_text(encoding="utf-8").splitlines() == ["alpha", "beta"]


def test_coverage_accumulates_across_projects(synthetic_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The final union contains traces from every isolated project run.

    We run the suite once with both projects and verify that the combined
    coverage file references files from *both* projects' ``src/`` trees —
    proving the post-run combine step was honoured for the second project.
    """
    # See test_run_per_project_pytest_all_passing for the same reasoning:
    # an outer pipeline run may pin COVERAGE_FILE to a host path and
    # silently redirect the synthetic suite's coverage data file off
    # tmp_path.
    monkeypatch.delenv("COVERAGE_FILE", raising=False)

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
        f"Coverage missing beta traces (isolated union did not accumulate); measured={measured}"
    )


def test_inherited_coverage_file_cannot_contaminate_union(
    synthetic_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A parent pytest-cov file is not reused by the public-project union."""
    _write_project(synthetic_repo, "alpha", fail=False, extra_module="mod_alpha")
    inherited = synthetic_repo / ".coverage.infra"
    monkeypatch.setenv("COVERAGE_FILE", str(inherited))

    assert run_per_project_pytest(synthetic_repo, projects=["alpha"], fail_under=1, timeout=60) == 0
    assert (synthetic_repo / DEFAULT_COVERAGE_FILE).is_file()
    assert not inherited.exists()


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


def test_discovered_project_roster_is_sorted_by_qualified_name(synthetic_repo: Path) -> None:
    order_log = synthetic_repo / "discovered-order.log"
    _write_project(
        synthetic_repo,
        "templates/beta",
        fail=False,
        extra_module="mod_beta",
        order_log=order_log,
    )
    _write_project(
        synthetic_repo,
        "templates/alpha",
        fail=False,
        extra_module="mod_alpha",
        order_log=order_log,
    )

    rc = run_per_project_pytest(
        synthetic_repo,
        fail_under=1,
        timeout=60,
    )

    assert rc == 0
    assert order_log.read_text(encoding="utf-8").splitlines() == [
        "templates/alpha",
        "templates/beta",
    ]


def test_run_per_project_pytest_continues_after_timeout(synthetic_repo: Path) -> None:
    marker_file = synthetic_repo / "beta-ran.txt"
    _write_project(
        synthetic_repo,
        "slowpoke",
        fail=False,
        extra_module="mod_slowpoke",
        sleep_seconds=10.0,
    )
    _write_project(
        synthetic_repo,
        "beta",
        fail=False,
        extra_module="mod_beta",
        marker_file=marker_file,
    )

    rc = run_per_project_pytest(
        synthetic_repo,
        projects=["slowpoke", "beta"],
        fail_under=1,
        timeout=60,
        subprocess_timeout_seconds=5,
    )

    assert rc != 0
    assert marker_file.read_text(encoding="utf-8") == "beta"


def test_run_per_project_pytest_rejects_nested_outer_and_inner_concurrency(synthetic_repo: Path) -> None:
    _write_project(synthetic_repo, "alpha", fail=False, extra_module="mod_alpha")

    with pytest.raises(ValueError, match="--project-workers=2"):
        run_per_project_pytest(
            synthetic_repo,
            projects=["alpha"],
            fail_under=1,
            timeout=60,
            project_workers=2,
            parallel="auto",
        )


def test_explicit_missing_project_fails_closed(synthetic_repo: Path) -> None:
    assert run_per_project_pytest(synthetic_repo, projects=["missing"], fail_under=100) == 1


def test_discovery_with_no_projects_fails_closed(synthetic_repo: Path) -> None:
    assert run_per_project_pytest(synthetic_repo, fail_under=100) == 1


def test_empty_tests_directory_is_not_runnable(synthetic_repo: Path) -> None:
    project = synthetic_repo / "projects" / "empty"
    (project / "src").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "src" / "__init__.py").write_text("", encoding="utf-8")

    assert run_per_project_pytest(synthetic_repo, projects=["empty"], fail_under=100) == 1


def test_allow_empty_requires_explicit_opt_in(synthetic_repo: Path) -> None:
    assert run_per_project_pytest(synthetic_repo, projects=[], fail_under=100, allow_empty=True) == 0


def test_default_fail_under_constant_matches_repo_threshold() -> None:
    """Combined-union project gate, reconciled to measured reality.

    Deliberately distinct from — and lower than — the per-project standalone
    90% floor (which exemplar projects meet). The combined number is
    structurally lower because per-project suites only cover their own
    ``src/`` while the union denominator spans every project included in the
    run. CI uses the public project scope; local runs may include rotating
    symlinked projects. Kept in lockstep with the ``DEFAULT_FAIL_UNDER``
    docstring/comment and the coverage docs in CLAUDE.md / AGENTS.md /
    .github/AGENTS.md (maintainer decision 2026-05-15).
    """
    assert DEFAULT_FAIL_UNDER == 75


def test_stage01_public_projects_flag_is_documented_in_help() -> None:
    """The Stage 01 CLI exposes public-scope all-projects validation."""
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "scripts/pipeline/stage_01_test.py", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode == 0
    assert "--public-projects" in proc.stdout
    assert "--profile" in proc.stdout
    assert "--project-workers" in proc.stdout


def test_stage01_parallel_flag_is_documented_in_help() -> None:
    """The Stage 01 CLI exposes opt-in pytest-xdist parallelism via -n/--parallel."""
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "scripts/pipeline/stage_01_test.py", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode == 0
    assert "--parallel" in proc.stdout
    assert "PYTEST_XDIST_WORKERS" in proc.stdout


def test_stage01_public_projects_requires_all_projects_mode() -> None:
    """The public-scope flag is not silently ignored on the wrong command."""
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "scripts/pipeline/stage_01_test.py", "--public-projects"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "--public-projects requires --project-only --all-projects" in proc.stderr


def test_stage01_invalid_profile_is_rejected() -> None:
    proc = subprocess.run(  # noqa: S603
        [sys.executable, "scripts/pipeline/stage_01_test.py", "--profile", "bogus"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "invalid choice" in proc.stderr


def test_stage01_invalid_project_workers_is_rejected() -> None:
    proc = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "scripts/pipeline/stage_01_test.py",
            "--project-only",
            "--all-projects",
            "--project-workers",
            "0",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "project-workers" in proc.stderr


def test_stage01_project_workers_requires_all_projects_mode() -> None:
    proc = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "scripts/pipeline/stage_01_test.py",
            "--project-workers",
            "2",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "--project-workers requires --project-only --all-projects" in proc.stderr


def test_stage01_rejects_hidden_nested_concurrency_from_env() -> None:
    env = os.environ.copy()
    env["PYTEST_XDIST_WORKERS"] = "2"
    proc = subprocess.run(  # noqa: S603
        [
            sys.executable,
            "scripts/pipeline/stage_01_test.py",
            "--project-only",
            "--all-projects",
            "--project-workers",
            "2",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert proc.returncode != 0
    assert "--project-workers=2" in proc.stderr
    assert "PYTEST_XDIST_WORKERS" in proc.stderr
