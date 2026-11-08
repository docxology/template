"""Per-project pytest orchestration tests for ``run_per_project_pytest``.

These tests build a synthetic two-project tree under ``tmp_path`` and exercise
``run_per_project_pytest`` end-to-end with real ``pytest`` subprocesses — no
mocks. They cover the contract documented in the docstring: per-project loop,
combined coverage gate, isolated per-project coverage files, and a final
union that cannot inherit the enclosing test process's ``COVERAGE_FILE``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infrastructure.core.testing.pytest_observations import DIRECTORY_ENV, NONCE_ENV, ROOT_ENV
from infrastructure.core.testing.pytest_profiles import (
    TestProfileName,
    build_profile_marker_expression,
    resolve_test_profile,
)
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


@pytest.mark.parametrize("profile", ["quick", "release", "exhaustive"])
def test_matrix_generated_profile_resolves_native_markers(
    synthetic_repo: Path, profile: TestProfileName, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_project(synthetic_repo, "native")
    project = synthetic_repo / "projects/native"
    (project / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        'addopts = "--strict-markers -m native_other"\n'
        'markers = ["native(payload): signature", "native_other: native default", "slow: opt in"]\n'
    )
    with (project / "tests/conftest.py").open("a") as stream:
        stream.write(
            "\nimport json\n"
            "def pytest_configure(config):\n"
            " config.addinivalue_line('markers', 'network(reason): native plugin service')\n"
            "def pytest_sessionfinish(session):\n"
            " (Path(__file__).parent.parent / 'selection.json').write_text(json.dumps({\n"
            "  'expression': session.config.option.markexpr,\n"
            "  'markers': session.config.getini('markers')}))\n"
        )
    with (project / "tests/test_basic.py").open("a") as stream:
        stream.write(
            "\nimport pytest\n"
            "@pytest.mark.native(payload='signature')\n"
            "@pytest.mark.slow\n"
            "def test_native_slow():\n assert value() == 42\n"
            "@pytest.mark.network(reason='service')\n"
            "def test_native_service():\n pytest.fail('excluded service ran')\n"
        )
    observations = synthetic_repo / "actual-pytest-receipts"
    monkeypatch.setenv("PYTEST_PLUGINS", "infrastructure.core.testing.pytest_receipt")
    monkeypatch.setenv(DIRECTORY_ENV, str(observations))
    monkeypatch.setenv(NONCE_ENV, f"native-{profile}")
    monkeypatch.setenv(ROOT_ENV, str(project))

    assert (
        run_per_project_pytest(
            synthetic_repo,
            projects=["native"],
            profile=profile,
            fail_under=1,
            timeout=60,
            receipt_path=synthetic_repo / "matrix-receipt.json",
        )
        == 0
    )
    actual = json.loads((project / "selection.json").read_text())
    assert "not network" in actual["expression"]
    assert ("not slow" in actual["expression"]) is (profile == "quick")
    assert "native_other" not in actual["expression"]
    registered = {row.split(":", 1)[0].split("(", 1)[0].strip() for row in actual["markers"]}
    assert {part.removeprefix("not ") for part in actual["expression"].split(" and ")} <= registered
    assert "requires_docker" not in registered
    receipt = json.loads(next(observations.glob("execution-*.json")).read_text())
    assert receipt["selection_profile"]["marker_expression"] == actual["expression"]
    assert len(receipt["selected"]) == (1 if profile == "quick" else 2)
    assert any(node.endswith("::test_native_service") for node in receipt["deselected"])
    matrix = json.loads((synthetic_repo / "matrix-receipt.json").read_text())
    assert matrix["marker_expression"] == build_profile_marker_expression(resolve_test_profile(profile))
    assert "not requires_docker" in matrix["marker_expression"]
    assert "not requires_docker" not in receipt["selection_profile"]["marker_expression"]


@pytest.mark.parametrize("expression", ["native", "unknown_native_expression"])
def test_matrix_explicit_marker_expression_remains_native_policy(synthetic_repo: Path, expression: str) -> None:
    _write_project(synthetic_repo, "native")
    project = synthetic_repo / "projects/native"
    (project / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\n"
        'addopts = "--strict-markers -m native_other"\n'
        'markers = ["native: explicit selection", "native_other: native default"]\n'
    )
    with (project / "tests/test_basic.py").open("a") as stream:
        stream.write("\nimport pytest\n@pytest.mark.native\ndef test_explicit_native():\n assert value() == 42\n")
    code = run_per_project_pytest(synthetic_repo, projects=["native"], marker_expr=expression, fail_under=1, timeout=60)
    assert (code == 0) is (expression == "native")
