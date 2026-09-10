"""Per-project pytest orchestration tests for ``run_per_project_pytest``.

These tests build a synthetic two-project tree under ``tmp_path`` and exercise
``run_per_project_pytest`` end-to-end with real ``pytest`` subprocesses — no
mocks. They cover the contract documented in the docstring: per-project loop,
combined coverage gate, isolated per-project coverage files, and a final
union that cannot inherit the enclosing test process's ``COVERAGE_FILE``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.core.testing.test_runner import (
    DEFAULT_COVERAGE_FILE,
    _contains_tests,
    run_per_project_pytest,
)
from ._test_runner_helpers import _write_project

pytestmark = pytest.mark.timeout(120)


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


def test_contains_tests_accepts_suffix_test_modules(tmp_path: Path) -> None:
    """The isolated runner recognizes both supported pytest naming conventions."""
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "helpers_test.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    assert _contains_tests(tests_dir) is True


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


@pytest.mark.slow
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
