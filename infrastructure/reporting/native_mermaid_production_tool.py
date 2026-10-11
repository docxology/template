"""Retain actual Mermaid production launches inside the existing fixed stage.

The packet binds caller data, consumed bytes and independently supervised tool
outcomes. Source occurrence membership, output-write causality, descendant
loaded code and native ink remain separate obligations.
"""

from __future__ import annotations

import inspect
import os
import secrets
import sys
import time
import types
from pathlib import Path
from typing import TYPE_CHECKING, Any

from infrastructure.rendering.native_render_custody import NATIVE_ORIGIN_KEYS
from infrastructure.rendering.security import IsolatedCompletedProcess

if TYPE_CHECKING:
    from infrastructure.reporting.native_source_external_admission import NativeSourceContext
    from infrastructure.reporting.native_stage_child_custody import NativeStageChildReaderOperation
    from infrastructure.reporting.native_tool_producer import NativeProducerOperation
    from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader

SCHEMA = "template-source-native-mermaid-production-command-v1"
FIELDS = frozenset(
    {
        "schema_version",
        "scope",
        "run_id",
        "source_binding",
        "owner_pid",
        "role",
        "command",
        "selected_command",
        "cwd",
        "source_implementation_inputs",
        "raw_source",
        "normalized_source",
        "consumed_inputs",
        "output_label",
        "output_before",
        "output",
        "tool_artifacts",
        "remaining_admission",
    }
)
CALLERS = {
    "inline": ("infrastructure/rendering/_pdf_mermaid.py", "_render_mermaid"),
    "standalone": ("infrastructure/rendering/mermaid_figure.py", "render_mermaid_png"),
}
REMAINING_ADMISSION = (
    "complete independently reconstructed Source occurrence/caller-value membership",
    "actual native child output-write causality beyond held before/after bodies",
    "complete Node/browser descendant consuming-library/shared-cache/kernel custody",
    "independent complete native Mermaid placement, glyph and ink acceptance",
)


def _binding(snapshot: ArtifactSnapshot) -> dict[str, str]:
    return {"path": snapshot.relative, "sha256": snapshot.sha256}


def _verify_caller(owner: NativeProducerOperation, role: str) -> str:
    """Check the actual selected SDK caller; a role string grants no authority."""
    from infrastructure.core.bytecode_audit import canonical_code

    relative, name = CALLERS[role]
    authored = owner.source.current_source_reader.read(relative)
    if authored.content != owner.source.reference.read(relative):
        raise ValueError("Mermaid production caller differs from independently held Source")
    filename = owner.source.bindings.selected_sdk_package_root / relative.removeprefix("infrastructure/")
    compiled = compile(authored.content, str(filename), "exec", dont_inherit=True, optimize=sys.flags.optimize)
    declarations = [
        value for value in compiled.co_consts if isinstance(value, types.CodeType) and value.co_name == name
    ]
    frame = inspect.currentframe()
    caller = frame.f_back.f_back if frame is not None and frame.f_back is not None else None
    if (
        caller is None
        or len(declarations) != 1
        or caller.f_code.co_filename != str(filename)
        or canonical_code(caller.f_code) != canonical_code(declarations[0])
    ):
        raise ValueError("Mermaid production launch requires its actual fixed selected SDK caller")
    return relative


def _normalized(raw: bytes, role: str) -> bytes:
    if role == "inline":
        from infrastructure.rendering._pdf_mermaid import _normalise_mermaid_source

        return (_normalise_mermaid_source(raw.decode("utf-8").strip()) + "\n").encode("utf-8")
    return raw + b"\n"


