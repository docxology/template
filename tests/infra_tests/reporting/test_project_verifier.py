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
from infrastructure.reporting.pipeline_test_runner import execute_test_pipeline


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
            requires-python = ">=3.12"
            dependencies = []

            [project.optional-dependencies]
            dev = ["coverage>=7"]

            [tool.coverage.run]
            source = ["src"]
            branch = true

            [tool.coverage.report]
            fail_under = 90

            [tool.template]
            project_test_command = ["python", "scripts/verify.py"]
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
        ("python", "scripts/verify.py"),
        coverage_floor=90,
        timeout_seconds=120,
    )

    assert exit_code == 0
    assert results["passed"] == results["total"] == 1
    assert results["coverage_percent"] >= 90
    coverage_json = json.loads((project / "coverage_project.json").read_text(encoding="utf-8"))
    assert coverage_json["totals"]["percent_covered"] >= 90


@pytest.mark.timeout(180)
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
def test_declared_verifier_rejects_success_without_fresh_receipt(tmp_path: Path) -> None:
    project = _write_verifier_project(tmp_path, write_receipt=False)

    with pytest.raises(ProjectVerifierError, match="fresh regular-file receipt"):
        run_declared_project_verifier(
            tmp_path,
            project,
            "templates/demo",
            ("python", "scripts/verify.py"),
            coverage_floor=90,
            timeout_seconds=120,
        )


