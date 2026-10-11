"""Actual Source-owned original native worker supervision and terminal custody.

The owner is prepared before its real Popen. Its direct result, source input and
terminal artifact snapshots remain held objects; no decoded JSON factory can
construct a completed original. Remote transport separately authenticates the
exact Source producer and its artifact membership before admitting an original.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import PROCESS_SCHEMA
from infrastructure.reporting.native_format_joint_source import (
    NativeOriginalLaunch,
    NativeReaderOperation,
    source_environment,
    validate_original_joint_launch,
    validate_retained_sdk_closure,
)
from infrastructure.reporting.native_format_process_custody import native_host_observation
from infrastructure.reporting.native_source_external_admission import NativeSourceContext, _anchored_directory_identity
from infrastructure.reporting.native_tool_process import run_native_tool_process
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import ArtifactSnapshot, SnapshotReader


from infrastructure.reporting.native_full_worker_pdfium import NativePDFiumProvider


class NativeOriginalSupervisor:
    """One genuinely live Source owner, one original invocation and one deadline."""

    def __init__(
        self,
        source: NativeSourceContext,
        specification: ArtifactSnapshot,
        descriptor: ArtifactSnapshot,
        implementation: ArtifactSnapshot,
        command: tuple[str, ...],
        closure_directory: Path,
        closure_identity: tuple[int, int],
        *,
        deadline: float,
        pdfium_provider: NativePDFiumProvider,
    ) -> None:
        if not isinstance(source, NativeSourceContext):
            raise ValueError("native original supervisor requires actual independently admitted Source")
        remaining(deadline)
        self.source = source
        self.root = source.bindings.current_root
        self.specification = specification
        self.descriptor = descriptor
        self.implementation = implementation
        self.command = command
        self.closure_directory = closure_directory
        self.closure_identity = closure_identity
        self.deadline = deadline
        if not isinstance(pdfium_provider, NativePDFiumProvider) or pdfium_provider.source is not source:
            raise ValueError("native original needs genuine prelaunch Source-owned PDFium admission")
        self.pdfium_provider = pdfium_provider
        self.owner_pid = os.getpid()
        self.producer = current_native_producer_operation()
        self._result: dict[str, Any] | None = None
        self._process: ArtifactSnapshot | None = None
        self._completion: float | None = None
        self._finished = False
        if self.producer is None or self.producer.source is not source or not command:
            raise ValueError("native original supervisor requires its genuine current Source producer")
        spec = specification.json_object()
        if (
            spec["deadline_monotonic"] != deadline
            or spec["run_id"] != source.bindings.run_id
            or spec["source_inputs"]["descriptor"] != {"path": descriptor.relative, "sha256": descriptor.sha256}
            or spec["source_inputs"]["implementation"]
            != {"path": implementation.relative, "sha256": implementation.sha256}
        ):
            raise ValueError("native original prelaunch Source/spec pins differ")
        if self.pdfium_provider.held_inputs() != spec["source_inputs"]["pdfium"]:
            raise ValueError("native original prelaunch PDFium input differs from actual held provider")
        self._verify()

    def _verify(self) -> None:
        remaining(self.deadline)
        if self.owner_pid != os.getpid() or self.producer is None:
            raise ValueError("native original supervisor is not held by its actual original process")
        self.pdfium_provider.verify_current(deadline=self.deadline)
        reader = SnapshotReader(self.root)
        self.producer.verify(reader, run_id=self.source.bindings.run_id, deadline=self.deadline)
        for item in (self.specification, self.descriptor, self.implementation):
            current = reader.read(item.relative)
            if current.sha256 != item.sha256 or current.identity != item.identity:
                raise ValueError("native original prelaunch Source/spec input changed")
        if _anchored_directory_identity(self.closure_directory, self.deadline) != self.closure_identity:
            raise ValueError("native original held execution-closure directory was replaced")

    def launch(self, directory: Path, environment: dict[str, str]) -> dict[str, Any]:
        """Execute exactly once; retain true signed OS result and full raw streams."""
        if self._result is not None or self._finished:
            raise ValueError("native original supervisor cannot launch twice")
        self._verify()
        before = native_host_observation()
        result = run_native_tool_process(
            directory,
            self.command[0],
            list(self.command[1:]),
            cwd=self.root,
            env=environment,
            deadline=self.deadline,
            purpose="original-native-worker",
            preserve_nominated_launcher=True,
        )
        self._result = result
        reader = SnapshotReader(self.root)
        raw_process = reader.read(
            (directory / "original-native-worker.native-process.json").relative_to(self.root).as_posix()
        )
        if raw_process.json_object() != result or tuple(result["command"] or ()) != self.command:
            raise ValueError("native original direct result differs from its retained actual process")
        original = result["original_exit_code"]
        accepted = result["accepted"]
        code = 124 if result["timed_out"] else 75 if not accepted and original in (None, 0, 75) else original
        streams: dict[str, Any] = {}
        for channel in ("stdout", "stderr"):
            binding = result.get("raw_" + channel)
            if isinstance(binding, dict):
                snapshot = reader.read(Path(binding["path"]).relative_to(self.root).as_posix())
                if snapshot.sha256 != binding["sha256"] or len(snapshot.content) != binding["bytes"]:
                    raise ValueError("native original full binary stream changed before terminal retention")
                streams["raw_" + channel] = {
                    "path": snapshot.relative,
                    "sha256": snapshot.sha256,
                    "bytes": len(snapshot.content),
                }
        self._completion = time.monotonic()
        observation = {
            "schema_version": PROCESS_SCHEMA,
            "run_id": self.source.bindings.run_id,
            "command": list(self.command),
            "selected_interpreter": self.command[0],
            "source_environment": source_environment(self.source),
            "sdk_closure_artifact": None,
            "completed_monotonic": self._completion,
            "original_deadline_monotonic": self.deadline,
            "caller_deadline_monotonic": self.deadline,
            "native_process_artifact": {"path": raw_process.relative, "sha256": raw_process.sha256},
            "exit_code": code,
            "original_exit_code": original,
            "pid": result["pid"],
            "owner_pid": result["owner_pid"],
            "host_before": before,
            "host_after": native_host_observation(),
            "timed_out": result["timed_out"],
            "custody_refused": not accepted,
            "diagnostic": "; ".join(result["diagnostics"]),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "executable": result["nomination"]["resolved_path"] if result["nomination"] else None,
            "executable_sha256": (result.get("executable_observation_before") or {}).get("sha256"),
            "executable_observation_before": result.get("executable_observation_before"),
            "executable_observation_after": result.get("executable_observation_after"),
            "executable_identity_before": result.get("executable_identity_before"),
            "executable_identity_after": result.get("executable_identity_after"),
            **streams,
        }
        if not reader.unchanged():
            raise ValueError("native original actual process/raw bytes changed during retention")
        return observation

    def finish(
        self, process: ArtifactSnapshot, closure: ArtifactSnapshot, native_execution: ArtifactSnapshot
    ) -> NativeOriginalLaunch:
        """Close direct OS/Source/Code/member facts before exporting held authority."""
        if self._finished or self._result is None or self._completion is None:
            raise ValueError("native original requires one actual completed supervisor invocation")
        self._finished = True
        self._verify()
        direct = self._result
        observed = process.json_object()
        if (
            not direct["accepted"]
            or direct["original_exit_code"] not in {0, 75}
            or observed.get("original_exit_code") != direct["original_exit_code"]
            or observed.get("exit_code") != direct["original_exit_code"]
            or observed.get("pid") != direct["pid"]
            or observed.get("owner_pid") != self.owner_pid
            or observed.get("command") != list(self.command)
            or observed.get("completed_monotonic") != self._completion
            or self._completion >= self.deadline
            or native_execution.json_object().get("execution_exit_code") != direct["original_exit_code"]
        ):
            raise ValueError("native original terminal data differs from actual supervised original OS custody")
        reference = self.source.reference
        spec = self.specification.json_object()
        original = NativeOriginalLaunch(
            scope=spec["scope"],
            run_id=spec["run_id"],
            specification_sha256=self.specification.sha256,
            specification_relative=self.specification.relative,
            process_relative=process.relative,
            closure_relative=closure.relative,
            native_execution_relative=native_execution.relative,
            descriptor_sha256=self.descriptor.sha256,
            implementation_sha256=self.implementation.sha256,
            process_sha256=process.sha256,
            closure_sha256=closure.sha256,
            command=self.command,
            source_binding=(str(reference.root), reference.commit, reference.source_identity),
            native_execution_sha256=native_execution.sha256,
            original_deadline=self.deadline,
            observed_completion=self._completion,
            pdfium_provider=self.pdfium_provider,
        )
        operation = NativeReaderOperation(
            self.source, self.deadline, {original.scope: original}, {original.scope: self.pdfium_provider}
        )
        reader = SnapshotReader(self.root, native_operation=operation)
        _, source = validate_original_joint_launch(spec, self.specification, process, closure, reader, operation)
        validate_retained_sdk_closure(closure, spec, source, reader, operation)
        validate_original_native_process(observed, reader, original=original)
        if not reader.unchanged():
            raise ValueError("native original closing artifact membership changed")
        self._process = process
        self._verify()
        return original


def validate_original_native_process(
    raw: dict[str, Any], reader: SnapshotReader, *, original: NativeOriginalLaunch
) -> None:
    """DATA predicate under independently held original process/hash/clock facts."""
    from infrastructure.reporting.native_tool_replay import validate_native_tool_data

    if reader.read(original.process_relative).sha256 != original.process_sha256:
        raise ValueError("native original process differs from external original custody")
    validate_native_tool_data(
        raw, reader, original_deadline=original.original_deadline, original_completion=original.observed_completion
    )