def run_source_native_mermaid(
    command: list[str],
    source_path: Path,
    output_path: Path,
    *,
    role: str,
    raw_source: str,
    input_paths: tuple[Path, ...],
    environment: dict[str, str],
    timeout: int,
) -> IsolatedCompletedProcess | None:
    """Use the already admitted stage owner; return None for ordinary callers.

    Looking up an already loaded module avoids importing native/provider
    namespaces before an external Source admission. Only its genuine current
    owner and the independently checked fixed stage authorize the launch.
    """
    loaded = sys.modules.get("infrastructure.reporting.native_tool_producer")
    if loaded is None:
        if any(os.environ.get(key) for key in NATIVE_ORIGIN_KEYS):
            raise ValueError("native-origin Mermaid production lacks its independently admitted Source owner")
        return None
    from infrastructure.reporting.native_tool_producer import NativeProducerOperation, current_native_producer_operation

    owner = current_native_producer_operation()
    if owner is None:
        if any(os.environ.get(key) for key in NATIVE_ORIGIN_KEYS):
            raise ValueError("native-origin Mermaid production lacks its genuine live Source owner")
        return None
    if type(owner) is not NativeProducerOperation:
        raise ValueError("Mermaid production needs the actual fixed Source producer type")
    try:
        from infrastructure.project.public_acceptance_evidence import write_json
        from infrastructure.project.public_reference_git import remaining
        from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
        from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime
        from infrastructure.reporting.native_stage_child import (
            current_native_stage_directory,
            retain_native_stage_artifact,
        )
        from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

        if role not in CALLERS or type(timeout) is not int or timeout <= 0 or not isinstance(raw_source, str):
            raise ValueError("Mermaid production role/timeout/caller source is absent")
        stage_directory = current_native_stage_directory(require_render=True)
        if stage_directory is None:
            raise ValueError("native Mermaid production requires its actual fixed Source-admitted stage child")
        root = owner.source.bindings.current_root
        reader = SnapshotReader(root, native_producer_operation=owner)
        owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
        caller = _verify_caller(owner, role)
        source_path, output_path, cwd = source_path.absolute(), output_path.absolute(), Path.cwd().absolute()
        matches = [
            scope for scope in PUBLIC_PROJECT_NAMES if output_path.is_relative_to(root / "projects" / scope / "output")
        ]
        if (
            len(matches) != 1
            or cwd not in {root, root / "projects" / matches[0]}
            or source_path.suffix != ".mmd"
            or output_path.suffix != ".png"
            or source_path.parent != output_path.parent
            or not command
            or any(not isinstance(value, str) or "\0" in value for value in command)
        ):
            raise ValueError("Mermaid production inputs/output/CWD differ from a real selected Source project role")
        scope = matches[0]
        phase_deadline = min(owner.deadline, time.monotonic() + min(timeout, 120))
        remaining(phase_deadline)
        paths = tuple(dict.fromkeys((source_path, *(path.absolute() for path in input_paths))))
        for path in paths:
            if path != path.resolve(strict=True) or not path.is_relative_to(root) or not path.is_file():
                raise ValueError("Mermaid production consumed input is not an actual confined regular file")
        normalized = reader.read(source_path.relative_to(root).as_posix())
        raw = raw_source.encode("utf-8")
        if len(raw) > 1024 * 1024 or len(paths) > 8:
            raise ValueError("Mermaid production caller/input cohort exceeds its finite Source profile")
        if normalized.content != _normalized(raw, role):
            raise ValueError("Mermaid production normalized bytes differ from the actual fixed Source transform")
        runtime = CitationRuntime(
            root,
            stage_directory / ("mermaid-" + secrets.token_hex(12)),
            env=environment,
            deadline=owner.deadline,
            run_id=owner.run_id,
        )
        raw_path = runtime.freeze("caller-raw-source.input", raw)
        # The before-body is a separate observation: an expected native output
        # replacement must not invalidate the consumed-input reader's snapshots.
        before = SnapshotReader(root).read(output_path.relative_to(root).as_posix()) if output_path.is_file() else None
        before_binding = (
            None
            if before is None
            else _binding(
                reader.read(runtime.freeze("output-before.input", before.content).relative_to(root).as_posix())
            )
        )
        try:
            tool = runtime.tool(
                command[0],
                command[1:],
                "source-mermaid-production",
                input_paths=paths,
                cwd=cwd,
                phase_deadline=phase_deadline,
            )
        except TimeoutError as error:
            # Direct incomplete-result DATA, never live accepted ToolAPI authority.
            attempt: dict[str, Any] = {
                "artifact": None,
                "native_tools": list(runtime.tools),
                "original_exit_code": None,
                "timed_out": None,
                "output": None,
                "completion_authorized": False,
                "retention_diagnostic": f"{type(error).__name__}: {error}",
            }
            if len(runtime.tools) == 1:
                try:
                    observed = reader.read(runtime.tools[0]["path"])
                    if observed.sha256 == runtime.tools[0]["sha256"]:
                        raw_tool = observed.json_object()
                        attempt["original_exit_code"] = raw_tool.get("original_exit_code")
                        attempt["timed_out"] = raw_tool.get("timed_out")
                except (OSError, ValueError) as retention:
                    attempt["retention_diagnostic"] += f"; {type(retention).__name__}: {retention}"
            setattr(error, "native_mermaid_attempt", attempt)
            raise
        except ValueError:
            # A fully retained genuine signed nonzero child may retain the ordinary
            # caller's existing fallback. Custody/clock/zero-result failures refuse.
            if len(runtime.tools) != 1:
                raise
            tool = reader.read(runtime.tools[0]["path"]).json_object()
            owner.validate_tool(runtime.tools[0], tool, reader, run_id=owner.run_id)
            if (
                type(tool.get("original_exit_code")) is not int
                or tool["original_exit_code"] == 0
                or tool.get("exit_code") != tool["original_exit_code"]
                or tool.get("timed_out") is not False
                or tool.get("custody_refused") is not False
                or tool.get("diagnostic")
            ):
                raise
        owner.validate_tool(runtime.tools[-1], tool, reader, run_id=owner.run_id)
        selected: dict[str, str] | None = None
        output_binding: dict[str, str] | None = None
        try:
            consumed = tool["consumed_input_artifacts"]
            source_rows = [row for row in consumed if row["observation"]["path"] == str(source_path)]
            if len(source_rows) != 1 or source_rows[0]["observation"]["sha256"] != normalized.sha256:
                raise ValueError("Mermaid production omitted its actual consumed normalized source body")
            output = reader.read(output_path.relative_to(root).as_posix()) if output_path.is_file() else None
            output_binding = (
                None
                if output is None
                else _binding(
                    reader.read(runtime.freeze("output-after.input", output.content).relative_to(root).as_posix())
                )
            )
            implementation = []
            for relative in (caller, "infrastructure/reporting/native_mermaid_production_tool.py"):
                item = reader.read(relative)
                if item.content != owner.source.reference.read(relative):
                    raise ValueError("Mermaid production actual Source helper changed before retention")
                implementation.append(_binding(item))
            value = {
                "schema_version": SCHEMA,
                "scope": scope,
                "run_id": owner.run_id,
                "source_binding": [owner.source.reference.commit, owner.source.reference.source_identity],
                "owner_pid": owner.owner_pid,
                "role": role,
                "command": tool["command"],
                "selected_command": list(command),
                "cwd": str(cwd),
                "source_implementation_inputs": implementation,
                "raw_source": _binding(reader.read(raw_path.relative_to(root).as_posix())),
                "normalized_source": source_rows[0]["artifact"],
                "consumed_inputs": consumed,
                "output_label": str(output_path),
                "output_before": before_binding,
                "output": output_binding,
                "tool_artifacts": list(runtime.tools),
                "remaining_admission": list(REMAINING_ADMISSION),
            }
            selected = write_json(root, runtime.directory / "mermaid-production.json", value)
            retain_native_stage_artifact(reader.read(selected["path"]), tool_artifacts=runtime.tools)
            runtime.unchanged()
            owner.verify(reader, run_id=owner.run_id, deadline=owner.deadline)
            remaining(phase_deadline)
        except BaseException as error:
            attempt = {
                "artifact": selected,
                "native_tools": list(runtime.tools),
                "original_exit_code": tool["original_exit_code"],
                "output": output_binding,
                "retention_diagnostic": f"{type(error).__name__}: {error}",
            }
            if tool["original_exit_code"] in {130, -2, 124}:
                terminal: BaseException = SystemExit(124) if tool["original_exit_code"] == 124 else KeyboardInterrupt()
                setattr(terminal, "native_mermaid_attempt", attempt)
                raise terminal from error
            setattr(error, "native_mermaid_attempt", attempt)
            raise
        completed = IsolatedCompletedProcess(
            args=tool["command"], returncode=tool["original_exit_code"], stdout=tool["stdout"], stderr=tool["stderr"]
        )
        completed.pid = tool["pid"]
        if tool["original_exit_code"] in {130, -2, 124}:
            # Preserve the native OS fact unchanged. The enclosing stage's terminal
            # interruption/exit is a separate Source intent, never a minted timeout.
            failure: BaseException = SystemExit(124) if tool["original_exit_code"] == 124 else KeyboardInterrupt()
            setattr(
                failure,
                "native_mermaid_attempt",
                {
                    "artifact": selected,
                    "native_tools": list(runtime.tools),
                    "original_exit_code": tool["original_exit_code"],
                    "output": output_binding,
                },
            )
            raise failure
        return completed
    except TimeoutError as error:
        # A real native phase/retention timeout is terminal Source intent124;
        # its actual child OS fact and timed_out flag remain untouched DATA.
        terminal = SystemExit(124)
        setattr(
            terminal,
            "native_mermaid_attempt",
            getattr(
                error,
                "native_mermaid_attempt",
                {
                    "artifact": None,
                    "native_tools": [],
                    "original_exit_code": None,
                    "timed_out": None,
                    "output": None,
                    "completion_authorized": False,
                    "retention_diagnostic": f"{type(error).__name__}: {error}",
                },
            ),
        )
        raise terminal from error
    except OSError as error:
        # Native Source custody/persistence refusal must not enter the ordinary
        # rendering caller's OSError-to-fallback path.
        refusal = RuntimeError(f"native Mermaid custody/persistence refused: {error}")
        if hasattr(error, "native_mermaid_attempt"):
            setattr(refusal, "native_mermaid_attempt", getattr(error, "native_mermaid_attempt"))
        raise refusal from error


