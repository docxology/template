"""Compose an original serial project test measurement into the same pipeline.

This functional DATA is not release acceptance. The executor holds the raw
measurement hash after its actual successful Stage 01 and supplies that hash to
later children. Run labels inside a file cannot authorize its own reuse.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shlex
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, cast

from infrastructure.core.files.secure_write import atomic_write_bytes_confined, read_bytes_confined
from infrastructure.core.pipeline.fingerprints import source_content_fingerprint
from infrastructure.core.runtime.python_binding import analysis_runtime_binding, select_analysis_python
from infrastructure.core.testing.pytest_observations import (
    DIRECTORY_ENV,
    NONCE_ENV,
    ROOT_ENV,
    read_execution_collection,
    read_execution_receipts,
)

ANCHOR_ENV = "PIPELINE_TEST_MEASUREMENT_SHA256"
_PLUGIN = "infrastructure.core.testing.pytest_receipt"
_SCHEMA = "template-project-test-measurement/v1"
_PUBLICATION: ContextVar[dict[str, str] | None] = ContextVar("project_test_measurement_publication", default=None)


class MeasurementIneligible(ValueError):
    """A genuine original selection cannot be composed as a full serial run."""


@contextmanager
def observe_measurement_publication() -> Iterator[dict[str, str]]:
    """Hold the producer's original SHA inside the actual stage worker."""
    publication: dict[str, str] = {}
    token = _PUBLICATION.set(publication)
    try:
        yield publication
    finally:
        _PUBLICATION.reset(token)


def measurement_path(project: Path, run_id: str) -> Path:
    """Keep all transient controls beneath the current project's ignored output."""
    return project / "output/.pipeline/tests" / hashlib.sha256(run_id.encode()).hexdigest() / "measurement.json"


def _context(env: Mapping[str, str]) -> dict[str, str]:
    names = ("PIPELINE_RUN_ID", "PIPELINE_PLAN_DIGEST")
    if any(not env.get(name) for name in names):
        raise ValueError("Project measurement requires an actual current pipeline context")
    return {name: env[name] for name in names}


def _inventory(project: Path) -> list[str]:
    # Reuse is deliberately restricted to a complete conventional pytest tree.
    # A project with custom collection remains eligible for genuine fresh tests.
    return sorted(
        path.relative_to(project).as_posix()
        for path in (project / "tests").rglob("*.py")
        if path.name.startswith("test_") or path.name.endswith("_test.py")
    )


def _ambient_supported(env: Mapping[str, str]) -> bool:
    try:
        options = shlex.split(env.get("PYTEST_ADDOPTS", ""))
    except ValueError:
        return False
    return all(option.startswith("--benchmark-storage=") for option in options)


@dataclass(frozen=True)
class ProjectTestMeasurement:
    """A fresh pre-child observation; never constructed from published reports."""

    repo: Path
    project: Path
    interpreter: Path
    runtime: dict[str, Any]
    source: str
    context: dict[str, str]
    nonce: str
    directory: Path
    arguments: tuple[str, ...]
    files: tuple[str, ...]
    floor: float
    deadline: float


def prepare_measurement(
    repo: Path,
    project: Path,
    interpreter: Path,
    runtime: dict[str, Any],
    cmd: list[str],
    env: dict[str, str],
    *,
    floor: float,
    deadline: float,
) -> ProjectTestMeasurement | None:
    """Observe only an actual pipeline Stage 01, without changing its selection."""
    if env.get("PIPELINE_STAGE_KEY") != "project_tests" or not _ambient_supported(env):
        return None
    if not math.isfinite(deadline) or time.monotonic() >= deadline:
        raise ValueError("Project measurement deadline expired before original tests")
    if type(floor) not in (int, float) or not math.isfinite(floor) or not 0 <= floor <= 100:
        raise ValueError("Project measurement requires a finite coverage floor")
    context = _context(env)
    if cmd[:3] != [str(interpreter), "-I", "-c"]:
        return None
    # A unique directory retains all retry/controller outputs. Multiple original
    # controllers make this attempt ineligible rather than selecting a last pass.
    nonce = uuid.uuid4().hex
    directory = measurement_path(project, context["PIPELINE_RUN_ID"]).parent / nonce
    atomic_write_bytes_confined(project, directory / "owner", nonce.encode(), mode=0o600)
    cmd.extend(["-p", _PLUGIN])
    env.update({DIRECTORY_ENV: str(directory), NONCE_ENV: nonce, ROOT_ENV: str(project)})
    return ProjectTestMeasurement(
        repo,
        project,
        interpreter,
        runtime,
        source_content_fingerprint(repo, project),
        context,
        nonce,
        directory,
        tuple(cmd[4:]),
        tuple(_inventory(project)),
        float(floor),
        deadline,
    )


