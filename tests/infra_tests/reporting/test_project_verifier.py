"""Real-process tests for the explicit single-project verifier contract."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from infrastructure.reporting.project_verifier import (
    ProjectVerifierError,
    _load_receipt,
    build_project_verifier_execution_command,
    run_declared_project_verifier,
    validate_project_test_command,
)
from infrastructure.core.pytest_profiles import test_runner_dependency_specs
from infrastructure.reporting.pipeline_test_runner import execute_test_pipeline


@pytest.fixture
def unlocked_project_uv_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the synthetic no-lock project isolated from repository frozen policy."""
    # Canonical projects carry uv.lock and continue to honor UV_FROZEN. These
    # disposable verifier projects intentionally exercise uv's clean bootstrap.
    monkeypatch.delenv("UV_FROZEN", raising=False)


def _write_verifier_project(repo_root: Path, *, write_receipt: bool = True) -> Path:
    project = repo_root / "projects" / "active" / "demo"
    for part in ("src", "tests", "scripts", "output"):
        (project / part).mkdir(parents=True, exist_ok=True)
    (project / "src" / "demo_mod.py").write_text(
        "def answer() -> int:\n    return 7\n",
        encoding="utf-8",
    )
    (project / "tests" / "test_demo.py").write_text(
        "from demo_mod import answer\n\ndef test_answer() -> None:\n    assert answer() == 7\n",
        encoding="utf-8",
    )
    (project / "pyproject.toml").write_text(
        dedent(
            """
            [project]
            name = "demo-verifier-project"
            version = "0.0.0"
            requires-python = ">=3.10"
            dependencies = []

            [project.optional-dependencies]
            dev = ["coverage>=7"]

            [tool.coverage.run]
            source = ["src"]
            branch = true

            [tool.coverage.report]
            fail_under = 90

            [tool.template]
            project_test_command = ["uv", "run", "--extra", "dev", "python", "scripts/verify.py"]
            """
        ).lstrip(),
        encoding="utf-8",
    )
    receipt_write = """
if WRITE_RECEIPT:
    receipt = {
        "schema_version": "template/project-test-receipt/1",
        "project": os.environ["TEMPLATE_PROJECT_TEST_PROJECT"],
        "run_id": os.environ["TEMPLATE_PROJECT_TEST_RUN_ID"],
        "command_sha256": os.environ["TEMPLATE_PROJECT_TEST_COMMAND_SHA256"],
        "coverage_percent": percent,
        "results": {
            "passed": 1,
            "failed": 0,
            "skipped": 0,
            "total": 1,
            "collection_errors": 0,
            "discovery_count": 1,
            "warnings": 0,
        },
    }
    Path(os.environ["TEMPLATE_PROJECT_TEST_RECEIPT"]).write_text(
        json.dumps(receipt), encoding="utf-8"
    )
"""
    verifier_source = (
        dedent(
            f"""
            import io
            import json
            import os
            import sys
            from pathlib import Path

            from coverage import Coverage

            ROOT = Path(__file__).resolve().parents[1]
            assert "PYTEST_ADDOPTS" not in os.environ
            assert "PYTEST_PLUGINS" not in os.environ
            assert "PYTEST_DISABLE_PLUGIN_AUTOLOAD" not in os.environ
            assert "UV_FROZEN" not in os.environ
            sys.path.insert(0, str(ROOT / "src"))
            coverage = Coverage(
                data_file=str(ROOT / ".coverage"),
                config_file=str(ROOT / "pyproject.toml"),
            )
            coverage.start()
            from demo_mod import answer
            assert answer() == 7
            coverage.stop()
            coverage.save()
            percent = float(coverage.report(file=io.StringIO()))
            WRITE_RECEIPT = {write_receipt!r}
            """
        ).lstrip()
        + dedent(receipt_write).lstrip()
    )
    (project / "scripts" / "verify.py").write_text(
        verifier_source,
        encoding="utf-8",
    )
    return project


@pytest.mark.timeout(180)
@pytest.mark.usefixtures("unlocked_project_uv_environment")
def test_declared_verifier_requires_real_receipt_and_independent_coverage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = _write_verifier_project(tmp_path)
    monkeypatch.setenv("PYTEST_ADDOPTS", "-k hidden-selection")
    monkeypatch.setenv("PYTEST_PLUGINS", "selection_rewriter")
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

    exit_code, results = run_declared_project_verifier(
        tmp_path,
        project,
        "templates/demo",
        ("uv", "run", "--extra", "dev", "python", "scripts/verify.py"),
        coverage_floor=90,
        timeout_seconds=120,
    )

    assert exit_code == 0
    assert results["passed"] == results["total"] == 1
    assert results["coverage_percent"] >= 90
    coverage_json = json.loads((project / "coverage_project.json").read_text(encoding="utf-8"))
    assert coverage_json["totals"]["percent_covered"] >= 90


@pytest.mark.timeout(180)
@pytest.mark.usefixtures("unlocked_project_uv_environment")
def test_single_project_stage_dispatches_declared_verifier_and_writes_report(tmp_path: Path) -> None:
    project = _write_verifier_project(tmp_path)

    exit_code = execute_test_pipeline(
        "active/demo",
        tmp_path,
        run_infra=False,
        run_project=True,
        quiet=True,
        include_slow=False,
        include_long_running=False,
        include_ollama_tests=False,
        strict=True,
    )

    assert exit_code == 0
    report = json.loads((project / "output" / "reports" / "test_results.json").read_text(encoding="utf-8"))
    assert report["summary"]["all_passed"] is True
    assert report["summary"]["total_tests"] == 1
    assert report["summary"]["project_coverage"] >= 90


