"""Distinct original Office control custody; full native-worker 0/75 is unchanged.

Only the actual parent launcher creates completed originals after a registered
real supervised invocation. Portable readers nominate these live capabilities
and their own genuine Source; transported observations never create authority.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from infrastructure.core.bytecode_audit import (
    MAX_CACHE_BYTES,
    MAX_EXECUTIONS,
    canonical_code,
)
from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_office_cache_structure import verify_office_execution_cache
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)
from infrastructure.reporting.release_readiness_snapshot import (
    ArtifactSnapshot,
    SnapshotReader,
)

SCHEMA = "template-source-owned-original-office-control-v1"
WORKER = "infrastructure.reporting.native_office_diagram_control_worker"
_LIVE_ORIGINAL = object()


@dataclass(frozen=True)
class NativeOfficeControlOriginal:
    """Parent-held genuine completion, never reconstructed from retained JSON."""

    run_id: str
    scope: str
    kind: str
    control: str
    expected_exit: int
    original_deadline: float
    observed_completion: float
    specification_relative: str
    specification_bytes: bytes
    process_relative: str
    process_bytes: bytes
    closure_relative: str
    observation_relative: str
    command: tuple[str, ...]
    source_commit: str
    source_identity: str
    sdk_root: Path
    expected_code: MappingProxyType[str, str]
    artifact_hashes: MappingProxyType[str, str]
    live_key: object

    def _read(self, relative: str, reader: SnapshotReader) -> ArtifactSnapshot:
        value = reader.read(relative)
        if self.live_key is not _LIVE_ORIGINAL or self.artifact_hashes.get(relative) != value.sha256:
            raise ValueError("Office artifact is absent from actual parent-held original completion")
        return value

    def graph_contains(self, selected: ArtifactSnapshot, reader: SnapshotReader, *, deadline: float) -> None:
        """Bind artifact membership to the original raw-stdout sealed observation."""
        pending: list[Any] = [self._read(self.observation_relative, reader).json_object()]
        seen: set[str] = set()
        count = 0
        while pending:
            remaining(deadline)
            count += 1
            if count > MAX_EXECUTIONS:
                raise ValueError("Office original observation graph exceeds its existing finite bound")
            value = pending.pop()
            if isinstance(value, dict):
                path, digest = value.get("path"), value.get("sha256")
                if isinstance(path, str) and isinstance(digest, str) and path in self.artifact_hashes:
                    actual = self._read(path, reader)
                    if actual.sha256 != digest:
                        raise ValueError("Office original sealed observation graph payload changed")
                    if actual.relative == selected.relative:
                        return
                    if path.endswith(".json") and path not in seen:
                        seen.add(path)
                        pending.append(actual.json_object())
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
        if selected.relative != self.observation_relative:
            raise ValueError("Office artifact is absent from original sealed observation membership")

    def closure(self, reader: SnapshotReader, *, deadline: float) -> dict[str, Any]:
        """Validate actual original Code against independently held admitted bytes."""
        remaining(deadline)
        selected = self._read(self.closure_relative, reader)
        raw = selected.json_object()
        if (
            raw.get("schema_version") != "template-native-selected-sdk-execution-closure-v3"
            or raw.get("status") != "pass"
            or raw.get("errors") != []
            or raw.get("original_operation_deadline") != self.original_deadline
        ):
            raise ValueError("Office original selected SDK Code closure is incomplete")
        from infrastructure.reporting.native_code_runtime import validate_native_code_runtime

        validate_native_code_runtime(raw.get("runtime"))
        specification = json.loads(self.specification_bytes)
        provider_site = Path(specification["dependencies"]["pdfium_site"])
        if raw.get("source_roots") != [
            str(self.sdk_root),
            str(provider_site / "pypdfium2"),
            str(provider_site / "pypdfium2_raw"),
        ]:
            raise ValueError(
                "Office original retained Code audit roots differ from prelaunch Source/provider nomination"
            )
        prefix = Path(raw["prefix"])
        total = count = 0
        seen = set()

        def payload(binding: dict[str, Any]) -> bytes:
            nonlocal total
            if set(binding) != {"path", "sha256", "bytes"} or Path(binding["path"]).name != binding["path"]:
                raise ValueError("Office original retained Code payload label is unsafe")
            relative = (Path(self.closure_relative).parent / binding["path"]).as_posix()
            value = self._read(relative, reader)
            total += len(value.content)
            if (
                value.sha256 != binding["sha256"]
                or len(value.content) != binding["bytes"]
                or total + len(selected.content) > MAX_CACHE_BYTES
            ):
                raise ValueError("Office original Code payload bytes/bounds differ")
            return value.content

        hook = payload(raw["raw_hook"])
        if hashlib.sha256(hook).hexdigest() != self.expected_code[str(self.sdk_root / "core/bytecode_audit.py")]:
            raise ValueError("Office original raw preimport hook differs from admitted SDK")
        implementation = payload(raw["implementation_bytes"])
        if hashlib.sha256(implementation).hexdigest() != raw["implementation_input"]["sha256"]:
            raise ValueError("Office original implementation input differs from actual bootstrap")
        specification = json.loads(self.specification_bytes)
        if raw["implementation_input"]["sha256"] != specification["implementation"]["sha256"]:
            raise ValueError("Office original implementation differs from parent's prelaunch binding")
        if raw.get("selected_sdk_package_root") != str(self.sdk_root):
            raise ValueError("Office original loaded a different selected SDK")
        for row in raw["executions"]:
            remaining(deadline)
            if set(row) != {"source_path", "source", "runs"} or row["source_path"] in seen or not row["runs"]:
                raise ValueError("Office original actual Code execution row differs")
            filename = row["source_path"]
            seen.add(filename)
            source = payload(row["source"])
            if self.expected_code.get(filename) != hashlib.sha256(source).hexdigest():
                raise ValueError("Office original executed an unadmitted SDK/provider source")
            compiled = compile(
                source,
                filename,
                "exec",
                dont_inherit=True,
                optimize=sys.flags.optimize,
            )
            expected = canonical_code(compiled)
            for run in row["runs"]:
                count += 1
                if count > MAX_EXECUTIONS or payload(run["executed_code"]) != expected:
                    raise ValueError("Office original actual executed Code differs from admitted Source")
                if run["cache"] is not None:
                    cache = run["cache"]
                    retained_cache = payload(cache["bytes"])
                    verify_office_execution_cache(
                        retained_cache,
                        compiled,
                        original_path=cache["original_path"],
                        prefix=prefix,
                        execution_sha256=cache["execution_sha256"],
                        deadline=deadline,
                    )
        if (
            str(self.sdk_root / "reporting/native_office_diagram_control_worker.py") not in seen
            or total != raw["retained_payload_bytes"]
        ):
            raise ValueError("Office original control lacks actual worker execution/complete Code bytes")
        expected_outcome = {
            "kind": "raised",
            "class": "SystemExit",
            "module": "builtins",
            "system_exit_code": self.expected_exit,
        }
        if raw["worker_outcome"] != expected_outcome:
            raise ValueError("Office original Code outcome differs from independently observed original OS exit")
        remaining(deadline)
        return raw


class OfficeControlReaderOperation:
    """Independent current Source plus genuine externally supplied originals."""

    def __init__(
        self,
        source: NativeSourceContext,
        originals: tuple[NativeOfficeControlOriginal, ...],
        *,
        deadline: float,
    ) -> None:
        if (
            not isinstance(source, NativeSourceContext)
            or not originals
            or any(value.live_key is not _LIVE_ORIGINAL for value in originals)
        ):
            raise ValueError("Office control reader requires live original parent custody and current Source")
        self.source = source
        self.originals = originals
        self.deadline = deadline
        self.verify(SnapshotReader(source.bindings.current_root))

    def verify(self, reader: SnapshotReader) -> None:
        remaining(self.deadline)
        self.source.verify_correspondence(
            self.source.reference,
            self.source.bindings.current_root,
            reader,
            self.deadline,
        )
        if any(
            value.source_commit != self.source.reference.commit
            or value.source_identity != self.source.reference.source_identity
            for value in self.originals
        ):
            raise ValueError("Office control originals differ from independently admitted exact current Source")
        remaining(self.deadline)

    def authenticate_artifact(
        self,
        binding: dict[str, Any],
        reader: SnapshotReader,
        *,
        run_id: str,
        required_sdk_modules: tuple[str, ...],
    ) -> dict[str, Any]:
        """Authenticate original artifact membership through actual parent custody."""
        self.verify(reader)
        matches = [
            value
            for value in self.originals
            if value.run_id == run_id and value.artifact_hashes.get(binding["path"]) == binding["sha256"]
        ]
        if len(matches) != 1:
            raise ValueError("Office original artifact needs one exact external original child")
        original = matches[0]
        event = original._read(binding["path"], reader)
        original.graph_contains(event, reader, deadline=self.deadline)
        specification = original._read(original.specification_relative, reader)
        process = original._read(original.process_relative, reader)
        if specification.content != original.specification_bytes or process.content != original.process_bytes:
            raise ValueError("Office original spec/process differs from parent's genuine prelaunch/completion bytes")
        raw = process.json_object()
        native = reader.read(raw["native_process_artifact"]["path"]).json_object()
        if (
            tuple(raw["command"]) != original.command
            or raw["original_exit_code"] != original.expected_exit
            or native["original_exit_code"] != original.expected_exit
        ):
            raise ValueError("Office original invocation/original OS exit differs from live parent custody")
        from infrastructure.reporting.native_tool_replay import (
            validate_native_tool_data,
        )

        validate_native_tool_data(
            raw,
            reader,
            original_deadline=original.original_deadline,
            original_completion=original.observed_completion,
        )
        closure = original.closure(reader, deadline=self.deadline)
        executed = {row["source_path"] for row in closure["executions"] if row["runs"]}
        if not {str(original.sdk_root / name) for name in required_sdk_modules} <= executed:
            raise ValueError("Office original lacks required actual admitted SDK helper executions")
        self.verify(reader)
        return {
            "operation": self,
            "original": original,
            "process": native,
            "closure": closure,
            "source": {"selected_sdk": {"package_root": str(original.sdk_root)}},
            "event": event,
        }

    def admit_original_child(self, raw: dict[str, Any], control: str, original_pdf_sha256: str, code: int) -> None:
        matches = [
            value
            for value in self.originals
            if value.control == control and value.expected_exit == code and json.loads(value.process_bytes) == raw
        ]
        if len(matches) != 1:
            raise ValueError("Office portable control lacks its exact genuine original child")
        original = matches[0]
        reader = SnapshotReader(self.source.bindings.current_root, native_control_operation=self)
        self.authenticate_artifact(
            {
                "path": original.observation_relative,
                "sha256": original.artifact_hashes[original.observation_relative],
            },
            reader,
            run_id=original.run_id,
            required_sdk_modules=(
                "reporting/native_office_diagram_controls.py",
                "reporting/native_office_diagram_positive.py",
            ),
        )
        observation = original._read(original.observation_relative, reader).json_object()
        if observation["original_pdf_sha256"] != original_pdf_sha256 or observation["oracle_exit_code"] != code:
            raise ValueError("Office actual original control Source-only PDF/oracle differs")
        self.verify(reader)

    def admit_original_mermaid_process(self, record: dict[str, Any]) -> None:
        """Authenticate Node DATA through genuine outer control and actual Code."""
        reader = SnapshotReader(self.source.bindings.current_root, native_control_operation=self)
        candidates = []
        for original in self.originals:
            specification = json.loads(original.specification_bytes)
            root_label = Path(specification["source"]["current_mirror"]["root"])
            path_label = (
                root_label / specification["directory"] / "source-mermaid-runtime" / "source-mermaid-node-version.json"
                if record.get("purpose") == "source-mermaid-node-version"
                else Path(record["cwd"]) / f"{record['purpose']}.json"
            )
            if path_label.is_relative_to(root_label):
                relative = path_label.relative_to(root_label).as_posix()
                digest = original.artifact_hashes.get(relative)
                if digest is not None:
                    candidates.append((original, {"path": relative, "sha256": digest}))
        if len(candidates) != 1:
            raise ValueError("Mermaid process is absent from one genuine original Office control")
        nominated, binding = candidates[0]
        admitted = self.authenticate_artifact(
            binding,
            reader,
            run_id=nominated.run_id,
            required_sdk_modules=(
                "reporting/native_mermaid_runtime_selection.py"
                if record.get("purpose") == "source-mermaid-node-version"
                else "reporting/native_pdf_citation_runtime.py",
                "reporting/native_tool_process.py",
            ),
        )
        if admitted["event"].json_object() != record or record.get("owner_pid") != admitted["process"]["pid"]:
            raise ValueError("Mermaid Node DATA differs from actual original child/PID ownership")
        from infrastructure.reporting.native_tool_replay import (
            validate_native_tool_data,
        )

        original = admitted["original"]
        validate_native_tool_data(
            record,
            reader,
            original_deadline=original.original_deadline,
            original_completion=original.observed_completion,
        )
        self.verify(reader)


def _capture_original(
    source: NativeSourceContext,
    directory: Path,
    specification: dict[str, Any],
    command: tuple[str, ...],
    process_binding: dict[str, Any],
    *,
    expected_code: dict[str, str],
    deadline: float,
) -> NativeOfficeControlOriginal:
    """Internal actual launcher completion only; never an exported DATA decoder."""
    from infrastructure.reporting.native_tool_producer import (
        current_native_producer_operation,
    )

    producer = current_native_producer_operation()
    if producer is None or producer.source is not source:
        raise ValueError("Office parent completion needs its actual live original Source/tool owner")
    reader = SnapshotReader(source.bindings.current_root, native_producer_operation=producer)
    process = reader.read(process_binding["path"])
    producer.validate_tool(process_binding, process.json_object(), reader, run_id=source.bindings.run_id)
    raw = process.json_object()
    if raw["original_exit_code"] != specification["expected_exit"] or tuple(raw["command"]) != command:
        raise ValueError("Office actual original control failed its declared original OS oracle")
    hashes = {}
    total = 0
    pending = [directory]
    while pending:
        parent = pending.pop()
        for child in sorted(parent.iterdir()):
            remaining(deadline)
            if child.is_symlink():
                raise ValueError("Office actual original completion has an unadmitted artifact alias")
            if child.is_dir():
                pending.append(child)
            elif child.is_file():
                value = reader.read(child.relative_to(reader.root).as_posix())
                hashes[value.relative] = value.sha256
                total += len(value.content)
                if len(hashes) > 20_000 or total > 1024 * 1024 * 1024:
                    raise ValueError("Office original artifact closure exceeds its existing finite bounds")
            else:
                raise ValueError("Office actual original completion has an unsupported artifact type")
    spec = reader.read((directory / "specification.json").relative_to(reader.root).as_posix())
    if spec.json_object() != specification:
        raise ValueError("Office original prelaunch Source/control specification changed")
    observation = reader.read((directory / "observation.json").relative_to(reader.root).as_posix())
    closure = reader.read((directory / "closure/receipt.json").relative_to(reader.root).as_posix())
    spec_sha = hashlib.sha256(spec.content).hexdigest()
    stdout = reader.read(raw["raw_stdout"]["path"]).content.decode("utf-8", errors="strict")
    wanted = [
        f"OFFICE_OBSERVATION_V1 {spec_sha} {observation.sha256} "
        f"{source.bindings.run_id} {specification['expected_exit']}",
        f"OFFICE_CLOSURE_V1 {closure.sha256}",
    ]
    seals = [
        line
        for line in stdout.splitlines()
        if line.startswith("OFFICE_OBSERVATION_V1 ") or line.startswith("OFFICE_CLOSURE_V1 ")
    ]
    if seals != wanted:
        raise ValueError("Office original observation/Code bytes lack genuine original raw-stdout terminal seals")
    source.verify_correspondence(source.reference, reader.root, reader, deadline)
    complete = time.monotonic()
    remaining(deadline)
    original = NativeOfficeControlOriginal(
        source.bindings.run_id,
        specification["scope"],
        specification["kind"],
        specification["control"],
        specification["expected_exit"],
        deadline,
        complete,
        spec.relative,
        spec.content,
        process.relative,
        process.content,
        (directory / "closure/receipt.json").relative_to(reader.root).as_posix(),
        (directory / "observation.json").relative_to(reader.root).as_posix(),
        command,
        source.reference.commit,
        source.reference.source_identity,
        source.bindings.selected_sdk_package_root,
        MappingProxyType(dict(expected_code)),
        MappingProxyType(hashes),
        _LIVE_ORIGINAL,
    )
    original.closure(reader, deadline=deadline)
    if not reader.unchanged():
        raise ValueError("Office actual original completion custody changed during sealing")
    remaining(deadline)
    return original
