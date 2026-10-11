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


@pytest.mark.timeout(120)
def test_actual_selected_provider_inventory_binds_verifier_and_validator(tmp_path: Path) -> None:
    import os
    import sys
    import sysconfig
    import venv

    project = _write_verifier_project(tmp_path)
    metadata = project / "pyproject.toml"
    metadata.write_text(
        metadata.read_text().replace(
            "dependencies = []", 'dependencies = ["template-selected-verifier-provider==1.0.0"]'
        )
    )
    environment = project / ".venv"
    venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(environment)
    site = environment / (
        "Lib/site-packages"
        if os.name == "nt"
        else f"lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages"
    )
    (site / "prepared_dependencies.pth").write_text(sysconfig.get_path("purelib") + "\n")
    provider = site / "template_selected_verifier_provider"
    provider.mkdir()
    (provider / "__init__.py").write_text("VALUE = 7\n")
    verifier = project / "scripts/verify.py"
    verifier.write_text(
        "import template_selected_verifier_provider\nassert template_selected_verifier_provider.VALUE == 7\n"
        + verifier.read_text()
    )
    code, results = run_declared_project_verifier(
        tmp_path, project, "active/demo", ("python", "scripts/verify.py"), coverage_floor=90
    )
    assert code == 0
    assert results["original_exit_code"] == 0
    assert results["coverage_percent"] == 100


