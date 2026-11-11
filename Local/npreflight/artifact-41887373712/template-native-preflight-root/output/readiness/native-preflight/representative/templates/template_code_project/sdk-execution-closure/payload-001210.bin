"""Exact current manuscript Mermaid fences, source positions and document order.

Discovery obeys the existing render source/hydration policy. SourceJSON never
selects manuscript inputs, and repeated fence bytes retain distinct occurrences.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from infrastructure.core.pipeline.fingerprints import canonical_digest
from infrastructure.project.public_reference_git import remaining
from infrastructure.project.public_scope import PUBLIC_PROJECT_NAMES
from infrastructure.rendering._combined_exports import combined_source_files
from infrastructure.rendering._pdf_mermaid import _MERMAID_BLOCK_RE
from infrastructure.rendering.manuscript_discovery import discover_manuscript_files
from infrastructure.reporting.native_source_external_admission import NativeSourceContext
from infrastructure.reporting.release_readiness_snapshot import SnapshotReader
from infrastructure.validation.output.render_formats import render_config_manuscript_dir
from infrastructure.validation.publication.rendered_provenance import validate_current_rendered_provenance

SCHEMA = "template-native-current-source-mermaid-fence-census-v1"
MAX_MANUSCRIPT_BYTES = 64 * 1024 * 1024
MAX_SOURCE_FENCES = 100


@dataclass(frozen=True)
class SourceMermaidFence:
    """One exact lexical position in one genuine current document source."""

    scope: str
    source_path: str
    source_file_sha256: str
    document_input_ordinal: int
    source_file_fence_ordinal: int
    document_fence_ordinal: int
    opening_line: int
    raw_start_byte: int
    raw_end_byte: int
    raw_source: bytes
    source_prefix_sha256: str
    source_suffix_sha256: str

    @property
    def identity(self) -> str:
        # The occurrence is a source location; raw-equivalent fences are never
        # rebased onto one another or given one shared occurrence identity.
        return f"{self.source_path}:{self.opening_line}"

    def data(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "scope": self.scope,
            "source_path": self.source_path,
            "source_file_sha256": self.source_file_sha256,
            "document_input_ordinal": self.document_input_ordinal,
            "source_file_fence_ordinal": self.source_file_fence_ordinal,
            "document_fence_ordinal": self.document_fence_ordinal,
            "opening_line": self.opening_line,
            "raw_start_byte": self.raw_start_byte,
            "raw_end_byte": self.raw_end_byte,
            "raw_source_sha256": hashlib.sha256(self.raw_source).hexdigest(),
            "raw_source_bytes": len(self.raw_source),
            "source_prefix_sha256": self.source_prefix_sha256,
            "source_suffix_sha256": self.source_suffix_sha256,
        }


@dataclass(frozen=True)
class SourceMermaidCensus:
    """Held original raw bytes and independently rebuilt complete source order."""

    source: NativeSourceContext
    occurrences: tuple[SourceMermaidFence, ...]
    document_inputs: tuple[tuple[str, tuple[tuple[str, str], ...]], ...]

    def sources(self) -> tuple[tuple[str, bytes], ...]:
        return tuple((row.identity, row.raw_source) for row in self.occurrences)

    def data(self) -> dict[str, Any]:
        body = {
            "schema_version": SCHEMA,
            "source_commit": self.source.reference.commit,
            "source_identity": self.source.reference.source_identity,
            "document_inputs": [
                {"scope": scope, "ordered_inputs": [{"path": path, "sha256": digest} for path, digest in items]}
                for scope, items in self.document_inputs
            ],
            "occurrences": [row.data() for row in self.occurrences],
        }
        return {**body, "content_digest": canonical_digest(body)}


def collect_current_source_mermaid_fences(source: NativeSourceContext, *, deadline: float) -> SourceMermaidCensus:
    """Read genuine selected inputs and retain every byte-position occurrence."""
    if not isinstance(source, NativeSourceContext):
        raise ValueError("Mermaid fence census needs genuine independently admitted Source")
    remaining(deadline)
    root = source.bindings.current_root
    reader = SnapshotReader(root)
    source.verify_correspondence(source.reference, root, reader, deadline)
    occurrences = []
    documents = []
    for scope in sorted(PUBLIC_PROJECT_NAMES):
        remaining(deadline)
        if not validate_current_rendered_provenance(root, scope).valid:
            raise ValueError("Mermaid source census requires current consumed hydration provenance: " + scope)
        project = root / "projects" / scope
        # Actual source guards surround the existing discovery functions; they
        # are code from the selected SDK and never imported from SourceDATA.
        manuscript = render_config_manuscript_dir(project)
        paths = combined_source_files(discover_manuscript_files(manuscript))
        if not paths:
            raise ValueError("Mermaid document source ordering is empty: " + scope)
        inputs = []
        document_ordinal = 0
        for input_ordinal, path in enumerate(paths):
            remaining(deadline)
            relative = path.relative_to(root).as_posix()
            original = source.reference.read(relative)
            snapshot = reader.read(relative)
            if snapshot.content != original or len(original) > MAX_MANUSCRIPT_BYTES:
                raise ValueError("Mermaid selected manuscript differs from its actual original Source bytes")
            inputs.append((relative, snapshot.sha256))
            content = original.decode("utf-8")
            for file_ordinal, match in enumerate(_MERMAID_BLOCK_RE.finditer(content)):
                remaining(deadline)
                start = len(content[: match.start("source")].encode("utf-8"))
                end = len(content[: match.end("source")].encode("utf-8"))
                raw = match.group("source").encode("utf-8")
                if original[start:end] != raw or not raw or len(raw) > 1024 * 1024:
                    raise ValueError("Mermaid exact lexical fence body differs/empty/unbounded")
                opening_line = content[: match.start()].count("\n") + 1
                occurrences.append(
                    SourceMermaidFence(
                        scope,
                        relative,
                        snapshot.sha256,
                        input_ordinal,
                        file_ordinal,
                        document_ordinal,
                        opening_line,
                        start,
                        end,
                        raw,
                        hashlib.sha256(original[:start]).hexdigest(),
                        hashlib.sha256(original[end:]).hexdigest(),
                    )
                )
                document_ordinal += 1
                if len(occurrences) > MAX_SOURCE_FENCES:
                    raise ValueError("complete Mermaid Source fence census exceeds existing observer bound")
        documents.append((scope, tuple(inputs)))
    if not occurrences or len({row.identity for row in occurrences}) != len(occurrences) or not reader.unchanged():
        raise ValueError("Mermaid original Source census is absent/duplicate/changed")
    source.verify_correspondence(source.reference, root, reader, deadline)
    return SourceMermaidCensus(source, tuple(occurrences), tuple(documents))
