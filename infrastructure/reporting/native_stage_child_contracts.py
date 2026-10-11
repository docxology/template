"""Fixed Source stage-child DATA shape; validation never constructs an owner."""

from __future__ import annotations

import hashlib
import math
import re
from pathlib import Path
from typing import Any

from infrastructure.core.bytecode_audit import MAX_EXECUTIONS
from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.core.script_discovery import discover_analysis_scripts
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot

WORKER = "infrastructure.reporting.native_stage_child_worker"
SCHEMA = "template-fixed-native-stage-child-v2"
OBSERVATION_SCHEMA = "template-fixed-native-stage-child-observation-v1"
PACKET_SCHEMA = "template-fixed-native-stage-child-packet-v1"
PURPOSE = "native-stage-child"
STAGE_SCRIPTS = frozenset(
    {
        "scripts/pipeline/stage_02_analysis.py",
        "scripts/pipeline/stage_03_render.py",
        "scripts/pipeline/stage_04_validate.py",
    }
)
SPEC_FIELDS = frozenset(
    {
        "schema_version",
        "scope",
        "run_id",
        "pipeline_run_id",
        "stage_key",
        "nonce",
        "directory",
        "source",
        "implementation",
        "request",
        "request_digest",
        "protocol",
        "script",
        "cwd",
        "parent_pid",
        "parent_directory",
        "parent_platform",
        "deadline_monotonic",
        "parent_deadline_monotonic",
        "closure_identity",
        "prefix_identity",
        "directory_identity",
        "source_audit_roots",
    }
)


def binding(snapshot: ArtifactSnapshot) -> dict[str, str]:
    return {"path": snapshot.relative, "sha256": snapshot.sha256}


