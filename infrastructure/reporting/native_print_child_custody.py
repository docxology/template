"""Fixed Source-owned control child roles under a genuine enclosing native owner.

Retained records do not construct an original capability. Every child ToolAPI
event is authenticated by the actual live producer or externally held original
native worker before its command, raw stdout seals and audited Code are read.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.core.bytecode_audit import MAX_CACHE_BYTES, MAX_EXECUTIONS, canonical_code
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_office_cache_structure import verify_office_execution_cache
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

CHILD_SCHEMA = "template-source-owned-print-child-v1"
WORKER = "infrastructure.reporting.native_print_artifact_controls"
SLIDE_CHILD_SCHEMA = "template-source-owned-slide-child-v1"
SLIDE_WORKER = "infrastructure.reporting.native_slide_controls"
BROWSER_CHILD_SCHEMA = "template-source-owned-browser-child-v1"
SEMANTIC_BROWSER_CHILD_SCHEMA = "template-source-owned-browser-semantic-child-v1"
BROWSER_WORKER = "infrastructure.reporting.native_format_browser_oracles"
SEMANTIC_BROWSER_WORKER = "infrastructure.reporting.native_format_browser_semantic_controls"
OFFICE_SCIENTIFIC_CHILD_SCHEMA = "template-source-owned-office-scientific-child-v1"
OFFICE_SCIENTIFIC_WORKER = "infrastructure.reporting.native_office_scientific_controls"
WHOLE_PDF_CHILD_SCHEMA = "template-source-owned-whole-pdf-child-v1"
WHOLE_PDF_WORKER = "infrastructure.reporting.native_pdf_whole_control_worker"


@dataclass(frozen=True)
class _ControlRole:
    schema: str
    worker: str
    purpose: str
    observation_seal: str
    closure_seal: str
    project_code: bool
    required_sdk_modules: tuple[str, ...]
    extra_specification_fields: frozenset[str] = frozenset()


_PRINT_ROLE = _ControlRole(
    CHILD_SCHEMA,
    WORKER,
    "print-child",
    "PRINT_OBSERVATION_V2",
    "PRINT_CLOSURE_V2",
    True,
    (
        "reporting/native_print_artifact_controls.py",
        "reporting/native_print_artifact_observer.py",
        "reporting/native_source_external_admission.py",
    ),
)
_SLIDE_ROLE = _ControlRole(
    SLIDE_CHILD_SCHEMA,
    SLIDE_WORKER,
    "slide-child",
    "SLIDE_OBSERVATION_V1",
    "SLIDE_CLOSURE_V1",
    False,
    (
        "reporting/native_slide_controls.py",
        "reporting/native_slide_checks.py",
        "reporting/native_slide_source.py",
        "reporting/native_source_external_admission.py",
        "reporting/native_pdf_citation_runtime.py",
        "reporting/native_tool_process.py",
    ),
)

_BROWSER_ROLE = _ControlRole(
    BROWSER_CHILD_SCHEMA,
    BROWSER_WORKER,
    "browser-child",
    "BROWSER_OBSERVATION_V1",
    "BROWSER_CLOSURE_V1",
    False,
    (
        "reporting/native_format_browser_oracles.py",
        "reporting/native_source_external_admission.py",
        "reporting/native_tool_process.py",
    ),
)
_SEMANTIC_BROWSER_ROLE = _ControlRole(
    SEMANTIC_BROWSER_CHILD_SCHEMA,
    SEMANTIC_BROWSER_WORKER,
    "browser-semantic-child",
    "BROWSER_SEMANTIC_OBSERVATION_V1",
    "BROWSER_SEMANTIC_CLOSURE_V1",
    False,
    (
        "reporting/native_format_browser_semantic_controls.py",
        "reporting/native_format_browser_oracles.py",
        "reporting/native_source_external_admission.py",
        "reporting/native_tool_process.py",
    ),
)

_OFFICE_SCIENTIFIC_ROLE = _ControlRole(
    OFFICE_SCIENTIFIC_CHILD_SCHEMA,
    OFFICE_SCIENTIFIC_WORKER,
    "office-scientific-child",
    "OFFICE_SCIENTIFIC_OBSERVATION_V1",
    "OFFICE_SCIENTIFIC_CLOSURE_V1",
    False,
    (
        "reporting/native_office_scientific_controls.py",
        "reporting/native_office_content_witness.py",
        "reporting/native_office_reference.py",
        "reporting/native_office_reference_visual.py",
        "reporting/native_source_external_admission.py",
        "reporting/native_tool_process.py",
        "reporting/native_pdf_citation_runtime.py",
    ),
    frozenset({"kind", "epub_arguments"}),
)


_WHOLE_PDF_ROLE = _ControlRole(
    WHOLE_PDF_CHILD_SCHEMA,
    WHOLE_PDF_WORKER,
    "whole-pdf-child",
    "WHOLE_PDF_OBSERVATION_V1",
    "WHOLE_PDF_CLOSURE_V1",
    False,
    (
        "reporting/native_pdf_whole_control_worker.py",
        "reporting/native_pdf_whole_control_run.py",
        "reporting/native_pdf_whole_control_effect.py",
        "reporting/native_pdf_whole_controls.py",
        "reporting/native_format_pdf_whole_reference.py",
        "reporting/native_source_external_admission.py",
        "reporting/native_hydration_reconstruction.py",
        "reporting/native_tool_process.py",
    ),
    frozenset({"artifact_id", "declared_formats", "pipeline_run_id", "plan_digest", "requirements_digest"}),
)


@dataclass(frozen=True)
class _Completion:
    """DATA limits derived only after genuine enclosing ToolAPI authentication."""

    original_deadline: float
    observed_completion: float


def _closure(
    source: NativeSourceContext,
    spec: dict[str, Any],
    binding: dict[str, str],
    reader: SnapshotReader,
    *,
    deadline: float,
    role: _ControlRole,
) -> dict[str, Any]:
    """Recheck exact admitted source/executed-code/cache bytes, never pyc imports."""
    from infrastructure.reporting.native_format_acceptance_validation import _file
    from infrastructure.reporting.native_code_runtime import validate_native_code_runtime

    selected = _file(binding, reader)
    raw = selected.json_object()
    sdk = Path(spec["source"]["selected_sdk"]["package_root"])
    mirror = Path(spec["source"]["current_mirror"]["root"])
    project_source = mirror / "projects" / spec["scope"] / "src"
    expected = json.loads(source.bindings.expected_implementation_bytes)["files"]
    code = {
        str(sdk / name.removeprefix("infrastructure/")): digest
        for name, digest in expected.items()
        if name.startswith("infrastructure/") and name.endswith(".py")
    }
    relative_source = f"projects/{spec['scope']}/src/"
    for name, kind, _ in source.source_records if role.project_code else ():
        if kind == "file" and name.startswith(relative_source) and name.endswith(".py"):
            code[str(mirror / name)] = hashlib.sha256(source.current_source_reader.read(name).content).hexdigest()
    if (
        raw.get("schema_version") != "template-native-selected-sdk-execution-closure-v3"
        or raw.get("status") != "pass"
        or raw.get("errors") != []
        or raw.get("original_operation_deadline") != spec["deadline_monotonic"]
        or raw.get("source_roots") != [str(sdk), *([str(project_source)] if role.project_code else [])]
        or raw.get("selected_sdk_package_root") != str(sdk)
        or selected.path != reader.root / spec["directory"] / "closure/receipt.json"
    ):
        raise ValueError("native source control child lacks its exact complete Source/Code closure")
    validate_native_code_runtime(raw.get("runtime"))
    total = count = 0
    seen: set[str] = set()

    def payload(value: dict[str, Any]) -> bytes:
        nonlocal total
        remaining(deadline)
        if set(value) != {"path", "sha256", "bytes"} or Path(value["path"]).name != value["path"]:
            raise ValueError("native source control child Code payload label is unsafe")
        snapshot = reader.read((selected.path.parent / value["path"]).relative_to(reader.root).as_posix())
        total += len(snapshot.content)
        if (
            snapshot.sha256 != value["sha256"]
            or len(snapshot.content) != value["bytes"]
            or total + len(selected.content) > MAX_CACHE_BYTES
        ):
            raise ValueError("native source control child Code payload bytes/bounds differ")
        return snapshot.content

    hook = payload(raw["raw_hook"])
    implementation = payload(raw["implementation_bytes"])
    if (
        hashlib.sha256(hook).hexdigest() != code[str(sdk / "core/bytecode_audit.py")]
        or hashlib.sha256(implementation).hexdigest() != spec["implementation"]["sha256"]
        or raw["implementation_input"]
        != {"path": str(mirror / spec["implementation"]["path"]), "sha256": spec["implementation"]["sha256"]}
        or json.loads(implementation)["files"] != expected
    ):
        raise ValueError("native source control child hook/implementation differs from admitted exact source")
    prefix = Path(raw["prefix"])
    for row in raw["executions"]:
        remaining(deadline)
        if set(row) != {"source_path", "source", "runs"} or row["source_path"] in seen or not row["runs"]:
            raise ValueError("native source control child actual Code execution row differs")
        filename = row["source_path"]
        seen.add(filename)
        held = payload(row["source"])
        if code.get(filename) != hashlib.sha256(held).hexdigest():
            raise ValueError("native source control child executed unadmitted SDK/project source")
        compiled = compile(held, filename, "exec", dont_inherit=True, optimize=sys.flags.optimize)
        for execution in row["runs"]:
            count += 1
            if count > MAX_EXECUTIONS or payload(execution["executed_code"]) != canonical_code(compiled):
                raise ValueError("native source control child executed Code differs from admitted Source")
            if execution["cache"] is not None:
                cached = execution["cache"]
                verify_office_execution_cache(
                    payload(cached["bytes"]),
                    compiled,
                    original_path=cached["original_path"],
                    prefix=prefix,
                    execution_sha256=cached["execution_sha256"],
                    deadline=deadline,
                )
    required = {str(sdk / name) for name in role.required_sdk_modules}
    if not required <= seen or (
        role.project_code and not any(name.startswith(str(project_source) + "/") for name in seen)
    ):
        raise ValueError("native source control child lacks actual selected worker/Source/project executions")
    if total != raw["retained_payload_bytes"] or raw["worker_outcome"] != {
        "kind": "raised",
        "class": "SystemExit",
        "module": "builtins",
        "system_exit_code": spec["expected_exit"],
    }:
        raise ValueError("native source control child Code closure differs from its original OS oracle")
    remaining(deadline)
    return raw


class _SourceControlReaderOperation:
    """Fresh current Source plus genuine enclosing parent; control records are DATA."""

    def __init__(
        self,
        source: NativeSourceContext,
        parent_reader: SnapshotReader,
        records: list[dict[str, Any]],
        *,
        scope: str,
        run_id: str,
        deadline: float,
    ) -> None:
        _role(self)  # Only exact Source-owned concrete types select a role.
        if not isinstance(source, NativeSourceContext) or parent_reader.native_control_operation is not None:
            raise ValueError("native source control reader requires a genuine unwrapped enclosing Source owner")
        self.source, self.parent_reader, self.records = source, parent_reader, records
        self.scope, self.run_id, self.deadline = scope, run_id, deadline
        self.verify(parent_reader)

    def verify(self, reader: SnapshotReader) -> None:
        remaining(self.deadline)
        if reader.root != self.source.bindings.current_root:
            raise ValueError("native source control current reader differs from its actual Source/run")
        producer = self.parent_reader.native_producer_operation
        # Portable current ToolAPI ownership is a different run from the held
        # original. An explicitly nominated external original reader takes
        # precedence; its genuine NativeReaderOperation is verified below.
        if producer is not None and self.parent_reader.native_operation is None:
            if producer.source is not self.source:
                raise ValueError("native source control producer differs from the actual enclosing Source owner")
            producer.verify(self.parent_reader, run_id=self.run_id, deadline=self.deadline)
        else:
            from infrastructure.reporting.native_format_joint_source import require_native_operation

            operation = require_native_operation(self.parent_reader)
            if operation.source is not self.source or not self.deadline <= operation.deadline:
                raise ValueError("native source control reader lacks genuine enclosing original/current Source custody")
            original = operation.originals.get(self.scope)
            if original is None or original.run_id != self.run_id:
                raise ValueError("native source control reader lacks this exact externally held original scope/run")
            operation.verify(self.parent_reader)
        self.source.verify_correspondence(self.source.reference, reader.root, reader, self.deadline)

    def child(self, item: dict[str, Any], reader: SnapshotReader) -> dict[str, Any]:
        """Authenticate actual parent Popen first, then replay its exact child inputs."""
        from infrastructure.reporting.native_format_acceptance_validation import _file
        from infrastructure.reporting.native_tool_replay import (
            _stamp,
            authenticate_original_native_artifact,
            validate_native_tool_data,
        )
        from infrastructure.reporting.native_source_provider_bootstrap import format_selected_sdk_native_bootstrap

        role = _role(self)
        self.verify(reader)
        if set(item) != {
            "name",
            "artifact",
            "process_artifact",
            "specification_artifact",
            "closure_artifact",
            "original_exit_code",
        }:
            raise ValueError("native source control requires the exact complete child record fields")
        process_file = _file(item["process_artifact"], self.parent_reader)
        process = process_file.json_object()
        producer = self.parent_reader.native_producer_operation
        # Portable current ToolAPI ownership is a different run from the held
        # original. An explicitly nominated external original reader takes
        # precedence; its genuine NativeReaderOperation is verified below.
        if producer is not None and self.parent_reader.native_operation is None:
            producer.validate_tool(item["process_artifact"], process, self.parent_reader, run_id=self.run_id)
            source_record = json.loads(self.source.descriptor(self.scope, deadline=self.deadline))
            completion = _Completion(producer.deadline, time.monotonic())
            parent_pid = producer.owner_pid
        else:
            authority = authenticate_original_native_artifact(
                item["process_artifact"],
                self.parent_reader,
                run_id=self.run_id,
                required_sdk_modules=(
                    role.worker.removeprefix("infrastructure.").replace(".", "/") + ".py",
                    "reporting/native_source_provider_bootstrap.py",
                ),
            )
            if authority["event"].json_object() != process:
                raise ValueError("native source control child process differs from externally held actual original")
            source_record = authority["source"]
            completion = authority["original"]
            parent_pid = authority["process"]["pid"]
            validate_native_tool_data(
                process,
                self.parent_reader,
                original_deadline=completion.original_deadline,
                original_completion=completion.observed_completion,
            )
        specification = _file(item["specification_artifact"], reader)
        spec = specification.json_object()
        if (
            set(spec)
            != {
                "schema_version",
                "scope",
                "name",
                "run_id",
                "directory",
                "source",
                "implementation",
                "expected_exit",
                "parent_pid",
                "parent_platform",
                "deadline_monotonic",
                "caller_deadline_monotonic",
                "closure_identity",
            }
            | role.extra_specification_fields
            or spec["schema_version"] != role.schema
            or spec["scope"] != self.scope
            or spec["name"] != item["name"]
            or type(spec["expected_exit"]) is not int
            or spec["expected_exit"] not in {0, 1}
            or type(spec["parent_pid"]) is not int
            or spec["parent_pid"] <= 0
            or spec["run_id"] != self.run_id
            or spec["source"] != source_record
            or spec["parent_pid"] != parent_pid
            or not spec["deadline_monotonic"] <= spec["caller_deadline_monotonic"] <= completion.original_deadline
            or spec["caller_deadline_monotonic"] != completion.original_deadline
            or process.get("owner_pid") != parent_pid
            or process.get("caller_deadline_monotonic") != spec["deadline_monotonic"]
            or item["original_exit_code"] != spec["expected_exit"]
            or type(item["original_exit_code"]) is not int
            or process.get("original_exit_code") != spec["expected_exit"]
            or process.get("exit_code") != spec["expected_exit"]
        ):
            raise ValueError("native source control child Source/role/original-clock custody differs")
        leaf = reader.root / spec["directory"]
        if specification.path != leaf / "specification.json" or process_file.path != leaf / f"{role.purpose}.json":
            raise ValueError("native source control child input/process belongs to another attempt")
        sdk, mirror = Path(source_record["selected_sdk"]["package_root"]), Path(source_record["current_mirror"]["root"])
        implementation = _file(spec["implementation"], reader)
        runtime = json.loads(implementation.content).get("runtime_environment", {})
        # The executable nomination is the admitted VENV launcher; ToolAPI also
        # checks its independently observed resolved physical body and OS identity.
        native = _file(process["native_process_artifact"], reader).json_object()
        nomination = native["nomination"]["path"]
        if native.get("launcher_preserved") is not True or native["nomination"]["resolved_path"] != runtime.get(
            "python_executable"
        ):
            raise ValueError(
                "native source control child actual launcher differs from the admitted selected interpreter"
            )
        hook = self.source.current_source_reader.read("infrastructure/core/bytecode_audit.py").content
        bootstrap = format_selected_sdk_native_bootstrap(
            hook,
            sdk,
            (mirror / "projects" / self.scope / "src",) if role.project_code else (),
            mirror / spec["implementation"]["path"],
            spec["implementation"]["sha256"],
            mirror / spec["directory"] / "closure",
            tuple(spec["closure_identity"]),
            spec["deadline_monotonic"],
            required_worker_module=role.worker,
        )
        command = [
            nomination,
            "-I",
            "-c",
            bootstrap,
            "--root",
            str(mirror),
            "--specification",
            specification.relative,
            "--specification-sha256",
            specification.sha256,
            "--implementation-sha256",
            implementation.sha256,
            "--deadline",
            repr(spec["deadline_monotonic"]),
            "--run-id",
            self.run_id,
        ]
        if (
            process["command"] != command
            or process.get("purpose") != role.purpose
            or implementation.sha256 != spec["implementation"]["sha256"]
        ):
            raise ValueError("native source control child differs from its actual prelaunch selected-SDK command")
        observation = _file(item["artifact"], reader)
        closure = _file(item["closure_artifact"], reader)
        if observation.path != leaf / "control-observation.json":
            raise ValueError("native source control child result belongs to another attempt")
        stdout = _file(
            {"path": process["raw_stdout"]["path"], "sha256": process["raw_stdout"]["sha256"]}, reader
        ).content.decode("utf-8", errors="strict")
        seals = [
            line
            for line in stdout.splitlines()
            if line.startswith((role.observation_seal + " ", role.closure_seal + " "))
        ]
        if seals != [
            f"{role.observation_seal} {specification.sha256} {observation.sha256} "
            f"{self.run_id} {spec['expected_exit']}",
            f"{role.closure_seal} {closure.sha256}",
        ]:
            raise ValueError("native source control child observation/Code lacks original raw-stdout terminal seals")
        audited = _closure(self.source, spec, item["closure_artifact"], reader, deadline=self.deadline, role=role)
        self.verify(reader)
        # The parent event above is genuine. Nested ToolAPI operations belong to
        # this actual child's PID, bounded phase and authenticated OS completion.
        child_completion = _Completion(spec["deadline_monotonic"], _stamp(native.get("operation_end")))
        return {
            "operation": self,
            "original": child_completion,
            "process": native,
            "closure": audited,
            "source": source_record,
            "event": observation,
            "specification": spec,
        }

    def authenticate_artifact(
        self, binding: dict[str, Any], reader: SnapshotReader, *, run_id: str, required_sdk_modules: tuple[str, ...]
    ) -> dict[str, Any]:
        """Admit nested tools only inside one actual parent's sealed child graph."""
        from infrastructure.reporting.native_format_acceptance_validation import _file

        if run_id != self.run_id:
            raise ValueError("native source control nested tool belongs to a different run")
        selected = _file(binding, reader)
        matches = [
            item
            for item in self.records
            if selected.path.is_relative_to(_file(item["specification_artifact"], reader).path.parent)
        ]
        if len(matches) != 1:
            raise ValueError("native source control nested tool needs one genuine original child")
        authority = self.child(matches[0], reader)
        sdk = Path(authority["source"]["selected_sdk"]["package_root"])
        executed = {row["source_path"] for row in authority["closure"]["executions"] if row["runs"]}
        if not {str(sdk / name) for name in required_sdk_modules} <= executed:
            raise ValueError("native source control nested tool lacks actual admitted SDK helper executions")
        pending: list[Any] = [authority["event"].json_object()]
        seen: set[str] = set()
        for _ in range(MAX_EXECUTIONS):
            remaining(self.deadline)
            if not pending:
                break
            value = pending.pop()
            if isinstance(value, dict):
                if set(value) == {"path", "sha256"}:
                    actual = _file(value, reader)
                    if actual.relative == selected.relative:
                        return {**authority, "event": selected}
                    if actual.relative not in seen and actual.path.suffix == ".json":
                        seen.add(actual.relative)
                        pending.append(actual.json_object())
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
        raise ValueError("native source control nested tool is absent from the genuine sealed child observation")


