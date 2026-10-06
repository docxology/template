"""Structured custom-verifier contract for single-project Stage 01 runs.

Projects with unusually stateful or chunked test suites may explicitly declare
an argv command in ``[tool.template].project_test_command``.  This module keeps
that opt-in path fail-closed: the command is confined to a Python entry point
under the project's ``scripts/`` tree, runs without a shell, and must emit a
fresh nonce-bound receipt.  Coverage is then read independently from the new
coverage database rather than trusted from command output alone.
"""

from __future__ import annotations

import hashlib
import io
import argparse
import json
import math
import os
import tempfile
import uuid
import sys
from pathlib import Path
from typing import Any, cast

from coverage import Coverage
from coverage.exceptions import CoverageException

from infrastructure.core.execution_boundary import run_bounded_subprocess, validate_hook_root
from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.core.files.coverage_cleanup import clean_coverage_files
from infrastructure.core.implementation_custody import bytecode_audit_bootstrap, verify_fresh_module_bytecode
from infrastructure.core.runtime.python_binding import analysis_runtime_binding
from infrastructure.core.testing.project_test_runtime import (
    ProjectTestRuntimeError,
    admit_project_test_runtime,
    project_test_deadline,
    remaining_test_budget,
    build_audited_project_test_command,
    project_test_audit_roots,
)
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.testing.pytest_orchestration import TestSuiteResults, build_pythonpath
from infrastructure.reporting.suite_runner import (
    DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS,
    run_pytest_stream,
)

logger = get_logger(__name__)

PROJECT_TEST_RECEIPT_SCHEMA = "template/project-test-receipt/1"
PROJECT_TEST_RECEIPT_ENV = "TEMPLATE_PROJECT_TEST_RECEIPT"
PROJECT_TEST_RUN_ID_ENV = "TEMPLATE_PROJECT_TEST_RUN_ID"
PROJECT_TEST_PROJECT_ENV = "TEMPLATE_PROJECT_TEST_PROJECT"
PROJECT_TEST_COMMAND_SHA_ENV = "TEMPLATE_PROJECT_TEST_COMMAND_SHA256"
DEFAULT_PROJECT_VERIFIER_TIMEOUT_SECONDS = DEFAULT_SINGLE_PROJECT_TEST_TIMEOUT_SECONDS
_MAX_RECEIPT_BYTES = 1_000_000


