"""Fresh Source-owned Pandoc reader scope; transported receipts select no tools.

This is a scoped parser invocation, not loaded native-library/crossref admission.
Original parser membership is authenticated separately with its original nonce.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_joint_source import require_native_operation
from infrastructure.reporting.native_pdf_citation_runtime import CitationRuntime, file_observation
from infrastructure.reporting.native_tool_producer import current_native_producer_operation
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

CROSSREF_CUSTODY_BLOCKER = (
    "HTML crossref loaded nested executable/library custody requires i"
    "ndependently admitted actual parser child execution"
)


class CurrentPandocReader:
    """Invocation helper held only inside a verified live current Source scope."""

    def __init__(self, runtime: CitationRuntime, reader: SnapshotReader, bodies: dict[str, dict[str, Any]]) -> None:
        self.runtime, self.reader, self.bodies = runtime, reader, bodies

    def verify(self) -> None:
        remaining(self.runtime.deadline)
        operation = require_native_operation(self.reader)
        producer = current_native_producer_operation()
        if (
            producer is None
            or self.reader.native_producer_operation is not producer
            or producer.source is not operation.source
            or producer.owner_pid != os.getpid()
            or producer.run_id != operation.source.bindings.run_id
            or producer.run_id != self.runtime.run_id
            or producer.deadline != operation.deadline
            or producer.deadline != self.runtime.deadline
        ):
            raise ValueError("current Pandoc requires exact live Source/SDK owner/run/original clock")
        producer.verify(self.reader, run_id=producer.run_id, deadline=self.runtime.deadline)
        self.runtime.unchanged()
        for body in self.bodies.values():
            remaining(self.runtime.deadline)
            if file_observation(Path(body["path"])) != body:
                raise ValueError("current Pandoc independently nominated tool/filter body changed")
        if not self.reader.unchanged():
            raise ValueError("current Pandoc input/native retained evidence changed")

    def tool(self, name: str, arguments: list[str], purpose: str) -> dict[str, Any]:
        """Validate the actual fresh ToolAPI registration while its owner lives."""
        from infrastructure.reporting.native_format_acceptance_validation import _tool

        self.verify()
        if name not in self.bodies:
            raise ValueError("current Pandoc tool was not independently nominated before invocation")
        before = self.bodies[name]
        observed = self.runtime.tool(name, arguments, purpose, input_paths=tuple(self.runtime.inputs))
        binding = self.runtime.tools[-1]
        admitted = _tool(binding, self.reader, self.runtime.run_id, name, purpose, arguments)
        if (
            admitted != observed
            or admitted["executable"] != before["path"]
            or admitted["executable_sha256"] != before["sha256"]
        ):
            raise ValueError("current Pandoc native original outcome/body/registration differs")
        self.verify()
        return admitted

    @property
    def crossref(self) -> str | None:
        path = self.bodies.get("pandoc-crossref", {}).get("path")
        return path if isinstance(path, str) else None

    def source_crossref_tool(
        self, arguments: list[str], purpose: str, *, scope: str, output_format: str
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """Run the actual selected Source filter child; retain its own graph."""
        from infrastructure.reporting.native_crossref_pandoc import source_crossref_pandoc

        self.verify()
        if self.crossref is None:
            raise ValueError("current parser did not independently nominate crossref before invocation")
        observed, child = source_crossref_pandoc(self.runtime, scope, arguments, purpose, output_format=output_format)
        from infrastructure.reporting.native_crossref_pair import parent_observation

        graph = parent_observation(child, self.reader)
        specification = self.reader.read(graph["specification"]["path"]).json_object()
        if specification["crossref"] != self.bodies["pandoc-crossref"]:
            raise ValueError("current parser nested crossref differs from its independent prelaunch body nomination")
        if observed["executable"] != self.bodies["pandoc"]["path"] or (
            observed["executable_sha256"] != self.bodies["pandoc"]["sha256"]
        ):
            raise ValueError("current parser actual Pandoc changed during Source-owned filter execution")
        self.verify()
        return observed, child


@contextmanager
def current_pandoc_reader(
    root: Path,
    reader: SnapshotReader,
    *,
    env: dict[str, str],
    deadline: float,
    purpose: str,
    crossref: bool = False,
) -> Iterator[CurrentPandocReader]:
    """Admit exact current inputs/processes with the fresh genuine reader nonce.

    The original native run may be different. Only the actual current Source
    capability supplies this invocation's run identity, Source and clock.
    """
    remaining(deadline)
    operation = require_native_operation(reader)
    producer = current_native_producer_operation()
    if (
        reader.root != root.resolve()
        or producer is None
        or producer.source is not operation.source
        or producer.owner_pid != os.getpid()
        or producer.run_id != operation.source.bindings.run_id
        or producer.deadline != deadline
        or operation.deadline != deadline
    ):
        raise ValueError("current Pandoc reader lacks its actual independently admitted Source owner/clock")
    producer.verify(reader, run_id=producer.run_id, deadline=deadline)
    if not purpose or not purpose.isascii() or not all(char.isalnum() or char == "-" for char in purpose):
        raise ValueError("current Pandoc reader purpose must be a Source-owned canonical label")
    bodies = {}
    for name in ("pandoc", *(("pandoc-crossref",) if crossref else ())):
        selected = shutil.which(name, path=env.get("PATH"))
        if selected is None:
            raise ValueError("current Pandoc reader lacks its independently selected " + name)
        bodies[name] = file_observation(Path(selected).resolve(strict=True))
    leaf = root / "output/readiness/current-native-readers" / producer.run_id / f"{purpose}-{uuid4().hex}"
    runtime = CitationRuntime(root, leaf, env=env, deadline=deadline, run_id=producer.run_id)
    live_reader = SnapshotReader(root, native_operation=operation, native_producer_operation=producer)
    current = CurrentPandocReader(runtime, live_reader, bodies)
    current.verify()
    if crossref:
        current.tool("pandoc-crossref", ["--version"], "current-crossref-version")
    yield current
    current.verify()
    if not reader.unchanged():
        raise ValueError("current Pandoc original input/evidence changed during fresh parser replay")
    producer.verify(reader, run_id=producer.run_id, deadline=deadline)
    operation.verify(reader)
    remaining(deadline)