class PrintControlReaderOperation(_SourceControlReaderOperation):
    """The exact configured-print role requires selected SDK and project Code."""

    schema = CHILD_SCHEMA


class SlideControlReaderOperation(_SourceControlReaderOperation):
    """The exact slide-control role audits only admitted selected SDK Code."""

    schema = SLIDE_CHILD_SCHEMA


class BasicBrowserControlReaderOperation(_SourceControlReaderOperation):
    """The exact basic browser role audits admitted selected SDK Code."""

    schema = BROWSER_CHILD_SCHEMA


class SemanticBrowserControlReaderOperation(_SourceControlReaderOperation):
    """The exact semantic browser role audits admitted selected SDK Code."""

    schema = SEMANTIC_BROWSER_CHILD_SCHEMA


class OfficeScientificControlReaderOperation(_SourceControlReaderOperation):
    """Exact scientific Office child; basic and diagram originals stay distinct."""

    schema = OFFICE_SCIENTIFIC_CHILD_SCHEMA


class WholePDFControlReaderOperation(_SourceControlReaderOperation):
    """Exact Source-owned complete PDF page/occurrence control child."""

    schema = WHOLE_PDF_CHILD_SCHEMA


def _role(operation: _SourceControlReaderOperation) -> _ControlRole:
    """Choose only by exact Source-owned type; retained DATA never chooses role."""
    if type(operation) is PrintControlReaderOperation:
        return _PRINT_ROLE
    if type(operation) is SlideControlReaderOperation:
        return _SLIDE_ROLE
    if type(operation) is BasicBrowserControlReaderOperation:
        return _BROWSER_ROLE
    if type(operation) is SemanticBrowserControlReaderOperation:
        return _SEMANTIC_BROWSER_ROLE
    if type(operation) is OfficeScientificControlReaderOperation:
        return _OFFICE_SCIENTIFIC_ROLE
    if type(operation) is WholePDFControlReaderOperation:
        return _WHOLE_PDF_ROLE
    from infrastructure.reporting.native_pitch_control_custody import PITCH_ROLE, PitchControlReaderOperation

    if type(operation) is PitchControlReaderOperation:
        return PITCH_ROLE
    raise ValueError("native source control requires one exact Source-owned concrete reader type")
