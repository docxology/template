"""Authenticate full Original Pitch axes, then rerun each once in genuine Current."""

from __future__ import annotations

import copy
import hashlib
import json
from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import ZipFile

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_checks import parse_native_bytes
from infrastructure.reporting.native_format_acceptance_evidence import _file, _tool
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_office_reference_visual import inspect_office_reference_projection
from infrastructure.reporting.native_pitch_control_mutations import mutate_pitch
from infrastructure.reporting.native_pitch_control_plan import SCOPE, PitchTarget, compile_pitch_control_plan
from infrastructure.reporting.native_pitch_control_run import SCHEMA
from infrastructure.reporting.native_pitch_source_layout import LAYOUT_CANONICALIZATION, LAYOUT_SCHEMA
from infrastructure.reporting.native_pitch_control_supervisor import supervise_pitch_controls
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

FIELDS = {
    "schema_version",
    "scope",
    "name",
    "run_id",
    "source",
    "plan",
    "references",
    "rows",
    "tool_artifacts",
    "oracle_exit_code",
}


def _identity(content: bytes, kind: str) -> Any:
    """All uncompressed PPTX member bytes; only ZIP container timestamps vary."""
    if kind == "pdf":
        return hashlib.sha256(content).hexdigest()
    parse_native_bytes("pptx", content)
    with ZipFile(BytesIO(content)) as archive:
        return {name: hashlib.sha256(archive.read(name)).hexdigest() for name in sorted(archive.namelist())}


def _pixels(native: dict[str, Any], reader: SnapshotReader) -> tuple[bytes, ...]:
    return tuple(
        _file({"path": row["path"], "sha256": row["sha256"]}, reader).content for row in native["raster"]["rasters"]
    )


def _facts(observation: dict[str, Any]) -> dict[str, Any]:
    """Only remove transport bindings after complete actual native page parity.

    PDF object/container hashes are checked through their exact retained inputs
    and actual tools. Every rendered glyph/vector/image/pixel is compared by
    _same_row before these observation fields are compared. No source targets,
    note text, font floors, geometry, diagnostics or decoder outcomes are erased.
    """
    value = copy.deepcopy(
        {key: observation[key] for key in ("projection", "package", "reference", "findings", "blockers", "status")}
    )
    for page in value["projection"]["pages"]:
        page.pop("pdf_sha256")
        if page.get("qr") is not None:
            page["qr"].pop("tool_artifact")
            page["qr"].pop("runtime_artifact")
    if value["package"] is not None:
        value["package"].pop("input_sha256")
        for page in value["package"]["pages"]:
            if page["qr"] is not None:
                page["qr"].pop("tool_artifact")
                page["qr"].pop("runtime_artifact")
    normalised: dict[str, Any] = json.loads(json.dumps(value))
    return normalised


def _argument(value: str, old_root: Path, old_leaf: Path, root: Path, leaf: Path) -> str:
    """Reproduce only exact Source-owned absolute native path operands."""
    prefix = "-env:UserInstallation="
    if value.startswith(prefix):
        old = old_leaf.as_uri()
        if not value[len(prefix) :].startswith(old + "/"):
            raise ValueError("Pitch Office native profile escapes its exact Original child")
        return prefix + leaf.as_uri() + value[len(prefix) + len(old) :]
    if value == str(old_leaf) or value.startswith(str(old_leaf) + "/"):
        return str(leaf) + value[len(str(old_leaf)) :]
    if value == str(old_root) or value.startswith(str(old_root) + "/"):
        return str(root) + value[len(str(old_root)) :]
    return value


def _tools(
    original: dict[str, Any],
    fresh: dict[str, Any],
    before_reader: SnapshotReader,
    reader: SnapshotReader,
    *,
    before_run: str,
    run_id: str,
    old_root: Path,
    old_leaf: Path,
    root: Path,
    leaf: Path,
) -> None:
    left, right = original["tool_artifacts"], fresh["tool_artifacts"]
    if len(left) != len(right) or not left:
        raise ValueError("Pitch complete Original/Current native tool roster differs")
    for before, after in zip(left, right, strict=True):
        held, current = _file(before, before_reader).json_object(), _file(after, reader).json_object()
        code = held["original_exit_code"]
        if type(code) is not int or code not in {0, 4} or current["original_exit_code"] != code:
            raise ValueError("Pitch nested actual native tool has an unintended OS outcome")
        if code == 4 and (held["tool"] != "zbarimg" or not held["purpose"].startswith("qr-decode-")):
            raise ValueError("Pitch only admits the genuine no-symbol QR decoder native outcome")
        _tool(before, before_reader, before_run, held["tool"], held["purpose"], held["command"][1:], code)
        _tool(after, reader, run_id, current["tool"], current["purpose"], current["command"][1:], code)
        expected = [_argument(arg, old_root, old_leaf, root, leaf) for arg in held["command"][1:]]
        if current["command"][1:] != expected or any(
            held[key] != current[key] for key in ("tool", "purpose", "executable", "executable_sha256")
        ):
            raise ValueError("Pitch fresh Source-selected command or actual native executable body differs")