def validate_source_native_mermaid_stage_artifact(
    source: NativeSourceContext,
    value: dict[str, Any],
    reader: SnapshotReader,
    *,
    scope: str,
    run_id: str,
    owner_pid: int,
    original_root_label: Path | None = None,
) -> None:
    """Validate finite packet DATA; actual stage/tool custody is checked separately."""
    from infrastructure.reporting.native_format_acceptance_validation import _file

    root = reader.root if original_root_label is None else original_root_label
    if (
        set(value) != FIELDS
        or value["schema_version"] != SCHEMA
        or value["scope"] != scope
        or value["run_id"] != run_id
        or value["owner_pid"] != owner_pid
        or value["role"] not in CALLERS
        or value["source_binding"] != [source.reference.commit, source.reference.source_identity]
        or value["remaining_admission"] != list(REMAINING_ADMISSION)
        or value["cwd"] not in {str(root), str(root / "projects" / scope)}
        or not isinstance(value["tool_artifacts"], list)
        or len(value["tool_artifacts"]) != 1
        or not isinstance(value["command"], list)
        or not value["command"]
        or any(not isinstance(item, str) or "\0" in item for item in value["command"])
        or not isinstance(value["selected_command"], list)
        or not value["selected_command"]
        or any(not isinstance(item, str) or "\0" in item for item in value["selected_command"])
        or not isinstance(value["output_label"], str)
    ):
        raise ValueError("Mermaid production packet differs from its exact Source/stage/caller/tool role")
    output = Path(value["output_label"])
    if (
        not output.is_absolute()
        or ".." in output.parts
        or not output.is_relative_to(root / "projects" / scope / "output")
        or output.suffix != ".png"
    ):
        raise ValueError("Mermaid production output label escaped the actual Source project role")
    expected_implementations = (CALLERS[value["role"]][0], "infrastructure/reporting/native_mermaid_production_tool.py")
    if not isinstance(value["source_implementation_inputs"], list) or len(value["source_implementation_inputs"]) != 2:
        raise ValueError("Mermaid production lacks both actual Source caller/helper bodies")
    for selected, relative in zip(value["source_implementation_inputs"], expected_implementations, strict=True):
        item = _file(selected, reader)
        if item.relative != relative or item.content != source.reference.read(relative):
            raise ValueError("Mermaid production caller/helper differs from independently held Source")
    raw, normalized = (_file(value[key], reader) for key in ("raw_source", "normalized_source"))
    if len(raw.content) > 1024 * 1024:
        raise ValueError("Mermaid production raw caller bytes exceed the finite Source profile")
    if normalized.content != _normalized(raw.content, value["role"]):
        raise ValueError("Mermaid production retained raw/normalized bytes differ from fixed Source transform")
    tool = _file(value["tool_artifacts"][0], reader).json_object()
    if (
        tool.get("run_id") != run_id
        or tool.get("owner_pid") != owner_pid
        or tool.get("purpose") != "source-mermaid-production"
        or tool.get("command") != value["command"]
        or tool.get("cwd") != value["cwd"]
        or tool.get("tool") != value["selected_command"][0]
        or tool["command"][1:] != value["selected_command"][1:]
        or type(tool.get("original_exit_code")) is not int
        or tool.get("exit_code") != tool["original_exit_code"]
        or tool.get("custody_refused") is not False
        or tool.get("timed_out") is not False
        or tool.get("diagnostic")
        or value["consumed_inputs"] != tool.get("consumed_input_artifacts")
    ):
        raise ValueError("Mermaid production DATA differs from its independently authenticated signed ToolAPI")
    consumed = value["consumed_inputs"]
    if not isinstance(consumed, list) or not 0 < len(consumed) <= 8:
        raise ValueError("Mermaid production actual consumed input cohort is absent")
    normalized_matches = 0
    for row in consumed:
        item = _file(row["artifact"], reader)
        observation = row["observation"]
        label = Path(observation["path"])
        if (
            not label.is_absolute()
            or ".." in label.parts
            or not label.is_relative_to(root)
            or item.sha256 != observation["sha256"]
            or len(item.content) != observation["bytes"]
        ):
            raise ValueError("Mermaid production frozen input differs from the actual consumed byte observation")
        if row["artifact"] == value["normalized_source"]:
            normalized_matches += 1
            if label.parent != output.parent or label.suffix != ".mmd":
                raise ValueError("Mermaid normalized source differs from its real sibling output role")
    if normalized_matches != 1:
        raise ValueError("Mermaid production normalized source is missing/repeated in actual consumed inputs")
    for key in ("output_before", "output"):
        if value[key] is not None:
            _file(value[key], reader)