@pytest.mark.timeout(120)
def test_actual_validator_malformed_provider_spec_keeps_typed_refusal(tmp_path: Path) -> None:
    import os
    import subprocess
    import sys
    import uuid

    from infrastructure.core.testing.project_test_runtime import (
        project_test_audit_roots,
        project_test_deadline,
        project_test_import_paths,
    )

    project = _write_verifier_project(tmp_path)
    metadata = project / "pyproject.toml"
    metadata.write_text(
        metadata.read_text().replace("dependencies = []", 'dependencies = ["template-malformed-provider==1.0.0"]')
    )
    provider = project / "src/template_malformed_provider"
    provider.mkdir()
    (provider / "__init__.py").write_text("VALUE = 7\n")
    verifier = project / "scripts/verify.py"
    verifier.write_text(
        verifier.read_text().replace("coverage.start()", "coverage.start()\nimport template_malformed_provider")
    )
    receipt = tmp_path / "actual-receipt.json"
    run_id = uuid.uuid4().hex
    command_sha = "a" * 64
    environment = os.environ.copy()
    environment.update(
        TEMPLATE_PROJECT_TEST_RECEIPT=str(receipt),
        TEMPLATE_PROJECT_TEST_RUN_ID=run_id,
        TEMPLATE_PROJECT_TEST_PROJECT="active/demo",
        TEMPLATE_PROJECT_TEST_COMMAND_SHA256=command_sha,
    )
    body = subprocess.run(
        [sys.executable, "-I", str(project / "scripts/verify.py")],
        cwd=project,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert body.returncode == 0, body.stderr
    roots = project_test_audit_roots(project, interpreter=Path(sys.executable))
    request = tmp_path / "actual-validation.json"
    request.write_text(
        json.dumps(
            {
                "receipt_path": str(receipt),
                "project_root": str(project),
                "project_name": "active/demo",
                "run_id": run_id,
                "command_sha256": command_sha,
                "coverage_floor": 90,
                "result_path": str(tmp_path / "validation-result.json"),
                "audit_roots": [str(root) for root in roots],
                "deadline_monotonic": project_test_deadline(30),
                "selected_interpreter": str(Path(sys.executable).absolute()),
            }
        )
    )
    source = (
        "import sys,runpy; "
        f"sys.path[:0]={[str(path) for path in project_test_import_paths(project)]!r}; "
        "import template_malformed_provider; template_malformed_provider.__spec__=None; "
        f"sys.argv=['project_verifier','--validate-receipt',{str(request)!r}]; "
        "runpy.run_module('infrastructure.reporting.project_verifier',run_name='__main__')"
    )
    checked = subprocess.run(
        [sys.executable, "-I", "-c", source], cwd=project, env=environment, capture_output=True, text=True, timeout=30
    )
    assert checked.returncode == 75, checked.stderr
    assert "Local provider-root discovery refused" in checked.stdout + checked.stderr
    assert not (tmp_path / "validation-result.json").exists()


@pytest.mark.timeout(300)
def test_union_matrix_honors_declared_verifier_and_retains_bound_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real declared verifier and ordinary pytest both enter the final union."""
    import hashlib

    from coverage import CoverageData

    from infrastructure.core.testing.public_matrix_receipt import PublicMatrixReceipt
    from infrastructure.core.testing.test_runner import run_per_project_pytest
    from tests.infra_tests.core._test_runner_helpers import _write_project

    monkeypatch.delenv("COVERAGE_FILE", raising=False)
    project = _write_verifier_project(tmp_path)
    # The declared source command owns its selection; generic pytest must not
    # collect this deliberately failing module instead of invoking that command.
    (project / "tests/test_demo.py").write_text("raise AssertionError('generic path selected')\n")
    _write_project(tmp_path, "ordinary", extra_module="ordinary_mod")
    receipt_path = tmp_path / "matrix.json"
    combined = tmp_path / ".coverage.union"
    assert (
        run_per_project_pytest(
            tmp_path,
            projects=["active/demo", "ordinary"],
            fail_under=90,
            timeout=60,
            subprocess_timeout_seconds=120,
            coverage_file=combined,
            receipt_path=receipt_path,
            project_workers=2,
        )
        == 0
    )
    receipt = PublicMatrixReceipt.read(receipt_path)
    assert receipt.validate(("active/demo", "ordinary")) == []
    lanes = {lane.project_name: lane for lane in receipt.lanes}
    declared = lanes["active/demo"]
    binding = declared.coverage_database
    assert binding is not None
    database = Path(str(binding["path"]))
    assert database.is_file() and not database.is_symlink()
    assert hashlib.sha256(database.read_bytes()).hexdigest() == binding["sha256"]
    assert len(database.read_bytes()) == binding["bytes"]
    assert declared.original_exit_code == 0
    assert declared.collection_count == 1 and declared.coverage_percent == 100
    assert declared.resource_profile == "source-declared-verifier"
    assert declared.resource_limits["outer_project_workers"] == "1"
    assert declared.resource_limits["subprocess_timeout_seconds"] == 6900
    assert json.loads(declared.resource_limits["test_selection"]) == ["python", "scripts/verify.py"]
    assert lanes["ordinary"].coverage_percent == 100
    assert lanes["ordinary"].resource_limits["outer_project_workers"] == "2"
    data = CoverageData(basename=str(combined))
    data.read()
    measured = data.measured_files()
    assert any(path.endswith("demo_mod.py") for path in measured)
    assert any(path.endswith("ordinary_mod.py") for path in measured)


@pytest.mark.timeout(240)
@pytest.mark.parametrize("refusal", ["missing-receipt", "below-floor"])
def test_union_matrix_refuses_unadmitted_declared_verifier(tmp_path: Path, refusal: str) -> None:
    """A child exit zero cannot replace fresh receipt and independent coverage."""
    from infrastructure.core.testing.public_matrix_receipt import PublicMatrixReceipt
    from infrastructure.core.testing.test_runner import run_per_project_pytest

    project = _write_verifier_project(tmp_path, write_receipt=refusal != "missing-receipt")
    if refusal == "below-floor":
        (project / "src/demo_mod.py").write_text("def answer():\n    return 7\ndef uncovered():\n    return 9\n")
    receipt_path = tmp_path / "refused-matrix.json"
    assert (
        run_per_project_pytest(
            tmp_path,
            projects=["active/demo"],
            fail_under=90,
            timeout=60,
            subprocess_timeout_seconds=120,
            coverage_file=tmp_path / ".coverage.union",
            receipt_path=receipt_path,
        )
        != 0
    )
    receipt = PublicMatrixReceipt.read(receipt_path)
    assert receipt.overall_exit != 0
    assert receipt.validate(("active/demo",))
    lane = receipt.lanes[0]
    assert lane.exit_code != 0 and lane.coverage_database is None
    assert lane.original_exit_code == 0
    assert not lane.timed_out


@pytest.mark.timeout(180)
@pytest.mark.parametrize("mutation", ["database-bytes", "missing-database", "missing-binding"])
def test_matrix_receipt_closes_exact_admitted_declared_coverage(tmp_path: Path, mutation: str) -> None:
    """Finalization refuses changed or missing bytes from an actual admitted run."""
    from infrastructure.core.testing.public_matrix_receipt import PublicMatrixReceipt, write_public_matrix_receipt
    from infrastructure.core.testing.test_runner import (
        ProjectPytestResult,
        ProjectPytestSpec,
        _measure_coverage_percent,
    )
    from infrastructure.core.testing.test_runner_outputs import output_tree_digest

    project = _write_verifier_project(tmp_path)
    database = tmp_path / ".coverage.admitted"
    before = output_tree_digest(project)
    code, observed = run_declared_project_verifier(
        tmp_path,
        project,
        "active/demo",
        ("python", "scripts/verify.py"),
        coverage_floor=90,
        timeout_seconds=120,
        coverage_destination=database,
    )
    assert code == 0 and observed["coverage_percent"] == 100
    binding = observed["coverage_database"]
    assert binding is not None and database.is_file()
    if mutation == "database-bytes":
        database.write_bytes(database.read_bytes() + b"altered")
    elif mutation == "missing-database":
        database.unlink()
    else:
        binding = None
    spec = ProjectPytestSpec(
        index=0,
        project_name="active/demo",
        project_root=project,
        tests_dir=project / "tests",
        coverage_file=database,
        cmd=["python", "scripts/verify.py"],
        env={},
        declared_command=("python", "scripts/verify.py"),
        coverage_floor=90,
    )
    result = ProjectPytestResult(
        index=0,
        project_name="active/demo",
        exit_code=code,
        coverage_file=database,
        collection_count=observed["discovery_count"],
        duration_seconds=1.0,
        coverage_database=binding,
        original_exit_code=observed["original_exit_code"],
        subprocess_timeout_seconds=6900,
    )
    receipt_path = tmp_path / "refused-finalization.json"
    arguments = dict(
        specs=[spec],
        results=[result],
        output_digests_before={"active/demo": before},
        profile="release",
        marker_expr=None,
        project_workers=1,
        parallel=None,
        combined_coverage_percent=100.0,
        combined_floor=90,
        measure_coverage_percent=_measure_coverage_percent,
        phase_durations={"project_matrix": 1.0, "coverage_combine": 1.0, "coverage_gate": 1.0},
    )
    assert write_public_matrix_receipt(tmp_path, receipt_path, overall_exit=0, **arguments) == 75
    receipt = PublicMatrixReceipt.read(receipt_path)
    assert receipt.validate(("active/demo",))
    assert receipt.lanes[0].coverage_percent is None
    assert receipt.lanes[0].original_exit_code == 0
    # Closing custody must preserve a previously observed failure identity.
    assert write_public_matrix_receipt(tmp_path, receipt_path, overall_exit=42, **arguments) == 42


def _write_profile_verifier_project(repo_root: Path, *, opt_in: bool = True) -> Path:
    """Give the existing real verifier a strict supported CLI and retained argv."""
    project = _write_verifier_project(repo_root)
    metadata = project / "pyproject.toml"
    if opt_in:
        metadata.write_text(metadata.read_text() + '\nproject_test_profile_argument = "--profile"\n')
    script = project / "scripts/verify.py"
    body = script.read_text()
    prefix = (
        "import argparse,json\nfrom pathlib import Path\n"
        "parser=argparse.ArgumentParser()\n"
        + (
            'parser.add_argument("--profile", choices=("quick","release","exhaustive"), required=True)\n'
            if opt_in
            else ""
        )
        + "selected=parser.parse_args()\n"
        + "Path(__file__).resolve().with_name('observed-profile.json').write_text(json.dumps(vars(selected)))\n"
    )
    script.write_text(prefix + body)
    return project


@pytest.mark.timeout(180)
@pytest.mark.parametrize("profile", ["quick", "release", "exhaustive"])
def test_actual_stage_forwards_only_the_declared_named_profile(tmp_path: Path, profile: str) -> None:
    project = _write_profile_verifier_project(tmp_path)
    exit_code = execute_test_pipeline(
        "active/demo",
        tmp_path,
        run_infra=False,
        run_project=True,
        quiet=True,
        include_slow=False,
        include_long_running=False,
        include_ollama_tests=False,
        profile=profile,
        strict=True,
    )
    assert exit_code == 0
    observed = json.loads((project / "scripts/observed-profile.json").read_text())
    assert observed == {"profile": profile}
    report = json.loads((project / "output/reports/test_results.json").read_text())
    assert report["summary"]["all_passed"] is True and report["project"]["passed"] == 1
    assert report["project"]["exit_code"] == 0 and report["summary"]["project_coverage"] >= 90


@pytest.mark.timeout(180)
def test_actual_stage_preserves_arbitrary_declared_argv_without_profile_opt_in(tmp_path: Path) -> None:
    project = _write_profile_verifier_project(tmp_path, opt_in=False)
    assert (
        execute_test_pipeline(
            "active/demo",
            tmp_path,
            run_infra=False,
            run_project=True,
            quiet=True,
            include_slow=False,
            include_long_running=False,
            include_ollama_tests=False,
            profile="release",
            strict=True,
        )
        == 0
    )
    # The real strict parser accepts no arguments, so any guessed profile flag
    # would fail the actual process rather than being silently ignored.
    assert json.loads((project / "scripts/observed-profile.json").read_text()) == {}


@pytest.mark.timeout(240)
def test_actual_union_forwards_declared_profile_and_retains_real_command(tmp_path: Path) -> None:
    import os
    import sys

    from infrastructure.core.execution_boundary import run_bounded_subprocess
    from infrastructure.core.testing.project_test_runtime import build_audited_project_test_command

    project = _write_profile_verifier_project(tmp_path)
    # A plain audited child imports production test_* modules without pytest's
    # assertion rewriting; retain the actual union and receipt checks there.
    driver = tmp_path / "union_profile_driver.py"
    driver.write_text(
        dedent(
            """
            import json
            import sys
            from pathlib import Path
            from infrastructure.core.testing.public_matrix_receipt import PublicMatrixReceipt
            from infrastructure.core.testing.test_runner import run_per_project_pytest
            tmp_path = Path(sys.argv[1])
            project = tmp_path / 'projects/active/demo'
            receipt_path = tmp_path / "profile-matrix.json"
            assert (
                run_per_project_pytest(
                    tmp_path,
                    projects=["active/demo"],
                    profile="release",
                    fail_under=90,
                    timeout=60,
                    subprocess_timeout_seconds=120,
                    coverage_file=tmp_path / ".coverage.profile-union",
                    receipt_path=receipt_path,
                    project_workers=1,
                )
                == 0
            )
            assert json.loads((project / "scripts/observed-profile.json").read_text()) == {"profile": "release"}
            receipt = PublicMatrixReceipt.read(receipt_path)
            assert receipt.validate(("active/demo",)) == []
            lane = receipt.lanes[0]
            assert lane.original_exit_code == 0 and lane.collection_count == 1 and lane.coverage_percent >= 90
            assert json.loads(lane.resource_limits["test_selection"]) == ["python", "scripts/verify.py", "--profile", "release"]
            """
        ).lstrip(),
        encoding="utf-8",
    )
    command = build_audited_project_test_command(
        tmp_path, Path(sys.executable).absolute(), (str(tmp_path),), script=driver
    )
    outcome = run_bounded_subprocess(command, cwd=tmp_path, env=os.environ.copy(), timeout=180)
    assert outcome.returncode == 0, outcome.stdout + outcome.stderr
    assert json.loads((project / "scripts/observed-profile.json").read_text()) == {"profile": "release"}


@pytest.mark.parametrize("literal", ["true", '""', '"--other"', "7"])
def test_profile_argument_metadata_refuses_unsupported_shapes(tmp_path: Path, literal: str) -> None:
    from infrastructure.core.project_pyproject import project_declared_test_command

    project = _write_verifier_project(tmp_path)
    path = project / "pyproject.toml"
    path.write_text(path.read_text() + "\nproject_test_profile_argument = " + literal + "\n")
    with pytest.raises(ValueError, match="literal --profile"):
        project_declared_test_command(project, profile="release")
    assert not (project / "scripts/observed-profile.json").exists()


def test_profile_argument_requires_an_actual_declared_command(tmp_path: Path) -> None:
    from infrastructure.core.project_pyproject import project_declared_test_command

    project = _write_verifier_project(tmp_path)
    path = project / "pyproject.toml"
    path.write_text(
        path.read_text().replace(
            'project_test_command = ["python", "scripts/verify.py"]', 'project_test_profile_argument = "--profile"'
        )
    )
    with pytest.raises(ValueError, match="requires a declared command"):
        project_declared_test_command(project, profile="release")


def test_profile_argument_refuses_an_already_fixed_profile(tmp_path: Path) -> None:
    from infrastructure.core.project_pyproject import project_declared_test_command

    project = _write_verifier_project(tmp_path)
    path = project / "pyproject.toml"
    path.write_text(
        path.read_text().replace(
            'project_test_command = ["python", "scripts/verify.py"]',
            'project_test_command = ["python", "scripts/verify.py", "--profile=quick"]',
        )
        + '\nproject_test_profile_argument = "--profile"\n'
    )
    with pytest.raises(ValueError, match="already select --profile"):
        project_declared_test_command(project, profile="release")


def test_profile_aware_command_uses_the_existing_profile_validation(tmp_path: Path) -> None:
    from infrastructure.core.project_pyproject import project_declared_test_command

    project = _write_profile_verifier_project(tmp_path)
    with pytest.raises(ValueError, match="Unknown test profile"):
        project_declared_test_command(project, profile="unrecognized")