def _same_row(
    before: dict[str, Any],
    fresh: dict[str, Any],
    before_reader: SnapshotReader,
    reader: SnapshotReader,
    *,
    deadline: float,
) -> None:
    if set(before) != {"target", "artifact", "input", "candidate", "parser", "observation", "oracle_exit_code"} or set(
        before
    ) != set(fresh):
        raise ValueError("Pitch native row lost its exact selected Source fields")
    if any(before[key] != fresh[key] for key in ("target", "artifact", "parser", "oracle_exit_code")):
        raise ValueError("Pitch Original/Current row has a different Source target, parser or required refusal")
    target = PitchTarget(**fresh["target"])
    kind = fresh["artifact"]["format"]
    source, current = _file(before["input"], before_reader), _file(fresh["input"], reader)
    if source.relative != fresh["artifact"]["path"] or current.relative != source.relative:
        raise ValueError("Pitch control baseline is another configured artifact")
    if _identity(source.content, kind) != _identity(current.content, kind):
        raise ValueError("Pitch independent Current actual configured native input body differs")
    held_candidate, candidate = _file(before["candidate"], before_reader), _file(fresh["candidate"], reader)
    rebuilt = mutate_pitch(source.content, kind, target, deadline=deadline)
    if (
        _identity(held_candidate.content, kind) != _identity(rebuilt, kind)
        or _identity(candidate.content, kind) != _identity(held_candidate.content, kind)
        or before["parser"] != parse_native_bytes(kind, held_candidate.content)
    ):
        raise ValueError("Pitch Original valid native mutant differs from independent Current Source mutation")
    code = target.intended_diagnostic
    for row in (before, fresh):
        observed = row["observation"]
        if (
            type(row["oracle_exit_code"]) is not int
            or row["oracle_exit_code"] != (0 if code is None else 1)
            or observed["blockers"]
            or code is None
            and (observed["status"] != "pass" or observed["findings"])
            or code is not None
            and (
                observed["status"] != "fail"
                or not any(
                    finding.get("code") == code
                    and (finding.get("page") == target.page or kind == "pptx" and code == "pitch.package.source.layout")
                    for finding in observed["findings"]
                )
            )
        ):
            raise ValueError("Pitch actual per-target baseline/refusal differs from the Source page diagnostic")
    old_native, native = before["observation"]["native"], fresh["observation"]["native"]
    parity = inspect_office_reference_projection(
        _file(old_native["pdf"], before_reader).content,
        _pixels(old_native, before_reader),
        _file(native["pdf"], reader).content,
        _pixels(native, reader),
        deadline=deadline,
    )
    if parity["findings"] or _facts(before["observation"]) != _facts(fresh["observation"]):
        raise ValueError("Pitch complete genuine Original/Current glyph/pixel/layout/note/link/QR outcomes differ")


