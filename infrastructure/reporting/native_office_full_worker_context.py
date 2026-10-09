"""Explicit Office nominees and genuine original/current worker contexts.

Selection DATA grants no font/shaping, process or native runtime authority.
The callers hold Source, original supervisor and actual live provider scopes.
Every Office artifact in one operation shares the supplied decode budget.
"""

from __future__ import annotations

import hashlib
import json
import re
import stat
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import (
    create_private_native_directory,
)
from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    SourceImageDecodeBudget,
)
from infrastructure.reporting.native_mermaid_runtime_selection import (
    NativeMermaidSelection,
    admit_source_mermaid_selection,
    current_source_mermaid_runtime_admission,
    source_mermaid_runtime_operation,
)
from infrastructure.reporting.native_mermaid_runtime_custody import MAX_FONT_BYTES
from infrastructure.reporting.native_office_mermaid_binding import (
    OfficeMermaidReaderRuntime,
)
from infrastructure.reporting.native_office_pdfium_provider import _file
from infrastructure.reporting.native_tool_producer import (
    current_native_producer_operation,
    native_producer_operation,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

if TYPE_CHECKING:
    from infrastructure.reporting.native_format_joint_source import (
        NativeReaderOperation,
    )
    from infrastructure.reporting.native_office_diagram_runtime import (
        PDFiumRuntimeAdmission,
    )

FONT_SCHEMA = "template-native-office-font-nominations-v1"


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def validate_office_font_nomination_data(value: object) -> None:
    """Validate portable original labels only; never select/read/admit a font."""
    if (
        not isinstance(value, dict)
        or set(value) != {"schema_version", "files", "content_digest"}
        or value["schema_version"] != FONT_SCHEMA
    ):
        raise ValueError("Office original font nomination schema differs")
    rows = value["files"]
    if not isinstance(rows, list) or len(rows) > 4096:
        raise ValueError("Office original font nomination count exceeds finite bounds")
    total = 0
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {
            "path",
            "sha256",
            "bytes",
            "identity",
        }:
            raise ValueError("Office original font nomination row differs")
        path, digest, count, identity = (
            row["path"],
            row["sha256"],
            row["bytes"],
            row["identity"],
        )
        if (
            not isinstance(path, str)
            or not Path(path).is_absolute()
            or ".." in Path(path).parts
            or "\0" in path
            or path in seen
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or type(count) is not int
            or not 0 <= count <= MAX_FONT_BYTES
            or not isinstance(identity, dict)
            or set(identity) != {"device", "inode", "mode", "size", "mtime_ns", "ctime_ns", "links"}
            or any(type(fact) is not int or fact < 0 for fact in identity.values())
            or not stat.S_ISREG(identity["mode"])
            or identity["size"] != count
            or identity["links"] < 1
        ):
            raise ValueError("Office original font body/physical labels are invalid")
        seen.add(path)
        total += count
        if total > MAX_FONT_BYTES:
            raise ValueError("Office original font nomination byte closure exceeds existing128MiB bound")
    if value["content_digest"] != _digest({"schema_version": FONT_SCHEMA, "files": rows}):
        raise ValueError("Office original font nomination digest differs")


def observe_office_font_nominations(font_files: tuple[Path, ...], *, deadline: float) -> dict[str, Any]:
    """Observe explicitly nominated regular bodies before use; no font authority."""
    remaining(deadline)
    if not isinstance(font_files, tuple) or len(font_files) > 4096:
        raise ValueError("Office font nominees must be a finite independently supplied tuple")
    labels: set[str] = set()
    rows: list[dict[str, Any]] = []
    total = 0
    for path in font_files:
        remaining(deadline)
        if not isinstance(path, Path) or not path.is_absolute() or ".." in path.parts or str(path) in labels:
            raise ValueError("Office font nominees require distinct absolute original command paths")
        labels.add(str(path))
        body, identity = _file(path, deadline)
        total += len(body)
        if total > MAX_FONT_BYTES:
            raise ValueError("Office font nomination aggregate exceeds the existing128MiB font bound")
        rows.append(
            {
                "path": str(path),
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
                "identity": identity,
            }
        )
    value = {"schema_version": FONT_SCHEMA, "files": rows}
    remaining(deadline)
    result = {**value, "content_digest": _digest(value)}
    validate_office_font_nomination_data(result)
    return result


def verify_office_font_nominations(
    expected: object,
    font_files: tuple[Path, ...],
    *,
    deadline: float,
    digest: str | None = None,
) -> None:
    """Re-admit actual independently argv-nominated bodies; JSON supplies no paths."""
    validate_office_font_nomination_data(expected)
    current = observe_office_font_nominations(font_files, deadline=deadline)
    if expected != current or (digest is not None and current["content_digest"] != digest):
        raise ValueError("Office font actual nomination/body/physical identity differs from original command pins")
    remaining(deadline)


@dataclass(frozen=True)
class NativeOfficeReaderSelection:
    """Caller-supplied current nominees, separate from transported original DATA."""

    mermaid: NativeMermaidSelection
    font_files: tuple[Path, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.mermaid, NativeMermaidSelection) or not isinstance(self.font_files, tuple):
            raise ValueError("Office current reader requires exact typed independently nominated selections")
        if len(self.font_files) > 4096 or any(
            not isinstance(path, Path) or not path.is_absolute() or ".." in path.parts for path in self.font_files
        ):
            raise ValueError("Office current font nominations are invalid or unbounded")


class _OriginalMermaidProcesses:
    """Verify wrapper DATA through already-held genuine full original custody."""

    def __init__(self, reference: dict[str, Any], reader: SnapshotReader, *, run_id: str) -> None:
        from infrastructure.reporting.native_format_joint_source import (
            require_native_operation,
        )

        self.reader = reader
        self.operation = require_native_operation(reader)
        self.run_id = run_id
        self.bindings: dict[str, dict[str, Any]] = {}
        records: list[tuple[dict[str, Any], dict[str, Any]]] = []
        runtime = reference.get("runtime_process")
        if not isinstance(runtime, dict) or set(runtime) != {"artifact", "process"}:
            raise ValueError("Office Source11 original reference lacks its exact actual Node version binding")
        records.append((runtime["artifact"], runtime["process"]))
        rows = reference.get("occurrences")
        if not isinstance(rows, list) or len(rows) > 100:
            raise ValueError("Office original Mermaid process closure is absent or unbounded")
        for row in rows:
            for kind in ("svg", "png"):
                records.append((row["process_artifacts"][kind], row["processes"][kind]))
        for binding, record in records:
            remaining(self.operation.deadline)
            if not isinstance(binding, dict) or set(binding) != {"path", "sha256"} or not isinstance(record, dict):
                raise ValueError("Office original Mermaid process wrapper binding differs")
            observed = reader.read(binding["path"])
            if observed.sha256 != binding["sha256"] or observed.json_object() != record:
                raise ValueError("Office original Mermaid wrapper bytes differ from their bound process DATA")
            fingerprint = _digest(record)
            if fingerprint in self.bindings and self.bindings[fingerprint] != binding:
                raise ValueError("Office original Mermaid actual process has ambiguous wrapper membership")
            self.bindings[fingerprint] = dict(binding)
        self.operation.verify(reader)

    def admit(self, record: dict[str, Any]) -> None:
        from infrastructure.reporting.native_tool_replay import (
            validate_original_native_tool,
        )

        binding = self.bindings.get(_digest(record))
        if binding is None:
            raise ValueError("Office Mermaid process is absent from this exact original reference")
        # Exact native-execution membership, selected Code, enclosing OS outcome,
        # actual PID and raw stream checks come from the external custodian.
        validate_original_native_tool(binding, record, self.reader, run_id=self.run_id)
        self.operation.verify(self.reader)
        remaining(self.operation.deadline)


@dataclass(frozen=True)
class OfficeCurrentReaderContext:
    """Live current Source/provider scope with one explicitly shared budget."""

    operation: NativeReaderOperation
    selection: NativeOfficeReaderSelection | None
    directory: Path
    decoded_pixel_budget: SourceImageDecodeBudget
    pdfium_runtime: PDFiumRuntimeAdmission

    def runtime_for(
        self,
        observer: dict[str, Any],
        reader: SnapshotReader,
        *,
        ordinal: int,
        run_id: str,
    ) -> OfficeMermaidReaderRuntime | None:
        if "office_complete_source" not in observer:
            return None
        projection = observer["office_complete_source"]["reference"]["source"]["mermaid"]
        if projection is None:
            return None
        if self.selection is None:
            raise ValueError("Office Mermaid current reader requires independent live runtime/font nominees")
        runtime = current_source_mermaid_runtime_admission()
        if (
            runtime is None
            or runtime.source is not self.operation.source
            or runtime.selection != self.selection.mermaid
        ):
            raise ValueError("Office Mermaid reader lost its genuine current Source runtime scope")
        runtime.observe(deadline=self.operation.deadline)
        custodian = _OriginalMermaidProcesses(projection["reference"], reader, run_id=run_id)
        return OfficeMermaidReaderRuntime(
            self.directory / f"office-artifact-{ordinal:04d}",
            self.selection.mermaid.package_root,
            self.selection.mermaid.node_executable,
            self.selection.mermaid.chrome_executable,
            self.selection.font_files,
            custodian.admit,
            self.decoded_pixel_budget,
            self.pdfium_runtime,
            runtime,
        )


@contextmanager
def office_current_reader_context(
    operation: NativeReaderOperation,
    selection: NativeOfficeReaderSelection | None,
    directory: Path,
    *,
    scope: str,
    decoded_pixel_budget: SourceImageDecodeBudget,
    env: dict[str, str],
) -> Iterator[OfficeCurrentReaderContext]:
    """Actual current execution only after fresh preimport bootstrap admission."""
    from infrastructure.reporting.native_format_joint_source import (
        NativeReaderOperation,
    )
    from infrastructure.reporting.native_full_worker_pdfium import (
        admitted_native_reader_pdfium,
        current_full_worker_pdfium_runtime,
    )

    if not isinstance(operation, NativeReaderOperation) or not isinstance(
        decoded_pixel_budget, SourceImageDecodeBudget
    ):
        raise ValueError("Office reader needs the externally held native operation and existing decode budget")
    if selection is not None and not isinstance(selection, NativeOfficeReaderSelection):
        raise ValueError("Office reader nominations must be the exact typed independent caller selection")
    root, deadline = operation.source.bindings.current_root, operation.deadline
    operation.verify(SnapshotReader(root))
    create_private_native_directory(root, directory)
    fonts_before = observe_office_font_nominations(selection.font_files, deadline=deadline) if selection else None
    with ExitStack() as stack:
        owner = current_native_producer_operation()
        if owner is None:
            stack.enter_context(
                native_producer_operation(
                    operation.source,
                    run_id=operation.source.bindings.run_id,
                    deadline=deadline,
                )
            )
        elif owner.source is not operation.source or owner.deadline != deadline:
            raise ValueError("Office current reader belongs to another Source owner or clock")
        pdfium = current_full_worker_pdfium_runtime()
        if pdfium is None:
            pdfium = stack.enter_context(
                admitted_native_reader_pdfium(operation, scope=scope, directory=directory / "pdfium-runtime")
            ).runtime
        if pdfium.source is not operation.source or pdfium.scope != scope or pdfium.deadline != deadline:
            raise ValueError("Office current PDFium scope differs from actual reader Source/scope/clock")
        if selection is not None:
            mermaid = current_source_mermaid_runtime_admission()
            if mermaid is None:
                mermaid = admit_source_mermaid_selection(
                    selection.mermaid,
                    operation.source,
                    deadline=deadline,
                    directory=directory / "mermaid-runtime",
                    env=env,
                )
                stack.enter_context(
                    source_mermaid_runtime_operation(mermaid, source=operation.source, deadline=deadline)
                )
            if mermaid.source is not operation.source or mermaid.selection != selection.mermaid:
                raise ValueError("Office current Mermaid runtime differs from its independent nomination")
            mermaid.observe(deadline=deadline)
        yield OfficeCurrentReaderContext(operation, selection, directory, decoded_pixel_budget, pdfium)
        pdfium.verify()
        if selection is not None:
            verify_office_font_nominations(fonts_before, selection.font_files, deadline=deadline)
            if mermaid is None:
                raise ValueError("Office current Mermaid runtime lost its final genuine Source custody")
            mermaid.observe(deadline=deadline)
        operation.verify(SnapshotReader(root))
        remaining(deadline)
