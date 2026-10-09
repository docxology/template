"""Genuine complete-Source native diagram positive, before any PDF mutation.

The factory performs source-only package construction, actual native conversion,
Poppler paint and independent PDFium paint on one unchanged caller clock. Its
live result cannot be decoded or asserted from a transported observation.
"""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from infrastructure.project.public_reference_git import remaining
from infrastructure.reporting.native_format_acceptance_contracts import (
    NativeArtifact,
    create_private_native_directory,
)
from infrastructure.reporting.native_office_diagram_binding import (
    admitted_office_diagram_sources,
    diagram_witness_budget,
    diagram_witness_runtime,
)
from infrastructure.reporting.native_format_pdf_source_decode_bounds import (
    SourceImageDecodeBudget,
)
from infrastructure.reporting.native_office_diagram_geometry import DiagramSource
from infrastructure.reporting.native_office_diagram_visibility import (
    observe_office_diagram_visibility,
)
from infrastructure.reporting.native_office_mermaid_binding import (
    OfficeMermaidAdmission,
)
from infrastructure.reporting.native_office_reference import (
    build_office_source_reference,
)
from infrastructure.reporting.native_office_reference_visual import (
    observe_reference_conversion,
)
from infrastructure.reporting.native_source_external_admission import (
    NativeSourceContext,
)
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader

SCHEMA = "template-office-original-source-native-diagram-positive-v1"
_LIVE_POSITIVE = object()


@dataclass(frozen=True)
class OfficeDiagramNativePositive:
    """Actual original in-process positive; only the executing factory owns it."""

    source: NativeSourceContext
    scope: str
    kind: str
    pdf: bytes
    sources: tuple[DiagramSource, ...]
    decoded_pixel_budget: SourceImageDecodeBudget
    record: dict[str, Any]
    reader: SnapshotReader
    owner_pid: int
    deadline: float
    completed_monotonic: float
    live_key: object
    seal: str

    def verify(self, deadline: float) -> None:
        remaining(deadline)
        if (
            self.live_key is not _LIVE_POSITIVE
            or self.owner_pid != os.getpid()
            or deadline != self.deadline
            or self.completed_monotonic >= deadline
        ):
            raise ValueError("Office positive is not the genuine caller's original live native positive")
        if (
            hashlib.sha256(repr(self.record).encode()).hexdigest() != self.seal
            or hashlib.sha256(self.pdf).hexdigest() != self.record["pdf"]["sha256"]
        ):
            raise ValueError("Office actual original positive bytes/observations changed")
        self.source.verify_correspondence(
            self.source.reference,
            self.source.bindings.current_root,
            self.reader,
            deadline,
        )
        if not self.reader.unchanged():
            raise ValueError("Office original Source/PDF/raster positive custody changed")
        remaining(deadline)


def build_office_diagram_native_positive(
    root: Path,
    directory: Path,
    scope: str,
    artifact: NativeArtifact,
    source: NativeSourceContext,
    mermaid_admission: OfficeMermaidAdmission,
    *,
    env: dict[str, str],
    deadline: float,
    run_id: str,
    epubcheck_jar: Path | None = None,
    java_executable: Path | None = None,
    frozen_epub_engine: Path | None = None,
) -> OfficeDiagramNativePositive:
    """Perform an actual Source-only native positive under the original clock."""
    remaining(deadline)
    if (
        source.bindings.current_root != root
        or source.bindings.run_id != run_id
        or artifact.format not in {"docx", "epub"}
    ):
        raise ValueError("Office original native positive requires genuine exact Source/scope/run")
    runtime = diagram_witness_runtime(mermaid_admission, deadline)
    if runtime.source is not source or runtime.scope != scope:
        raise ValueError("Office original native positive selected another Source/provider admission")
    create_private_native_directory(root, directory)
    for leaf in ("source-reference", "native-conversion"):
        create_private_native_directory(root, directory / leaf)
    reader = SnapshotReader(root)
    source.verify_correspondence(source.reference, root, reader, deadline)
    reference = build_office_source_reference(
        root,
        directory / "source-reference",
        scope,
        artifact,
        reader,
        env=env,
        deadline=deadline,
        run_id=run_id,
        mermaid_admission=mermaid_admission,
    )
    native = observe_reference_conversion(
        root,
        directory / "native-conversion",
        reference["package"],
        artifact.format,
        env=env,
        deadline=deadline,
        run_id=run_id,
        epubcheck_jar=epubcheck_jar,
        java_executable=java_executable,
        frozen_engine=frozen_epub_engine,
    )
    pdf = reader.read(native["conversion"]["pdf"]["path"])
    if pdf.sha256 != native["conversion"]["pdf"]["sha256"]:
        raise ValueError("Office actual Source-only native positive PDF changed")
    sources = admitted_office_diagram_sources(reference["source"], scope, reader, mermaid_admission)
    if not sources:
        raise ValueError("Office diagram mutation requires actual configured original diagrams")
    pages = tuple(reader.read(row["path"]).content for row in native["raster"]["rasters"])
    visibility = observe_office_diagram_visibility(
        root,
        directory / "source-stencils",
        pdf.content,
        pages,
        sources,
        budget=diagram_witness_budget(mermaid_admission),
        pdfium_runtime=runtime,
        env=env,
        deadline=deadline,
        run_id=run_id,
    )
    if (
        visibility["status"] != "pass"
        or visibility["findings"]
        or visibility["blockers"]
        or not visibility["geometry"]["placements"]
    ):
        raise ValueError("Office original Source-only Poppler/PDFium native positive failed before mutation")
    runtime.verify()
    source.verify_correspondence(source.reference, root, reader, deadline)
    if not reader.unchanged():
        raise ValueError("Office actual Source/native positive custody changed before mutation")
    completed = time.monotonic()
    remaining(deadline)
    record = {
        "schema_version": SCHEMA,
        "run_id": run_id,
        "scope": scope,
        "kind": artifact.format,
        "source": {
            "commit": source.reference.commit,
            "source_identity": source.reference.source_identity,
        },
        "original_deadline_monotonic": deadline,
        "owner_pid": os.getpid(),
        "completed_monotonic": completed,
        "reference": reference,
        "native": native,
        "pdf": {"path": pdf.relative, "sha256": pdf.sha256},
        "visibility": visibility,
        "occurrences": [value.identity for value in sources],
    }
    result = OfficeDiagramNativePositive(
        source,
        scope,
        artifact.format,
        pdf.content,
        sources,
        diagram_witness_budget(mermaid_admission),
        record,
        reader,
        os.getpid(),
        deadline,
        completed,
        _LIVE_POSITIVE,
        hashlib.sha256(repr(record).encode()).hexdigest(),
    )
    result.verify(deadline)
    return result