def validate_artifact_bindings(values: object) -> None:
    """Closed bounded DATA rows; neither hashes nor paths create authority."""
    if not isinstance(values, list) or len(values) > MAX_EXECUTIONS:
        raise ValueError("native stage retained binding roster exceeds its existing bound")
    seen: set[str] = set()
    for item in values:
        if (
            not isinstance(item, dict)
            or set(item) != {"path", "sha256"}
            or not isinstance(item["path"], str)
            or not item["path"]
            or Path(item["path"]).is_absolute()
            or ".." in Path(item["path"]).parts
            or "\\" in item["path"]
            or "\0" in item["path"]
            or item["path"] in seen
            or not isinstance(item["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None
        ):
            raise ValueError("native stage retained binding roster repeats or has unsafe/ambiguous fields")
        seen.add(item["path"])


def audit_roots(root: Path, sdk: Path, scope: str) -> tuple[Path, ...]:
    if scope not in PUBLIC_PROJECT_NAMES:
        raise ValueError("native stage child requires an exact Source-owned public scope")
    project = root / "projects" / scope
    return sdk, root / "scripts", project / "src", project / "scripts"


def validate_request(
    source: NativeSourceContext,
    scope: str,
    snapshot: ArtifactSnapshot,
    *,
    deadline: float,
    original_root_label: Path | None = None,
) -> tuple[dict[str, Any], str, str]:
    """Bind a fixed existing stage or actual Source-discovered analysis leaf."""
    remaining(deadline)
    root = source.bindings.current_root if original_root_label is None else original_root_label
    project = root / "projects" / scope
    payload = snapshot.json_object()
    argv = payload.get("argv")
    if (
        scope not in PUBLIC_PROJECT_NAMES
        or payload.get("schema") not in {"template-python-stage/3", "template-python-analysis/4"}
        or payload.get("repo_root") != str(root)
        or payload.get("project_root") != str(project)
        or not isinstance(argv, list)
        or not argv
        or len(argv) > 1000
        or any(not isinstance(value, str) or "\0" in value for value in argv)
        or not isinstance(payload.get("run_id"), str)
        or not payload["run_id"]
        or not isinstance(payload.get("stage_key"), str)
        or not payload["stage_key"]
        or payload.get("cwd") not in {str(root), str(project)}
    ):
        raise ValueError("native stage request differs from its fixed Source scope/roots/argv/run/cwd")
    script = Path(argv[0])
    if not script.is_absolute() or ".." in script.parts:
        raise ValueError("native stage request omitted its actual confined Source script")
    relative = script.relative_to(root).as_posix()
    protocol = "analysis" if payload["schema"] == "template-python-analysis/4" else "stage"
    if protocol == "stage":
        if relative not in STAGE_SCRIPTS:
            raise ValueError("native stage role is limited to fixed Source analysis/render/validation stages")
    else:
        hydration = f"projects/{scope}/scripts/z_generate_manuscript_variables.py"
        hydration_key = "hydration:scripts/z_generate_manuscript_variables.py"
        if payload["stage_key"] == hydration_key:
            authored_hydration = any(name == hydration and kind == "file" for name, kind, _ in source.source_records)
            if relative != hydration or not authored_hydration or payload["cwd"] != str(project):
                raise ValueError("native stage hydration differs from its one actual held Source script/project cwd")
        else:
            selected_project = source.bindings.current_root / "projects" / scope
            declared = discover_analysis_scripts(source.bindings.current_root, scope, selected_project)
            selected = {path.relative_to(source.bindings.current_root).as_posix() for path in declared}
            if (
                relative not in selected
                or payload["stage_key"] != "analysis:" + Path(relative).relative_to(f"projects/{scope}").as_posix()
                or payload["cwd"] != str(root)
            ):
                raise ValueError("native stage analysis leaf is absent from actual Source-owned discovery")
        if (
            not isinstance(payload.get("analysis_nonce"), str)
            or re.fullmatch(r"[0-9a-f]{32}", payload["analysis_nonce"]) is None
            or payload.get("original_deadline_monotonic") != deadline
            and original_root_label is None
        ):
            raise ValueError("native stage analysis request differs from its original nonce/deadline")
    authored = source.current_source_reader.read(relative, max_bytes=8 * 1024 * 1024)
    if authored.content != source.reference.read(relative):
        raise ValueError("native stage script differs from independently held original Source")
    if len(snapshot.content) > (16 * 1024 * 1024 if protocol == "analysis" else 1024 * 1024):
        raise ValueError("native stage request exceeds its unchanged Source protocol ceiling")
    remaining(deadline)
    return payload, protocol, hashlib.sha256(authored.content).hexdigest()


def validate_specification(spec: dict[str, Any]) -> None:
    if (
        set(spec) != SPEC_FIELDS
        or spec["schema_version"] != SCHEMA
        or spec["scope"] not in PUBLIC_PROJECT_NAMES
        or not isinstance(spec["run_id"], str)
        or re.fullmatch(r"[0-9a-f]{32}", spec["run_id"]) is None
        or not isinstance(spec["nonce"], str)
        or re.fullmatch(r"[0-9a-f]{32}", spec["nonce"]) is None
        or not isinstance(spec["pipeline_run_id"], str)
        or not spec["pipeline_run_id"]
        or not isinstance(spec["stage_key"], str)
        or not spec["stage_key"]
        or type(spec["parent_pid"]) is not int
        or spec["parent_pid"] <= 0
        or spec["protocol"] not in {"stage", "analysis"}
        or not isinstance(spec["directory"], str)
        or not spec["directory"]
        or "\0" in spec["directory"]
        or "\\" in spec["directory"]
        or not isinstance(spec["cwd"], str)
        or not Path(spec["cwd"]).is_absolute()
        or "\0" in spec["cwd"]
        or ".." in Path(spec["cwd"]).parts
        or not isinstance(spec["request_digest"], str)
        or re.fullmatch(r"[0-9a-f]{64}", spec["request_digest"]) is None
        or not isinstance(spec["source"], dict)
        or not isinstance(spec["source_audit_roots"], list)
        or len(spec["source_audit_roots"]) != 4
        or any(
            not isinstance(item, str) or "\0" in item or not Path(item).is_absolute()
            for item in spec["source_audit_roots"]
        )
        or not isinstance(spec["parent_platform"], str)
        or not spec["parent_platform"]
        or not isinstance(spec["parent_directory"], str)
        or not spec["parent_directory"]
        or "\0" in spec["parent_directory"]
        or "\\" in spec["parent_directory"]
        or any(
            type(spec[name]) not in (int, float) or not math.isfinite(spec[name])
            for name in ("deadline_monotonic", "parent_deadline_monotonic")
        )
        or not spec["deadline_monotonic"] <= spec["parent_deadline_monotonic"]
    ):
        raise ValueError("native stage specification fields/role/identities/original clocks differ")
    for name in ("closure_identity", "prefix_identity", "directory_identity"):
        value = spec[name]
        if not isinstance(value, list) or len(value) != 2 or any(type(item) is not int or item < 0 for item in value):
            raise ValueError("native stage specification omitted its actual held directory identity")
    for name in ("implementation", "request", "script"):
        value = spec[name]
        if (
            not isinstance(value, dict)
            or set(value) != {"path", "sha256"}
            or not isinstance(value["path"], str)
            or Path(value["path"]).is_absolute()
            or ".." in Path(value["path"]).parts
            or "\\" in value["path"]
            or "\0" in value["path"]
            or not isinstance(value["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", value["sha256"]) is None
        ):
            raise ValueError("native stage specification needs closed confined artifact/Source bindings")
    directory = Path(spec["directory"])
    parent = Path(spec["parent_directory"])
    if (
        parent.is_absolute()
        or ".." in parent.parts
        or not parent.is_relative_to("output/readiness")
        or directory.is_absolute()
        or ".." in directory.parts
        or not directory.is_relative_to(parent / "native-stage")
        or len(directory.relative_to(parent / "native-stage").parts) != 4
        or directory.name != "child-" + spec["nonce"]
    ):
        raise ValueError("native stage specification directory escaped fixed runtime evidence scope")
    if spec["request"]["path"] != (directory / "request.json").as_posix():
        raise ValueError("native stage request is not in its actual child scratch directory")


def verify_stage_observation(
    spec: dict[str, Any],
    observation: dict[str, Any],
    *,
    child_pid: int,
    request: ArtifactSnapshot,
) -> None:
    fields = {
        "schema_version",
        "scope",
        "run_id",
        "pipeline_run_id",
        "stage_key",
        "nonce",
        "request",
        "request_digest",
        "worker_pid",
        "parent_pid",
        "stage_return_code",
        "stage_exception",
        "result",
        "original_checkpoint",
        "nested_tool_artifacts",
        "stage_children",
        "stage_artifacts",
        "script_intent_authority",
    }
    if (
        set(observation) != fields
        or observation["schema_version"] != OBSERVATION_SCHEMA
        or any(
            observation[key] != spec[key]
            for key in ("scope", "run_id", "pipeline_run_id", "stage_key", "nonce", "request_digest")
        )
        or observation["request"] != binding(request)
        or canonical_digest(request.json_object()) != spec["request_digest"]
        or observation["worker_pid"] != child_pid
        or observation["parent_pid"] != spec["parent_pid"]
        or not isinstance(observation["nested_tool_artifacts"], list)
        or not isinstance(observation["stage_children"], list)
        or not isinstance(observation["stage_artifacts"], list)
        or observation["script_intent_authority"]
        != "Source stage worker only; child signed OS belongs to parent ToolAPI"
    ):
        raise ValueError("native stage observation differs from its actual parent/request/child process")
    returned = observation["stage_return_code"]
    if returned is not None and (type(returned) is not int or not 0 <= returned <= 255):
        raise ValueError("native stage worker returned an invalid Source intent convention")
    if returned is None and not isinstance(observation["stage_exception"], dict):
        raise ValueError("native stage observation omitted both returned intent and its actual exception")
    exception = observation["stage_exception"]
    if (
        returned is not None
        and exception is not None
        or exception is not None
        and (
            set(exception) != {"class", "module"}
            or any(not isinstance(exception[name], str) or not exception[name] for name in ("class", "module"))
        )
    ):
        raise ValueError("native stage observation has inconsistent returned intent/exception DATA")
    for name in ("nested_tool_artifacts", "stage_children", "stage_artifacts"):
        validate_artifact_bindings(observation[name])