def test_declared_verifier_rejects_shell_and_script_escape(tmp_path: Path) -> None:
    project = _write_verifier_project(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("raise SystemExit(0)\n", encoding="utf-8")
    escape = project / "scripts" / "escape.py"
    escape.symlink_to(outside)

    with pytest.raises(ProjectVerifierError, match="must use"):
        validate_project_test_command(project, ("bash", "-c", "true"))
    with pytest.raises(ProjectVerifierError, match="resolve inside"):
        validate_project_test_command(
            project,
            ("python", "scripts/escape.py"),
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
            ("python", "scripts/verify.py"),
            coverage_floor=90,
            timeout_seconds=120,
        )

    assert not external_target.exists()


def test_declared_verifier_binds_existing_interpreter_without_acquisition(tmp_path: Path) -> None:
    import sys

    declared = ("python", "scripts/verify.py", "--release")
    effective = build_project_verifier_execution_command(declared, tmp_path)
    assert effective[0:3] == (str(Path(sys.executable).absolute()), "-I", "-c")
    assert "runpy.run_path" in effective[3]
    assert effective[-1] == "--release"
    assert "uv" not in effective and "--with" not in effective and "--extra" not in effective


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
def test_declared_verifier_independently_rejects_coverage_below_floor(tmp_path: Path) -> None:
    project = _write_verifier_project(tmp_path)

    (project / "src/demo_mod.py").write_text("def answer():\n    return 7\ndef uncovered():\n    return 9\n")
    with pytest.raises(ProjectVerifierError, match="below the declared 90.00% floor"):
        run_declared_project_verifier(
            tmp_path,
            project,
            "templates/demo",
            ("python", "scripts/verify.py"),
            coverage_floor=90,
            timeout_seconds=120,
        )


@pytest.mark.parametrize(
    "retired",
    [
        ("uv", "run", "python", "scripts/verify.py"),
        ("uv", "run", "--extra", "dev", "python", "scripts/verify.py"),
        ("python", "--extra", "dev", "scripts/verify.py"),
    ],
)
def test_retired_acquisition_declarations_fail_before_execution(tmp_path: Path, retired: tuple[str, ...]) -> None:
    project = _write_verifier_project(tmp_path)
    prior_coverage = project / ".coverage"
    prior_coverage.write_bytes(b"retained prior verifier evidence")
    with pytest.raises(ProjectVerifierError) as error:
        run_declared_project_verifier(tmp_path, project, "active/demo", retired, coverage_floor=90)
    assert error.value.exit_code == 2
    assert prior_coverage.read_bytes() == b"retained prior verifier evidence"


def test_invalid_declared_stage_preserves_prior_coverage(tmp_path: Path) -> None:
    from infrastructure.reporting.pipeline_test_runner import run_project_tests

    project = _write_verifier_project(tmp_path)
    metadata = project / "pyproject.toml"
    metadata.write_text(metadata.read_text().replace('["python", "scripts/verify.py"]', '["bash", "true"]'))
    prior_coverage = project / ".coverage"
    prior_coverage.write_bytes(b"retained prior coverage")
    code, results = run_project_tests(tmp_path, "active/demo")
    assert code == 2
    assert results["original_exit_code"] is None
    assert prior_coverage.read_bytes() == b"retained prior coverage"


@pytest.mark.parametrize("child_exit", [2, 7, 75, 124, 130])
@pytest.mark.timeout(90)
def test_custom_child_original_exit_survives_adapter(tmp_path: Path, child_exit: int) -> None:
    from infrastructure.reporting.pipeline_test_runner import run_project_tests

    project = _write_verifier_project(tmp_path)
    (project / "scripts/verify.py").write_text(f"raise SystemExit({child_exit})\n")
    code, results = run_project_tests(tmp_path, "active/demo")
    assert code == (child_exit if child_exit in (75, 124, 130) else 1)
    assert results["original_exit_code"] == child_exit


@pytest.mark.parametrize("timeout", [False, 0, -1, float("nan"), float("inf")])
def test_invalid_verifier_deadline_is_configuration_error(tmp_path: Path, timeout: float) -> None:
    project = _write_verifier_project(tmp_path)
    with pytest.raises(ProjectVerifierError) as error:
        run_declared_project_verifier(
            tmp_path,
            project,
            "active/demo",
            ("python", "scripts/verify.py"),
            coverage_floor=90,
            timeout_seconds=timeout,
        )
    assert error.value.exit_code == 2
    assert not (project / ".coverage").exists()


@pytest.mark.timeout(90)
def test_nominated_missing_runtime_blocks_without_fallback(tmp_path: Path) -> None:
    from infrastructure.reporting.pipeline_test_runner import run_project_tests

    project = _write_verifier_project(tmp_path)
    (project / ".venv").mkdir()
    prior_coverage = project / ".coverage"
    prior_coverage.write_bytes(b"retained prior verifier evidence")
    code, _results = run_project_tests(tmp_path, "active/demo")
    assert code == 75
    assert prior_coverage.read_bytes() == b"retained prior verifier evidence"


@pytest.mark.timeout(90)
def test_coverage_validation_consumes_remaining_whole_budget(tmp_path: Path) -> None:
    project = _write_verifier_project(tmp_path)
    config = project / "pyproject.toml"
    config.write_text(config.read_text().replace('source = ["src"]', 'source = ["src"]\nplugins = ["slow_plugin"]'))
    (project / "slow_plugin.py").write_text("import time\ndef coverage_init(reg, options):\n    time.sleep(30)\n")
    script = project / "scripts/verify.py"
    source = script.read_text().replace(
        'config_file=str(ROOT / "pyproject.toml"),', 'config_file=False, source=[str(ROOT / "src")], branch=True,'
    )
    source += '\n(ROOT / "child_finished").write_text("actual child completed")\n'
    script.write_text(source)
    with pytest.raises(ProjectVerifierError) as error:
        run_declared_project_verifier(
            tmp_path, project, "active/demo", ("python", "scripts/verify.py"), coverage_floor=90, timeout_seconds=20
        )
    assert error.value.exit_code == 124
    assert error.value.original_exit_code == 0
    assert (project / "child_finished").read_text() == "actual child completed"


@pytest.mark.parametrize("script", ["", ".", "scripts", "scripts/."])
def test_empty_or_directory_script_is_invocation_error(tmp_path: Path, script: str) -> None:
    project = _write_verifier_project(tmp_path)
    with pytest.raises(ProjectVerifierError) as refused:
        run_declared_project_verifier(tmp_path, project, "active/demo", ("python", script), coverage_floor=90)
    assert refused.value.exit_code == 2
    assert refused.value.original_exit_code is None
    assert not (project / ".coverage").exists()


@pytest.mark.parametrize("floor", [False, -1, 101, float("nan"), float("inf")])
def test_invalid_coverage_floor_refuses_before_execution(tmp_path: Path, floor: float) -> None:
    project = _write_verifier_project(tmp_path)
    with pytest.raises(ProjectVerifierError) as refused:
        run_declared_project_verifier(
            tmp_path, project, "active/demo", ("python", "scripts/verify.py"), coverage_floor=floor
        )
    assert refused.value.exit_code == 2
    assert refused.value.original_exit_code is None
    assert not (project / ".coverage").exists()