def _bound_bytes(project: Path, path: Path) -> bytes:
    return read_bytes_confined(project, path, max_bytes=64 * 1024 * 1024)


def _commitment(project: Path, path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(project).as_posix(),
        "sha256": hashlib.sha256(_bound_bytes(project, path)).hexdigest(),
    }


def _coverage(project: Path, raw: bytes, floor: float) -> dict[str, Any]:
    report = json.loads(raw)
    percentage = report["totals"]["percent_covered"]
    if (
        report["meta"].get("branch_coverage") is not True
        or type(percentage) not in (int, float)
        or not math.isfinite(percentage)
        or percentage < floor
        or not report["files"]
    ):
        raise ValueError("Original project branch coverage does not meet its declared floor")
    for name in report["files"]:
        path = Path(name)
        target = path if path.is_absolute() else project / path
        # Read the actual named Source through the same no-follow boundary.
        target.relative_to(project / "src")
        read_bytes_confined(project, target)
    return cast(dict[str, Any], report)


def _execution(
    project: Path, directory: Path, nonce: str, arguments: list[str], files: list[str]
) -> tuple[int, list[dict[str, str]]]:
    paths = sorted(directory.glob("execution-*.json"))
    if not paths:
        raise ValueError("Original project execution callback is missing")
    if len(paths) > 1:
        raise MeasurementIneligible("Measurement requires one original serial controller, without retries")
    raw = _bound_bytes(project, paths[0])
    value = json.loads(raw)
    selected, _ = read_execution_receipts(directory, nonce, snapshots=(raw,))
    collected, deselected, profile = read_execution_collection(directory, nonce, snapshots=(raw,))
    if (
        value["worker"] != "controller"
        or value["selected"] != list(selected)
        or value["collected"] != list(collected)
        or value["deselected"] != list(deselected)
        or value["selection_profile"] != profile
        or type(value.get("collection_skips")) is not int
        or profile["arguments"] != arguments
    ):
        raise ValueError("Original project observation differs from its nominated invocation or schema")
    if (
        value["collection_skips"] != 0
        or deselected
        or collected != selected
        or sorted({node.partition("::")[0] for node in selected}) != files
        or profile["keyword_expression"]
        or any(
            phases != {"setup": "passed", "call": "passed", "teardown": "passed"}
            for phases in value["reports"].values()
        )
    ):
        raise MeasurementIneligible("Original full project collection or all-pass execution differs")
    return len(selected), [
        {"path": paths[0].relative_to(project).as_posix(), "sha256": hashlib.sha256(raw).hexdigest()}
    ]