def replay_pitch_controls(
    records: object,
    reader: SnapshotReader,
    *,
    current_source: NativeSourceContext,
    directory: Path,
    formats: tuple[str, ...],
    interpreter: Path,
    env: dict[str, str],
    deadline: float,
) -> dict[str, Any]:
    """Original OS/Code first; fresh separate-root Current executes each axis once."""
    from infrastructure.reporting.native_pitch_control_custody import PitchControlReaderOperation

    operation = require_native_operation(reader)
    original = operation.originals.get(SCOPE)
    if original is None or deadline != operation.deadline or reader.native_producer_operation is not None:
        raise ValueError("Pitch replay requires genuine externally held Original and its existing deadline")
    if not isinstance(records, list) or not records or not all(isinstance(row, dict) for row in records):
        raise ValueError("Pitch replay requires the complete actual Original child roster")
    context = PitchControlReaderOperation(
        operation.source, reader, records, scope=SCOPE, run_id=original.run_id, deadline=deadline
    )
    controls = SnapshotReader(reader.root, native_control_operation=context)
    held = []
    for item in records:
        remaining(deadline)
        authority = context.child(item, controls)
        raw = _file(item["artifact"], controls).json_object()
        if (
            set(raw) != FIELDS
            or raw["schema_version"] != SCHEMA
            or raw["scope"] != SCOPE
            or raw["name"] != item["name"]
            or raw["run_id"] != original.run_id
            or raw["source"] != authority["source"]
            or raw["oracle_exit_code"] != item["original_exit_code"]
            or authority["specification"]["caller_deadline_monotonic"] != original.original_deadline
        ):
            raise ValueError("Pitch actual Original axis source/run/clock/role differs")
        for binding in raw["tool_artifacts"]:
            tool = _file(binding, controls).json_object()
            _tool(
                binding,
                controls,
                original.run_id,
                tool["tool"],
                tool["purpose"],
                tool["command"][1:],
                tool["original_exit_code"],
            )
        held.append((raw, authority))
    owner = current_native_producer_operation()
    if (
        not isinstance(current_source, NativeSourceContext)
        or owner is None
        or owner.source is not current_source
        or owner.deadline != deadline
        or owner.run_id != current_source.bindings.run_id
        or current_source.reference.commit != operation.source.reference.commit
        or current_source.reference.source_identity != operation.source.reference.source_identity
        or current_source.bindings.expected_commit != operation.source.bindings.expected_commit
        or current_source.bindings.expected_source_identity != operation.source.bindings.expected_source_identity
        or current_source.bindings.expected_implementation_bytes
        != operation.source.bindings.expected_implementation_bytes
        or current_source.bindings.selected_sdk_package_root != operation.source.bindings.selected_sdk_package_root
        or current_source.bindings.current_root_identity == operation.source.bindings.current_root_identity
        or owner.run_id in {operation.source.bindings.run_id, original.run_id}
        or not directory.is_relative_to(owner.stage_scope_directory(SCOPE))
    ):
        raise ValueError("Pitch Current lacks genuine separate Source/root/run, shared SDK and unchanged owner clock")
    root = current_source.bindings.current_root
    for protected in (
        reader.root,
        operation.source.reference.root,
        operation.source.bindings.selected_sdk_package_root,
    ):
        if root.is_relative_to(protected) or protected.is_relative_to(root):
            raise ValueError("Pitch fresh Current overlaps Original/Source/selected SDK")
    current_reader = SnapshotReader(root, native_producer_operation=owner)
    plan, _ = compile_pitch_control_plan(root, current_reader, formats=formats, deadline=deadline)
    if [row["name"] for row in records] != plan["active_controls"] or any(raw["plan"] != plan for raw, _ in held):
        raise ValueError(
            "Pitch Original complete Source pair/page/applicability plan differs from independently compiled Current"
        )
    fresh_records = supervise_pitch_controls(
        root, directory, formats=formats, interpreter=interpreter, env=env, deadline=deadline, run_id=owner.run_id
    )
    fresh_context = PitchControlReaderOperation(
        current_source, current_reader, fresh_records, scope=SCOPE, run_id=owner.run_id, deadline=deadline
    )
    fresh_reader = SnapshotReader(root, native_control_operation=fresh_context)
    outcomes = []
    for item, (raw, authority), new in zip(records, held, fresh_records, strict=True):
        remaining(deadline)
        current_authority = fresh_context.child(new, fresh_reader)
        fresh = _file(new["artifact"], fresh_reader).json_object()
        if (
            fresh["plan"] != plan
            or raw["name"] != fresh["name"]
            or raw["oracle_exit_code"] != fresh["oracle_exit_code"]
            or [row["target"] for row in raw["rows"]] != plan["targets"][raw["name"]]
            or [row["target"] for row in fresh["rows"]] != plan["targets"][fresh["name"]]
            or set(raw["references"]) != set(fresh["references"])
        ):
            raise ValueError("Pitch genuine Current altered the complete selected target or source reference roster")
        old_root = Path(authority["source"]["current_mirror"]["root"])
        old_leaf = old_root / authority["specification"]["directory"]
        leaf = root / current_authority["specification"]["directory"]
        _tools(
            raw,
            fresh,
            controls,
            fresh_reader,
            before_run=original.run_id,
            run_id=owner.run_id,
            old_root=old_root,
            old_leaf=old_leaf,
            root=root,
            leaf=leaf,
        )
        for identity, reference in raw["references"].items():
            kind = identity.rsplit(":", 1)[1]
            if kind == "pptx" and any(
                value.get("schema_version") != LAYOUT_SCHEMA or value.get("canonicalization") != LAYOUT_CANONICALIZATION
                for value in (reference, fresh["references"][identity])
            ):
                raise ValueError("Pitch source layout reference canonicalization requires fresh versioned evidence")
            if _identity(_file(reference["input"], controls).content, kind) != _identity(
                _file(fresh["references"][identity]["input"], fresh_reader).content, kind
            ):
                raise ValueError("Pitch Current independent complete Source layout/theme reference differs")
        for before, after in zip(raw["rows"], fresh["rows"], strict=True):
            _same_row(before, after, controls, fresh_reader, deadline=deadline)
        outcomes.append(
            {
                "name": raw["name"],
                "targets": plan["targets"][raw["name"]],
                "original_exit_code": item["original_exit_code"],
                "current_exit_code": new["original_exit_code"],
                "current_artifact": new["artifact"],
                "target_outcomes": [
                    {
                        "target": before["target"],
                        "original_exit_code": before["oracle_exit_code"],
                        "current_exit_code": after["oracle_exit_code"],
                        "intended_diagnostic": after["target"]["intended_diagnostic"],
                    }
                    for before, after in zip(raw["rows"], fresh["rows"], strict=True)
                ],
            }
        )
    owner.verify(current_reader, run_id=owner.run_id, deadline=deadline)
    operation.verify(reader)
    if not controls.unchanged() or not fresh_reader.unchanged():
        raise ValueError("Pitch genuine Original/Current selected native graph changed during replay")
    remaining(deadline)
    return {
        "schema_version": "template-native-pitch-complete-control-replay-v1",
        "scope": SCOPE,
        "source_binding": [current_source.reference.commit, current_source.reference.source_identity],
        "plan": plan,
        "original_run_id": original.run_id,
        "current_run_id": owner.run_id,
        "outcomes": outcomes,
        "component_status": "passed",
    }