def replay_source_native_mermaid_command(
    selected: dict[str, str],
    reader: SnapshotReader,
    stage: NativeStageChildReaderOperation,
) -> dict[str, Any]:
    """Consume one actual Original/Current stage packet without executing Core."""
    from infrastructure.reporting.native_tool_replay import validate_original_native_tool

    stage.verify(reader)
    authority = stage.authenticate_artifact(
        selected,
        reader,
        run_id=stage.run_id,
        required_sdk_modules=(
            "reporting/native_mermaid_production_tool.py",
            "reporting/native_pdf_citation_runtime.py",
        ),
    )
    value = authority["event"].json_object()
    if not isinstance(value, dict):
        raise ValueError("Mermaid production actual held event must be a JSON object")
    validate_source_native_mermaid_stage_artifact(
        stage.source,
        value,
        reader,
        scope=stage.scope,
        run_id=stage.run_id,
        owner_pid=authority["process"]["pid"],
        original_root_label=Path(authority["source"]["current_mirror"]["root"]),
    )
    caller_module = CALLERS[value["role"]][0].removeprefix("infrastructure/")
    # Check actual executed caller membership, then the real retained process;
    # no pass/status/packet field constructs the externally held owner.
    stage.authenticate_artifact(selected, reader, run_id=stage.run_id, required_sdk_modules=(caller_module,))
    for tool_binding in value["tool_artifacts"]:
        tool = reader.read(tool_binding["path"]).json_object()
        validate_original_native_tool(
            tool_binding,
            tool,
            reader,
            run_id=stage.run_id,
            required_sdk_modules=(caller_module, "reporting/native_mermaid_production_tool.py"),
        )
    if not reader.unchanged():
        raise ValueError("Mermaid production actual held tool/input/output bodies changed during readback")
    stage.verify(reader)
    return value
