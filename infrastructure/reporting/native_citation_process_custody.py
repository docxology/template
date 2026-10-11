"""Live original CitationRuntime facts, separate from transported process DATA.

The custodian requires the genuine already-active Source producer. Only direct
tool callbacks register occurrences; a decoded receipt never constructs an owner.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.reporting.native_format_acceptance_contracts import CITATION_TOOL_FIELDS, TOOL_SCHEMA
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_source_external_admission import NativeSourceContext
    from infrastructure.reporting.native_tool_producer import NativeProducerOperation


@dataclass(frozen=True)
class CitationOriginalInvocation:
    """Direct actual ToolAPI event; the live producer supplies its authority."""

    producer: NativeProducerOperation
    root: Path
    artifact_relative: str
    artifact_sha256: str
    original_deadline_monotonic: float
    observed_completion_monotonic: float


class OriginalCitationToolObserver(Protocol):
    """Observe a genuine direct callback without replacing tool execution."""

    def __call__(self, original: CitationOriginalInvocation) -> None: ...


class CitationOriginalProcessCustodian:
    """Authenticate current original Mermaid Node records through their owner."""

    def __init__(self, root: Path, source: NativeSourceContext, *, run_id: str, deadline: float) -> None:
        from infrastructure.reporting.native_source_external_admission import NativeSourceContext
        from infrastructure.reporting.native_tool_producer import current_native_producer_operation

        producer = current_native_producer_operation()
        if (
            not isinstance(source, NativeSourceContext)
            or producer is None
            or producer.source is not source
            or root.absolute() != source.bindings.current_root
            or type(deadline) not in (int, float)
            or not math.isfinite(deadline)
        ):
            raise ValueError("citation custodian requires its genuine active Source producer")
        self.root = root.absolute()
        self.source = source
        self.run_id = run_id
        self.deadline = float(deadline)
        self._producer = producer
        self._originals: dict[str, CitationOriginalInvocation] = {}
        self._verify()

    def _verify(self) -> SnapshotReader:
        reader = SnapshotReader(self.root, native_producer_operation=self._producer)
        self._producer.verify(reader, run_id=self.run_id, deadline=self.deadline)
        if time.monotonic() >= self.deadline:
            raise TimeoutError("citation original custody exhausted its existing operation clock")
        return reader

    def observe_actual_tool(self, original: CitationOriginalInvocation) -> None:
        """Consume only the actual runtime callback and retain exact membership."""
        reader = self._verify()
        if (
            type(original) is not CitationOriginalInvocation
            or original.producer is not self._producer
            or original.root != self.root
            or not original.observed_completion_monotonic < original.original_deadline_monotonic <= self.deadline
        ):
            raise ValueError("citation callback has no actual original Source/process ownership")
        observed = reader.read(original.artifact_relative)
        raw = observed.json_object()
        if observed.sha256 != original.artifact_sha256 or set(raw) != CITATION_TOOL_FIELDS:
            raise ValueError("citation direct original callback retained bytes or fieldset differ")
        binding = {"path": observed.relative, "sha256": observed.sha256}
        self._producer.validate_tool(binding, raw, reader, run_id=self.run_id)
        digest = canonical_digest(raw)
        if digest in self._originals:
            raise ValueError("citation actual original invocation was registered twice")
        self._originals[digest] = original
        if not reader.unchanged():
            raise ValueError("citation original callback source/process artifacts changed")
        self._verify()
        if time.monotonic() >= original.original_deadline_monotonic:
            raise TimeoutError("citation actual callback exceeded the original tool clock")

    def admit_original_process(self, record: dict[str, Any]) -> None:
        """Verify DATA against retained direct facts; never turn DATA into owner."""
        reader = self._verify()
        if (
            not isinstance(record, dict)
            or set(record) != CITATION_TOOL_FIELDS
            or record.get("schema_version") != TOOL_SCHEMA
        ):
            raise ValueError("citation original process requires its exact admitted ToolAPI schema")
        original = self._originals.get(canonical_digest(record))
        if original is None:
            raise ValueError("process is absent from the actual CitationRuntime invocation custodian")
        binding = {"path": original.artifact_relative, "sha256": original.artifact_sha256}
        self._producer.validate_tool(binding, record, reader, run_id=self.run_id)
        if not reader.unchanged():
            raise ValueError("citation original process source/artifact custody changed")
        self._verify()