@pytest.mark.timeout(180)
@pytest.mark.usefixtures("unlocked_project_uv_environment")
def test_declared_verifier_rejects_success_without_fresh_receipt(tmp_path: Path) -> None:
    project = _write_verifier_project(tmp_path, write_receipt=False)

    with pytest.raises(ProjectVerifierError, match="fresh regular-file receipt"):
        run_declared_project_verifier(
            tmp_path,
            project,
            "templates/demo",
            ("uv", "run", "--extra", "dev", "python", "scripts/verify.py"),
            coverage_floor=90,
            timeout_seconds=120,
        )


def test_declared_verifier_rejects_shell_and_script_escape(tmp_path: Path) -> None:
    project = _write_verifier_project(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("raise SystemExit(0)\n", encoding="utf-8")
    escape = project / "scripts" / "escape.py"
    escape.symlink_to(outside)

    with pytest.raises(ProjectVerifierError, match="explicit uv-run"):
        validate_project_test_command(project, ("bash", "-c", "true"))
    with pytest.raises(ProjectVerifierError, match="resolve inside"):
        validate_project_test_command(
            project,
            ("uv", "run", "--extra", "dev", "python", "scripts/escape.py"),
        )


def test_declared_verifier_rejects_broken_coverage_symlink_before_launch(tmp_path: Path) -> None:
    project = _write_verifier_project(tmp_path)
    external_target = tmp_path / "external" / "coverage.db"
    (project / ".coverage").symlink_to(external_target)

    with pytest.raises(ProjectVerifierError, match="symlinked .coverage"):
        run_declared_project_verifier(
            tmp_path,
            project,
            "templates/demo",
            ("uv", "run", "--extra", "dev", "python", "scripts/verify.py"),
            coverage_floor=90,
            timeout_seconds=120,
        )

    assert not external_target.exists()


def test_declared_verifier_overlays_exact_workspace_runner_versions() -> None:
    declared = ("uv", "run", "--extra", "dev", "python", "scripts/verify.py", "--release")

    effective = build_project_verifier_execution_command(declared)

    with_values = tuple(effective[index + 1] for index, part in enumerate(effective) if part == "--with")
    assert with_values == test_runner_dependency_specs()
    assert effective[-5:] == ("--extra", "dev", "python", "scripts/verify.py", "--release")


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"schema_version": "wrong"}, "schema_version mismatch"),
        ({"project": "wrong"}, "project mismatch"),
        ({"run_id": "old"}, "run_id mismatch"),
        ({"command_sha256": "wrong"}, "command_sha256 mismatch"),
        ({"coverage_percent": "unknown"}, "coverage_percent must be a finite number"),
    ],
)
def test_receipt_identity_and_coverage_fields_fail_closed(
    tmp_path: Path,
    mutation: dict[str, object],
    message: str,
) -> None:
    payload: dict[str, object] = {
        "schema_version": "template/project-test-receipt/1",
        "project": "active/demo",
        "run_id": "fresh",
        "command_sha256": "abc",
        "coverage_percent": 100.0,
        "results": {
            "passed": 1,
            "failed": 0,
            "skipped": 0,
            "total": 1,
            "collection_errors": 0,
            "discovery_count": 1,
            "warnings": 0,
        },
    }
    payload.update(mutation)
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ProjectVerifierError, match=message):
        _load_receipt(
            receipt,
            project_name="active/demo",
            run_id="fresh",
            command_sha256="abc",
        )


def test_receipt_rejects_failed_or_vacuous_outcomes(tmp_path: Path) -> None:
    base = {
        "schema_version": "template/project-test-receipt/1",
        "project": "active/demo",
        "run_id": "fresh",
        "command_sha256": "abc",
        "coverage_percent": 100.0,
    }
    receipt = tmp_path / "receipt.json"
    for results, message in (
        (
            {
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "total": 0,
                "collection_errors": 0,
                "discovery_count": 0,
                "warnings": 0,
            },
            "vacuous zero-test run",
        ),
        (
            {
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "total": 1,
                "collection_errors": 0,
                "discovery_count": 1,
                "warnings": 0,
            },
            "reports failed=1",
        ),
    ):
        receipt.write_text(json.dumps({**base, "results": results}), encoding="utf-8")
        with pytest.raises(ProjectVerifierError, match=message):
            _load_receipt(
                receipt,
                project_name="active/demo",
                run_id="fresh",
                command_sha256="abc",
            )


@pytest.mark.timeout(180)
@pytest.mark.usefixtures("unlocked_project_uv_environment")
def test_declared_verifier_independently_rejects_coverage_below_floor(tmp_path: Path) -> None:
    project = _write_verifier_project(tmp_path)

    with pytest.raises(ProjectVerifierError, match="below the declared 101.00% floor"):
        run_declared_project_verifier(
            tmp_path,
            project,
            "templates/demo",
            ("uv", "run", "--extra", "dev", "python", "scripts/verify.py"),
            coverage_floor=101,
            timeout_seconds=120,
        )
