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
import json
import math
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, cast

from coverage import Coverage
from coverage.exceptions import CoverageException

from infrastructure.core.execution_boundary import validate_hook_root
from infrastructure.core.logging.utils import get_logger
from infrastructure.core.pytest_orchestration import TestSuiteResults, build_pythonpath, prepend_uv_to_path
from infrastructure.core.pytest_profiles import test_runner_dependency_specs
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
    """Raised when a declared verifier violates its execution/evidence contract."""


def project_test_command_sha256(command: tuple[str, ...]) -> str:
    """Return the stable identity digest for one exact argv declaration."""
    payload = json.dumps(list(command), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_project_test_command(project_root: Path, command: tuple[str, ...]) -> tuple[str, ...]:
    """Validate and return an explicit no-shell project verifier command.

    The intentionally narrow ``uv run [--extra NAME] python
    scripts/<entry>.py`` shape keeps the declaration portable, lets a clean
    project install its declared verifier dependencies, and prevents a config
    typo from silently turning Stage 01 into an arbitrary shell dispatch
    surface. The project source is still trusted to execute code, just as its
    pytest suite already is.
    """
    if len(command) < 4 or command[:2] != ("uv", "run"):
        raise ProjectVerifierError("project_test_command must use an explicit uv-run Python argv")
    python_index = 2
    if command[python_index] == "--extra":
        if len(command) < 6 or not command[python_index + 1] or command[python_index + 1].startswith("-"):
            raise ProjectVerifierError("project_test_command --extra requires one named project extra")
        python_index += 2
    if len(command) <= python_index + 1 or command[python_index] != "python":
        raise ProjectVerifierError(
            "project_test_command must be "
            '["uv", "run", "python", ...] or '
            '["uv", "run", "--extra", "<name>", "python", ...]'
        )
    raw_entrypoint = Path(command[python_index + 1])
    if raw_entrypoint.is_absolute():
        raise ProjectVerifierError("project_test_command entry point must be project-relative")
    scripts_root = (project_root / "scripts").resolve()
    try:
        entrypoint = validate_hook_root(project_root / raw_entrypoint, hook_root=scripts_root)
    except ValueError as exc:
        raise ProjectVerifierError(str(exc)) from exc
    if entrypoint.suffix != ".py" or not entrypoint.is_file():
        raise ProjectVerifierError(f"project verifier must be an existing Python file: {raw_entrypoint}")
    return command


def build_project_verifier_execution_command(command: tuple[str, ...]) -> tuple[str, ...]:
    """Overlay the workspace's exact test-runner versions onto *command*.

    The project verifier and the independent Stage-01 adapter both read the
    same Coverage database. Pinning the shared runner stack prevents a clean
    project environment from silently creating evidence with a different
    Coverage/pytest implementation than the one validating it.
    """
    prefix: list[str] = ["uv", "run"]
    for dependency in test_runner_dependency_specs():
        prefix.extend(["--with", dependency])
    return (*prefix, *command[2:])


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
        payload = json.loads(receipt_path.read_text(encoding="utf-8"))
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
        coverage = Coverage(
            data_file=str(coverage_db),
            config_file=str(config_file) if config_file.is_file() else True,
        )
        coverage.load()
        percent = float(coverage.report(file=io.StringIO(), ignore_errors=False))
        coverage.json_report(outfile=str(project_root / "coverage_project.json"), pretty_print=True)
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
    validated = validate_project_test_command(project_root, command)
    execution_command = build_project_verifier_execution_command(validated)
    if timeout_seconds <= 0:
        raise ProjectVerifierError("project verifier timeout must be positive")
    coverage_db = project_root / ".coverage"
    if coverage_db.is_symlink():
        raise ProjectVerifierError("project verifier refuses a symlinked .coverage database")
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
        prepend_uv_to_path(env)
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
            timeout_seconds=timeout_seconds,
        )
        if exit_code != 0:
            detail = stderr.strip()
            suffix = f": {detail[-1000:]}" if detail else ""
            raise ProjectVerifierError(f"declared project verifier exited {exit_code}{suffix}")
        results, receipt_coverage = _load_receipt(
            receipt_path,
            project_name=project_name,
            run_id=run_id,
            command_sha256=command_sha,
        )
        measured_coverage = _regenerate_coverage_json(project_root)
    if not math.isclose(receipt_coverage, measured_coverage, abs_tol=0.01):
        raise ProjectVerifierError(
            "project verifier receipt coverage does not match the independently read database: "
            f"{receipt_coverage:.4f}% != {measured_coverage:.4f}%"
        )
    if measured_coverage + 1e-9 < coverage_floor:
        raise ProjectVerifierError(
            f"project verifier coverage {measured_coverage:.2f}% is below the declared {coverage_floor:.2f}% floor"
        )
    results["coverage_percent"] = measured_coverage
    logger.info(
        "Declared project verifier passed: %d tests, %.2f%% coverage",
        results["total"],
        measured_coverage,
    )
    return 0, results


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
