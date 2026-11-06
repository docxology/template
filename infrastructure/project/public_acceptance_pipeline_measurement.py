"""Exact portable bytes of the executor's genuinely held project measurement.

Project coordinates remain DATA. Only explicit current-root bindings are opened
by the independent reader; no producer path or receipt can mint a held anchor.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from infrastructure.core.files.secure_write import read_bytes_confined
from infrastructure.core.pipeline.fingerprints import source_content_fingerprint
from infrastructure.core.testing.project_test_measurement import (
    MEASUREMENT_SCHEMA,
    measurement_coverage_report,
    measurement_source_paths,
    measurement_execution_snapshot,
    project_measurement_inventory,
    measurement_path,
    validate_measurement,
)
from infrastructure.core.testing.pytest_orchestration import project_declared_coverage_floor
from infrastructure.project.installed_acceptance_artifacts import write_binary
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-portable-project-measurement-v1"
_MAX_FILE = 64 * 1024 * 1024
_MAX_TOTAL = 256 * 1024 * 1024
_MAX_FILES = 4000


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _context(project: Path, execution: dict[str, Any]) -> tuple[tuple[str, str, str], dict[str, str]]:
    run_id, plan = execution["run_id"], execution["plan_digest"]
    if not isinstance(run_id, str) or not run_id or re.fullmatch(r"[0-9a-f]{64}", plan) is None:
        raise ValueError("portable measurement requires the actual original run/plan")
    return (str(project), run_id, plan), {"PIPELINE_RUN_ID": run_id, "PIPELINE_PLAN_DIGEST": plan}


def _bytes(project: Path, path: Path) -> bytes:
    return read_bytes_confined(project, path, max_bytes=_MAX_FILE)


def capture_project_measurement(executor: Any, execution: dict[str, Any]) -> dict[str, Any] | None:
    """Called by the actual child while its verified Stage01 anchor is still held."""
    project = executor.config.project_dir
    context, env = _context(project, execution)
    path = measurement_path(project, execution["run_id"])
    held = executor._project_measurement
    if held is None:
        if path.exists() or path.is_symlink():
            raise ValueError("published project measurement has no executor-held original anchor")
        return None
    if held[0] != context or re.fullmatch(r"[0-9a-f]{64}", held[1]) is None:
        raise ValueError("executor-held project measurement context differs from the actual child")
    count, _ = validate_measurement(project, env, held[1])
    return {
        "schema": SCHEMA,
        "context": list(context),
        "anchor_sha256": held[1],
        "measurement_project_path": path.relative_to(project).as_posix(),
        "passed": count,
    }


def _capture(project: Path, facts: dict[str, Any]) -> dict[str, Any] | None:
    value = facts["project_test_measurement"]
    if value is None:
        return None
    context, _ = _context(project, facts["execution"])
    if (
        not isinstance(value, dict)
        or set(value) != {"schema", "context", "anchor_sha256", "measurement_project_path", "passed"}
        or value["schema"] != SCHEMA
        or value["context"] != list(context)
        or re.fullmatch(r"[0-9a-f]{64}", value["anchor_sha256"]) is None
        or value["measurement_project_path"]
        != measurement_path(project, facts["execution"]["run_id"]).relative_to(project).as_posix()
        or type(value["passed"]) is not int
        or value["passed"] <= 0
    ):
        raise ValueError("portable measurement lost its original held context/hash/count")
    return value


def _references(value: dict[str, Any], measurement_relative: str) -> list[dict[str, str]]:
    if (
        value.get("schema") != MEASUREMENT_SCHEMA
        or not isinstance(value.get("receipts"), list)
        or not value["receipts"]
    ):
        raise ValueError("portable measurement requires the current project-coordinate schema and all callbacks")
    if len(value["receipts"]) > _MAX_FILES:
        raise ValueError("portable measurement callback census exceeds Source bounds")
    nonce = value["nonce"]
    if not isinstance(nonce, str) or re.fullmatch(r"[0-9a-f]{32}", nonce) is None:
        raise ValueError("portable measurement nonce is malformed")
    directory = Path(measurement_relative).parent / nonce
    if value["directory"] != directory.as_posix():
        raise ValueError("portable measurement callback directory differs from its original nonce/run")
    rows = [*value["receipts"], value["coverage"], value["database"]]
    names = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"project_path", "sha256"}:
            raise ValueError("portable measurement requires exact project-coordinate commitments")
        name = row["project_path"]
        if (
            not isinstance(name, str)
            or not name
            or "\\" in name
            or "\0" in name
            or Path(name).is_absolute()
            or ".." in Path(name).parts
            or Path(name).as_posix() != name
            or re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) is None
        ):
            raise ValueError("portable measurement project coordinate is unsafe")
        names.append(name)
    if (
        len(names) != len(set(names))
        or value["coverage"]["project_path"] != "coverage_project.json"
        or value["database"]["project_path"] != ".coverage.project"
    ):
        raise ValueError("portable measurement omitted, duplicated or changed a declared artifact role")
    if any(
        Path(row["project_path"]).parent != directory
        or re.fullmatch(r"execution-[0-9]+\.json", Path(row["project_path"]).name) is None
        for row in value["receipts"]
    ):
        raise ValueError("portable measurement callback is outside its exact original directory")
    return rows


def retain_project_measurement(
    root: Path,
    directory: Path,
    copied: Path,
    scope: str,
    facts: dict[str, Any],
    outputs: list[dict[str, Any]],
    output_bytes: int,
) -> dict[str, Any] | None:
    """Copy complete actual project artifacts before the producer root disappears."""
    if scope not in PUBLIC_PROJECT_NAMES:
        raise ValueError("portable measurement is outside the canonical public roster")
    project = copied / "projects" / scope
    captured = _capture(project, facts)
    files = {row["relative"]: row for row in outputs}
    relative = measurement_path(project, facts["execution"]["run_id"]).relative_to(project / "output").as_posix()
    if captured is None:
        if relative in files:
            raise ValueError("portable output contains an unheld project measurement")
        return None
    if relative not in files or files[relative]["sha256"] != captured["anchor_sha256"]:
        raise ValueError("portable output omitted the exact executor-held measurement")
    expected_measurement = {
        "path": (directory / "pipeline-outputs" / relative).relative_to(root).as_posix(),
        "sha256": captured["anchor_sha256"],
    }
    if files[relative]["binding"] != expected_measurement:
        raise ValueError("portable measurement original canonical output coordinate differs")
    raw = _bytes(project, project / captured["measurement_project_path"])
    if _hash(raw) != captured["anchor_sha256"]:
        raise ValueError("original measurement changed before portable retention")
    value = json.loads(raw)
    artifacts = []
    total, count = output_bytes, len(outputs)
    for row in _references(value, captured["measurement_project_path"]):
        name = row["project_path"]
        body = _bytes(project, project / name)
        if _hash(body) != row["sha256"]:
            raise ValueError("original measurement artifact changed before portable retention")
        if name.startswith("output/"):
            original = files.get(name.removeprefix("output/"))
            if original is None or original["sha256"] != row["sha256"]:
                raise ValueError("portable pipeline omitted an original measurement callback")
            binding = original["binding"]
            if binding != {
                "path": (directory / "pipeline-outputs" / Path(name).relative_to("output"))
                .relative_to(root)
                .as_posix(),
                "sha256": row["sha256"],
            }:
                raise ValueError("portable measurement callback canonical output coordinate differs")
        else:
            total += len(body)
            count += 1
            if total > _MAX_TOTAL or count > _MAX_FILES:
                raise ValueError("portable measurement exceeds the existing pipeline retained-byte census")
            binding = write_binary(root, directory / "project-test-measurement" / name, body)
        artifacts.append({"project_path": name, "binding": binding})
    return {"schema": SCHEMA, "measurement_artifact": files[relative]["binding"], "artifacts": artifacts}


def _runtime(value: dict[str, Any], process: dict[str, Any], facts: dict[str, Any]) -> None:
    runtime = value["runtime"]
    fields = {
        "schema",
        "executable",
        "resolved_executable",
        "binary_sha256",
        "prefix",
        "python_minor",
        "configuration_sha256",
        "site_roots",
        "installation_metadata",
        "dependency_scope",
    }
    if (
        not isinstance(runtime, dict)
        or set(runtime) != fields
        or runtime["schema"] != "template-selected-python-runtime/1"
        or value["interpreter"] != process["selected_interpreter"]
        or runtime["executable"] != value["interpreter"]
        or runtime["resolved_executable"] != process["executable"]
        or runtime["binary_sha256"] != process["executable_sha256"]
        or not facts["runtime"]["python_version"].startswith(runtime["python_minor"] + ".")
        or runtime["dependency_scope"] != "metadata-record-declarations"
        or not isinstance(runtime["site_roots"], list)
        or not runtime["site_roots"]
        or len(runtime["site_roots"]) != len(set(runtime["site_roots"]))
        or not isinstance(runtime["installation_metadata"], dict)
        or not runtime["installation_metadata"]
        or not isinstance(runtime["configuration_sha256"], str)
        or runtime["configuration_sha256"] != ""
        and re.fullmatch(r"[0-9a-f]{64}", runtime["configuration_sha256"]) is None
    ):
        raise ValueError("portable measurement original runtime differs from its actual original process")
    for path in [runtime["executable"], runtime["resolved_executable"], runtime["prefix"], *runtime["site_roots"]]:
        if not isinstance(path, str) or not Path(path).is_absolute() or ".." in Path(path).parts:
            raise ValueError("portable measurement original runtime coordinate is malformed")
    for name, digest in runtime["installation_metadata"].items():
        if (
            not isinstance(name, str)
            or Path(name).is_absolute()
            or ".." in Path(name).parts
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            raise ValueError("portable measurement original installation declaration is malformed")


def validate_retained_project_measurement(
    scope: str,
    custody: dict[str, Any],
    facts: dict[str, Any],
    process: dict[str, Any],
    reader: SnapshotReader,
    directory: Path,
) -> None:
    """Read the complete retained closure with the original owner's predicates."""
    if reader.operation_deadline is not None:
        remaining(reader.operation_deadline)
    project = Path(facts["producer_root"]) / "projects" / scope
    captured = _capture(project, facts)
    retention = custody["project_test_measurement"]
    files = {row["relative"]: row for row in custody["output_after"]}
    relative = measurement_path(project, facts["execution"]["run_id"]).relative_to(project / "output").as_posix()
    if captured is None:
        if retention is not None or relative in files:
            raise ValueError("portable reader cannot adopt an unheld project measurement")
        return
    if (
        not isinstance(retention, dict)
        or set(retention) != {"schema", "measurement_artifact", "artifacts"}
        or retention["schema"] != SCHEMA
    ):
        raise ValueError("portable reader omitted the complete project measurement closure")
    expected_measurement = {
        "path": (directory / "pipeline-outputs" / relative).relative_to(reader.root).as_posix(),
        "sha256": captured["anchor_sha256"],
    }
    if (
        relative not in files
        or retention["measurement_artifact"] != expected_measurement
        or files[relative]["binding"] != expected_measurement
    ):
        raise ValueError("portable reader changed the original measurement coordinate")
    snapshot = reader.read(retention["measurement_artifact"]["path"])
    if snapshot.sha256 != captured["anchor_sha256"] or retention["measurement_artifact"]["sha256"] != snapshot.sha256:
        raise ValueError("portable measurement differs from its executor-held original hash")
    value = snapshot.json_object()
    current_project = reader.root / "projects" / scope
    _, env = _context(project, facts["execution"])
    floor = project_declared_coverage_floor(current_project)
    if (
        value.get("schema") != MEASUREMENT_SCHEMA
        or value["project"] != str(project)
        or value["repo"] != facts["producer_root"]
        or value["context"] != env
        or value["original_exit_code"] != 0
        or value["source"] != source_content_fingerprint(reader.root, current_project)
        or value["files"] != project_measurement_inventory(current_project)
        or floor is None
        or type(value["floor"]) not in (int, float)
        or not math.isfinite(value["floor"])
        or value["floor"] != floor
        or type(value["passed"]) is not int
        or value["passed"] != captured["passed"]
    ):
        raise ValueError("portable measurement original Source/run/floor/count differs")
    _runtime(value, process, facts)
    references = _references(value, captured["measurement_project_path"])
    rows = retention["artifacts"]
    if (
        not isinstance(rows, list)
        or len(rows) != len(references)
        or any(not isinstance(row, dict) or set(row) != {"project_path", "binding"} for row in rows)
    ):
        raise ValueError("portable measurement artifact inventory is incomplete")
    by_name = {row["project_path"]: row["binding"] for row in rows}
    if len(by_name) != len(rows) or set(by_name) != {row["project_path"] for row in references}:
        raise ValueError("portable measurement artifact inventory differs from every original reference")
    contents = {}
    for reference in references:
        if reader.operation_deadline is not None:
            remaining(reader.operation_deadline)
        name = reference["project_path"]
        binding = by_name[name]
        expected_path = (
            (directory / "project-test-measurement" / name).relative_to(reader.root).as_posix()
            if not name.startswith("output/")
            else (directory / "pipeline-outputs" / Path(name).relative_to("output")).relative_to(reader.root).as_posix()
        )
        if (
            set(binding) != {"path", "sha256"}
            or binding["path"] != expected_path
            or binding["sha256"] != reference["sha256"]
        ):
            raise ValueError("portable measurement canonical export coordinate differs")
        if name.startswith("output/") and files[name.removeprefix("output/")]["binding"] != binding:
            raise ValueError("portable measurement callback differs from its complete output inventory")
        held = reader.read(binding["path"])
        if held.sha256 != reference["sha256"]:
            raise ValueError("portable measurement retained artifact bytes changed")
        contents[name] = held.content
    receipts = value["receipts"]
    if len(receipts) != 1:
        raise ValueError("portable measurement requires its one original serial controller without retries")
    count = measurement_execution_snapshot(
        contents[receipts[0]["project_path"]], value["nonce"], value["arguments"], value["files"]
    )
    if count != value["passed"]:
        raise ValueError("portable measurement original membership differs")
    report = measurement_coverage_report(contents[value["coverage"]["project_path"]], floor)
    for source in measurement_source_paths(project, report):
        reader.read((Path("projects") / scope / source.relative_to(project)).as_posix())
    if reader.operation_deadline is not None:
        remaining(reader.operation_deadline)
    if not reader.unchanged():
        raise ValueError("portable measurement changed during independent byte readback")


__all__ = ["capture_project_measurement", "retain_project_measurement", "validate_retained_project_measurement"]