def publish_measurement(observation: ProjectTestMeasurement, *, original_exit_code: int) -> str:
    """Promote complete actual original data after success and fresh custody checks."""
    item = observation
    if original_exit_code != 0 or time.monotonic() >= item.deadline:
        raise ValueError("Only an original successful test child within its deadline can publish")
    count, receipts = _execution(item.project, item.directory, item.nonce, list(item.arguments), list(item.files))
    coverage_path = item.project / "coverage_project.json"
    coverage_raw = _bound_bytes(item.project, coverage_path)
    _coverage(item.project, coverage_raw, item.floor)
    if (
        source_content_fingerprint(item.repo, item.project) != item.source
        or analysis_runtime_binding(item.project, interpreter=item.interpreter) != item.runtime
        or _inventory(item.project) != list(item.files)
    ):
        raise ValueError("Original test Source/runtime changed during execution")
    record: dict[str, Any] = {
        "schema": _SCHEMA,
        "project": str(item.project),
        "repo": str(item.repo),
        "context": item.context,
        "source": item.source,
        "runtime": item.runtime,
        "interpreter": str(item.interpreter),
        "original_exit_code": original_exit_code,
        "arguments": list(item.arguments),
        "files": list(item.files),
        "nonce": item.nonce,
        "directory": item.directory.relative_to(item.project).as_posix(),
        "floor": item.floor,
        "passed": count,
        "receipts": receipts,
        "coverage": _commitment(item.project, coverage_path),
        "database": _commitment(item.project, item.project / ".coverage.project"),
    }
    if record["coverage"]["sha256"] != hashlib.sha256(coverage_raw).hexdigest():
        raise ValueError("Original coverage changed during validation")
    raw = (json.dumps(record, sort_keys=True, allow_nan=False) + "\n").encode()
    if time.monotonic() >= item.deadline:
        raise ValueError("Original test deadline expired before measurement promotion")
    atomic_write_bytes_confined(
        item.project, measurement_path(item.project, item.context["PIPELINE_RUN_ID"]), raw, mode=0o600
    )
    if _bound_bytes(item.project, measurement_path(item.project, item.context["PIPELINE_RUN_ID"])) != raw:
        raise ValueError("Original measurement changed during promotion readback")
    if time.monotonic() >= item.deadline:
        raise ValueError("Original test deadline expired during measurement promotion")
    anchor = hashlib.sha256(raw).hexdigest()
    publication = _PUBLICATION.get()
    if publication is not None:
        if publication:
            raise ValueError("Original stage cannot publish multiple test measurements")
        publication["sha256"] = anchor
    return anchor


def validate_measurement(project: Path, env: Mapping[str, str], anchor: str) -> tuple[int, dict[str, Any]]:
    """Validate an externally held hash before interpreting current-run test DATA."""
    if re.fullmatch(r"[0-9a-f]{64}", anchor) is None:
        raise ValueError("Invalid executor-held project measurement hash")
    context = _context(env)
    raw = _bound_bytes(project, measurement_path(project, context["PIPELINE_RUN_ID"]))
    if hashlib.sha256(raw).hexdigest() != anchor:
        raise ValueError("Project test measurement differs from the executor-held hash")
    value = json.loads(raw)
    repo = Path(value["repo"])
    selected = select_analysis_python(project)
    from infrastructure.core.testing.pytest_orchestration import project_declared_coverage_floor

    floor = project_declared_coverage_floor(project)
    if (
        value["schema"] != _SCHEMA
        or value["project"] != str(project)
        or value["context"] != context
        or value["original_exit_code"] != 0
        or value["interpreter"] != str(selected)
        or value["source"] != source_content_fingerprint(repo, project)
        or value["runtime"] != analysis_runtime_binding(project, interpreter=selected)
        or value["files"] != _inventory(project)
        or floor is None
        or value["floor"] != floor
    ):
        raise ValueError("Project measurement does not match current Source/runtime/run/floor")
    coverage_raw = b""
    for entry in [*value["receipts"], value["coverage"], value["database"]]:
        path = project / entry["path"]
        artifact_raw = _bound_bytes(project, path)
        if hashlib.sha256(artifact_raw).hexdigest() != entry["sha256"]:
            raise ValueError("Original project measurement artifact changed")
        if entry is value["coverage"]:
            coverage_raw = artifact_raw
    count, receipts = _execution(
        project, project / value["directory"], value["nonce"], value["arguments"], value["files"]
    )
    if count != value["passed"] or receipts != value["receipts"]:
        raise ValueError("Original measurement membership differs")
    return count, _coverage(project, coverage_raw, floor)


def consume_measurement(project: Path, output: Path | None = None) -> tuple[int, str] | None:
    """Absence permits fresh execution; an invalid present anchor fails closed."""
    anchor = os.environ.get(ANCHOR_ENV)
    if anchor is None:
        return None
    count, report = validate_measurement(project, os.environ, anchor)
    if output is not None:
        atomic_write_bytes_confined(project, output, json.dumps(report, sort_keys=True).encode())
    return count, f"{report['totals']['percent_covered']:.2f}"


__all__ = ["consume_measurement", "prepare_measurement", "publish_measurement"]