class ProjectVerifierError(RuntimeError):
    """A typed verifier refusal that preserves the actual child exit outcome."""

    def __init__(self, message: str, *, exit_code: int = 1, original_exit_code: int | None = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.original_exit_code = original_exit_code


def project_test_command_sha256(command: tuple[str, ...]) -> str:
    """Return the stable identity digest for one exact argv declaration."""
    payload = json.dumps(list(command), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_project_test_command(project_root: Path, command: tuple[str, ...]) -> tuple[str, ...]:
    """Validate and return an explicit no-shell project verifier command.

    The portable declaration is ``python scripts/<entry>.py [args]``.
    Stage 01 selects an existing prepared interpreter; declarations cannot
    acquire packages, request extras, or dispatch a shell.
    """
    if len(command) < 2 or any(not isinstance(part, str) or not part for part in command) or command[0] != "python":
        raise ProjectVerifierError('project_test_command must use ["python", "scripts/<entry>.py", ...]', exit_code=2)
    raw_entrypoint = Path(command[1])
    if (
        raw_entrypoint.is_absolute()
        or not raw_entrypoint.parts
        or raw_entrypoint.parts[0] != "scripts"
        or ".." in raw_entrypoint.parts
    ):
        raise ProjectVerifierError(
            "project_test_command entry point must be project-relative inside scripts", exit_code=2
        )
    scripts_root = (project_root / "scripts").resolve()
    try:
        entrypoint = validate_hook_root(project_root / raw_entrypoint, hook_root=scripts_root)
    except ValueError as exc:
        raise ProjectVerifierError(str(exc), exit_code=2) from exc
    if entrypoint.suffix != ".py" or not entrypoint.is_file():
        raise ProjectVerifierError(f"project verifier must be an existing Python file: {raw_entrypoint}", exit_code=2)
    try:
        read_bytes_confined(project_root, project_root / raw_entrypoint, max_bytes=16 * 1024 * 1024)
    except (OSError, ValueError) as exc:
        raise ProjectVerifierError(f"Project verifier source cannot be admitted: {exc}", exit_code=2) from exc
    return command


def build_project_verifier_execution_command(
    command: tuple[str, ...], project_root: Path, *, interpreter: Path | None = None
) -> tuple[str, ...]:
    """Bind portable argv to one existing interpreter; never run a resolver."""
    selected = Path(sys.executable).absolute() if interpreter is None else interpreter
    return build_audited_project_test_command(
        project_root, selected, command[2:], script=project_root.absolute() / command[1]
    )


def _require_nonnegative_int(mapping: dict[str, Any], key: str) -> int:
    value = mapping.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ProjectVerifierError(f"project verifier receipt field results.{key} must be a non-negative integer")
    return value


def _load_receipt(
    receipt_path: Path,
    *,
    project_name: str,
    run_id: str,
    command_sha256: str,
) -> tuple[TestSuiteResults, float]:
    """Load and validate one fresh verifier receipt."""
    if receipt_path.is_symlink() or not receipt_path.is_file():
        raise ProjectVerifierError("project verifier exited without a fresh regular-file receipt")
    if receipt_path.stat().st_size > _MAX_RECEIPT_BYTES:
        raise ProjectVerifierError("project verifier receipt exceeds the 1 MB contract limit")
    try:
        payload = json.loads(read_bytes_confined(receipt_path.parent, receipt_path, max_bytes=_MAX_RECEIPT_BYTES))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectVerifierError(f"project verifier receipt is unreadable: {exc}") from exc
    if not isinstance(payload, dict):
        raise ProjectVerifierError("project verifier receipt root must be a JSON object")
    expected = {
        "schema_version": PROJECT_TEST_RECEIPT_SCHEMA,
        "project": project_name,
        "run_id": run_id,
        "command_sha256": command_sha256,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ProjectVerifierError(
                f"project verifier receipt {key} mismatch: expected {value!r}, got {payload.get(key)!r}"
            )
    raw_results = payload.get("results")
    if not isinstance(raw_results, dict):
        raise ProjectVerifierError("project verifier receipt results must be an object")
    passed = _require_nonnegative_int(raw_results, "passed")
    failed = _require_nonnegative_int(raw_results, "failed")
    skipped = _require_nonnegative_int(raw_results, "skipped")
    total = _require_nonnegative_int(raw_results, "total")
    collection_errors = _require_nonnegative_int(raw_results, "collection_errors")
    discovery_count = _require_nonnegative_int(raw_results, "discovery_count")
    if total == 0 or discovery_count == 0:
        raise ProjectVerifierError("project verifier receipt reports a vacuous zero-test run")
    if total != passed + failed + skipped + collection_errors:
        raise ProjectVerifierError("project verifier receipt total does not match its outcome counts")
    if discovery_count < total:
        raise ProjectVerifierError("project verifier receipt discovery_count is smaller than total")
    if failed or collection_errors:
        raise ProjectVerifierError(
            f"project verifier receipt reports failed={failed}, collection_errors={collection_errors}"
        )
    raw_coverage = payload.get("coverage_percent")
    if not isinstance(raw_coverage, (int, float)) or isinstance(raw_coverage, bool) or not math.isfinite(raw_coverage):
        raise ProjectVerifierError("project verifier receipt coverage_percent must be a finite number")
    results = cast(
        TestSuiteResults,
        {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": total,
            "warnings": _require_nonnegative_int(raw_results, "warnings"),
            "exit_code": 0,
            "discovery_count": discovery_count,
            "collection_errors": collection_errors,
            "execution_phases": {},
            "test_categories": {},
            "coverage_percent": float(raw_coverage),
            "failed_tests": [],
        },
    )
    return results, float(raw_coverage)


def _regenerate_coverage_json(project_root: Path) -> float:
    """Read the fresh project coverage DB and write the canonical JSON report."""
    coverage_db = project_root / ".coverage"
    if coverage_db.is_symlink() or not coverage_db.is_file():
        raise ProjectVerifierError("project verifier did not produce a fresh .coverage database")
    config_file = project_root / "pyproject.toml"
    try:
        frozen_database = read_bytes_confined(project_root, coverage_db, max_bytes=64 * 1024 * 1024)
        with tempfile.TemporaryDirectory(prefix="template-coverage-validation-") as temporary:
            admitted_database = Path(temporary) / ".coverage"
            admitted_database.write_bytes(frozen_database)
            coverage = Coverage(
                data_file=str(admitted_database),
                config_file=str(config_file) if config_file.is_file() else True,
            )
            coverage.load()
            percent = float(coverage.report(file=io.StringIO(), ignore_errors=False))
            report_path = Path(temporary) / "coverage_project.json"
            coverage.json_report(outfile=str(report_path), pretty_print=True)
            if read_bytes_confined(project_root, coverage_db, max_bytes=64 * 1024 * 1024) != frozen_database:
                raise ProjectVerifierError("Project coverage database changed during independent validation")
            atomic_write_bytes_confined(project_root, project_root / "coverage_project.json", report_path.read_bytes())
    except (CoverageException, OSError, ValueError) as exc:
        raise ProjectVerifierError(f"cannot read project verifier coverage evidence: {exc}") from exc
    return percent


def run_declared_project_verifier(
    repo_root: Path,
    project_root: Path,
    project_name: str,
    command: tuple[str, ...],
    *,
    coverage_floor: float,
    timeout_seconds: float = DEFAULT_PROJECT_VERIFIER_TIMEOUT_SECONDS,
) -> tuple[int, TestSuiteResults]:
    """Run a declared verifier and return canonical Stage-01 test results."""
    try:
        deadline = project_test_deadline(timeout_seconds)
        if (
            isinstance(coverage_floor, bool)
            or not isinstance(coverage_floor, (int, float))
            or not math.isfinite(coverage_floor)
            or not 0 <= coverage_floor <= 100
        ):
            raise ProjectVerifierError("Project coverage floor must be finite within 0–100", exit_code=2)
        validated = validate_project_test_command(project_root, command)
        selected, runtime = admit_project_test_runtime(project_root, deadline=deadline)
    except ProjectTestRuntimeError as exc:
        raise ProjectVerifierError(
            str(exc), exit_code=exc.exit_code, original_exit_code=exc.original_exit_code
        ) from exc
    execution_command = build_project_verifier_execution_command(validated, project_root, interpreter=selected)
    coverage_db = project_root / ".coverage"
    if coverage_db.is_symlink():
        raise ProjectVerifierError("project verifier refuses a symlinked .coverage database")
    clean_coverage_files(repo_root, scope_dir=project_root)
    if coverage_db.exists():
        raise ProjectVerifierError("stale project .coverage survived Stage-01 cleanup")
    coverage_json = project_root / "coverage_project.json"
    coverage_json.unlink(missing_ok=True)
    run_id = uuid.uuid4().hex
    command_sha = project_test_command_sha256(execution_command)
    with tempfile.TemporaryDirectory(prefix="template-project-verifier-") as temp_dir:
        receipt_path = Path(temp_dir) / "receipt.json"
        env = os.environ.copy()
        env.pop("COVERAGE_FILE", None)
        for pytest_env in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTEST_DISABLE_PLUGIN_AUTOLOAD"):
            env.pop(pytest_env, None)
        env.setdefault("MPLBACKEND", "Agg")
        env.setdefault("PYTHONUNBUFFERED", "1")
        env["PYTHONPATH"] = build_pythonpath(
            repo_root,
            project_root,
            prepend=[str(project_root)],
            existing_pythonpath=env.get("PYTHONPATH"),
        )
        env.update(
            {
                PROJECT_TEST_RECEIPT_ENV: str(receipt_path),
                PROJECT_TEST_RUN_ID_ENV: run_id,
                PROJECT_TEST_PROJECT_ENV: project_name,
                PROJECT_TEST_COMMAND_SHA_ENV: command_sha,
            }
        )
        exit_code, _stdout, stderr = run_pytest_stream(
            list(execution_command),
            project_root,
            env,
            quiet=False,
            timeout_seconds=remaining_test_budget(deadline),
        )
        if exit_code != 0:
            detail = stderr.strip()
            suffix = f": {detail[-1000:]}" if detail else ""
            raise ProjectVerifierError(
                f"declared project verifier exited {exit_code}{suffix}",
                exit_code=exit_code if exit_code in (75, 124, 130) else 1,
                original_exit_code=exit_code,
            )
        try:
            unchanged_runtime = analysis_runtime_binding(project_root, interpreter=selected) == runtime["binding"]
        except (OSError, ValueError) as exc:
            raise ProjectVerifierError(
                f"Selected prepared test runtime custody refused after verifier: {exc}",
                exit_code=75,
                original_exit_code=0,
            ) from exc
        if not unchanged_runtime:
            raise ProjectVerifierError(
                "Selected prepared test runtime changed after actual verifier child", exit_code=75, original_exit_code=0
            )
        request_path = Path(temp_dir) / "validation.json"
        result_path = Path(temp_dir) / "validation_result.json"
        request_path.write_text(
            json.dumps(
                {
                    "receipt_path": str(receipt_path),
                    "project_root": str(project_root.absolute()),
                    "project_name": project_name,
                    "run_id": run_id,
                    "command_sha256": command_sha,
                    "coverage_floor": coverage_floor,
                    "result_path": str(result_path),
                    "audit_roots": [str(root) for root in project_test_audit_roots(project_root)],
                }
            ),
            encoding="utf-8",
        )
        prefix = Path(temp_dir) / "validation-pycache"
        prefix.mkdir(mode=0o700)
        platform_root = Path(__file__).absolute().parents[1]
        bootstrap = bytecode_audit_bootstrap(project_test_audit_roots(project_root), prefix)
        launch = (
            "import sys,runpy; sys.path.insert(0,sys.argv[1]); sys.path.insert(0,sys.argv[3]); "
            "sys.argv=['project_verifier','--validate-receipt',sys.argv[2]]; "
            + bootstrap
            + "\nrunpy.run_module('infrastructure.reporting.project_verifier',run_name='__main__')"
        )
        try:
            checked = run_bounded_subprocess(
                [
                    str(selected),
                    "-I",
                    "-X",
                    f"pycache_prefix={prefix}",
                    "-c",
                    launch,
                    str(platform_root.parent),
                    str(request_path),
                    str(project_root.absolute()),
                ],
                cwd=project_root,
                env=env,
                timeout=remaining_test_budget(deadline),
            )
            if checked.returncode != 0:
                detail = checked.command_error or checked.stderr or checked.stdout
                raise ProjectVerifierError(
                    f"Independent verifier evidence validation exited {checked.returncode}: {detail[-1000:]}",
                    exit_code=checked.returncode if checked.returncode in (75, 124, 130) else 1,
                    original_exit_code=0,
                )
            results = cast(
                TestSuiteResults,
                json.loads(read_bytes_confined(Path(temp_dir), result_path, max_bytes=_MAX_RECEIPT_BYTES)),
            )
            measured_coverage = float(results["coverage_percent"])
            try:
                unchanged_runtime = analysis_runtime_binding(project_root, interpreter=selected) == runtime["binding"]
            except (OSError, ValueError) as exc:
                raise ProjectVerifierError(
                    f"Selected prepared test runtime custody refused: {exc}", exit_code=75, original_exit_code=0
                ) from exc
            if not unchanged_runtime:
                raise ProjectVerifierError(
                    "Selected prepared test runtime changed during verification", exit_code=75, original_exit_code=0
                )
            remaining_test_budget(deadline)
        except ProjectTestRuntimeError as exc:
            raise ProjectVerifierError(str(exc), exit_code=exc.exit_code, original_exit_code=0) from exc
    results["coverage_percent"] = measured_coverage
    results["selected_runtime"] = runtime
    results["original_exit_code"] = 0
    logger.info(
        "Declared project verifier passed: %d tests, %.2f%% coverage",
        results["total"],
        measured_coverage,
    )
    return 0, results


def _validate_receipt_worker(request_path: Path) -> int:
    """Independently validate receipt and Coverage inside the composed deadline."""
    request = json.loads(read_bytes_confined(request_path.parent, request_path, max_bytes=_MAX_RECEIPT_BYTES))
    project_root = Path(request["project_root"])
    results, receipt_coverage = _load_receipt(
        Path(request["receipt_path"]),
        project_name=request["project_name"],
        run_id=request["run_id"],
        command_sha256=request["command_sha256"],
    )
    measured = _regenerate_coverage_json(project_root)
    if not math.isclose(receipt_coverage, measured, abs_tol=0.01):
        raise ProjectVerifierError("project verifier receipt coverage does not match the independently read database")
    floor = request["coverage_floor"]
    if isinstance(floor, bool) or not isinstance(floor, (int, float)) or not math.isfinite(floor):
        raise ProjectVerifierError("Project coverage floor must be finite", exit_code=2)
    if measured + 1e-9 < floor:
        raise ProjectVerifierError(
            f"project verifier coverage {measured:.2f}% is below the declared {floor:.2f}% floor"
        )
    results["coverage_percent"] = measured
    frozen_roots = tuple(Path(root) for root in request["audit_roots"])
    if project_test_audit_roots(project_root) != frozen_roots:
        raise ProjectVerifierError("Project plugin-root set changed during independent validation", exit_code=75)
    for root in frozen_roots:
        verify_fresh_module_bytecode(root, Path(sys.pycache_prefix or ""))
    atomic_write_bytes_confined(request_path.parent, Path(request["result_path"]), json.dumps(results).encode("utf-8"))
    return 0


def _main() -> int:
    parser = argparse.ArgumentParser(description="Bounded internal Stage01 receipt validation")
    parser.add_argument("--validate-receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        return _validate_receipt_worker(args.validate_receipt)
    except (OSError, ValueError, ProjectVerifierError) as exc:
        logger.error("Independent project evidence validation refused: %s", exc)
        return getattr(exc, "exit_code", 1)


__all__ = [
    "DEFAULT_PROJECT_VERIFIER_TIMEOUT_SECONDS",
    "PROJECT_TEST_COMMAND_SHA_ENV",
    "PROJECT_TEST_PROJECT_ENV",
    "PROJECT_TEST_RECEIPT_ENV",
    "PROJECT_TEST_RECEIPT_SCHEMA",
    "PROJECT_TEST_RUN_ID_ENV",
    "ProjectVerifierError",
    "build_project_verifier_execution_command",
    "project_test_command_sha256",
    "run_declared_project_verifier",
    "validate_project_test_command",
]


if __name__ == "__main__":
    raise SystemExit(_main())
